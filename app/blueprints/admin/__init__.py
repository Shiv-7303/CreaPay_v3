from flask import Blueprint, jsonify, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, login_user, current_user
from app.utils.decorators import admin_required
from app.models.user import User
from app.models.deal import Deal
from app.models.activity_log import ActivityLog
from app import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', methods=['GET'])
@login_required
@admin_required
def index():
    return redirect(url_for('admin.analytics'))

@admin_bp.route('/analytics', methods=['GET'])
@login_required
@admin_required
def analytics():
    return render_template('admin/analytics.html')

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def users():
    plan_filter = request.args.get('plan', 'all').lower()

    query = User.query
    if plan_filter == 'free':
        query = query.filter_by(plan='free')
    elif plan_filter == 'pro':
        query = query.filter_by(plan='pro')
    elif plan_filter == 'suspended':
        query = query.filter_by(is_active=False)

    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, current_filter=plan_filter)

@admin_bp.route('/users/<id>/set-plan', methods=['POST'])
@login_required
@admin_required
def set_user_plan(id):
    from app.models.subscription import Subscription
    from datetime import datetime, timedelta, timezone

    user = User.query.get_or_404(id)
    new_plan = request.form.get('plan')

    if new_plan in ['free', 'pro'] and new_plan != user.plan:
        old_plan = user.plan
        user.plan = new_plan

        now = datetime.now(timezone.utc)

        if new_plan == 'pro':
            # Create a manual subscription record
            user.plan_expires_at = now + timedelta(days=30)
            sub = Subscription(
                user_id=user.id,
                razorpay_payment_id='manual_admin_upgrade',
                plan='pro',
                amount_paid=0.0,
                starts_at=now,
                expires_at=user.plan_expires_at,
                status='active'
            )
            db.session.add(sub)
        else:
            # Downgrading to free
            user.plan_expires_at = None
            # Cancel active subscriptions
            active_subs = Subscription.query.filter_by(user_id=user.id, status='active').all()
            for sub in active_subs:
                sub.status = 'cancelled'

        log = ActivityLog(user_id=current_user.id, action=f"Changed plan for {user.email} from {old_plan} to {new_plan}")
        db.session.add(log)
        db.session.commit()
        flash(f"Updated plan for {user.email} to {new_plan}", "success")

    return redirect(url_for('admin.users', plan=request.args.get('plan', 'all')))

@admin_bp.route('/users/<id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend_user(id):
    user = User.query.get_or_404(id)
    user.is_active = False
    log = ActivityLog(user_id=current_user.id, action=f"Suspended user {user.email}")
    db.session.add(log)
    db.session.commit()
    flash(f"Suspended {user.email}", "success")
    return redirect(url_for('admin.users', plan=request.args.get('plan', 'all')))

@admin_bp.route('/users/<id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(id):
    user = User.query.get_or_404(id)
    user.is_active = True
    log = ActivityLog(user_id=current_user.id, action=f"Activated user {user.email}")
    db.session.add(log)
    db.session.commit()
    flash(f"Activated {user.email}", "success")
    return redirect(url_for('admin.users', plan=request.args.get('plan', 'all')))

@admin_bp.route('/users/<id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    email = user.email

    # Hard delete: Manually delete related records to avoid foreign key constraints
    from app.models.deal import Deal
    from app.models.brand import Brand
    from app.models.invoice import Invoice
    from app.models.subscription import Subscription
    from app.models.activity_log import ActivityLog

    # 1. Delete Invoices (linked to deals)
    deals = Deal.query.filter_by(user_id=user.id).all()
    for deal in deals:
        Invoice.query.filter_by(deal_id=deal.id).delete()

    # 2. Delete Deals
    Deal.query.filter_by(user_id=user.id).delete()

    # 3. Delete Brands
    Brand.query.filter_by(user_id=user.id).delete()

    # 4. Delete Subscriptions
    Subscription.query.filter_by(user_id=user.id).delete()

    # 5. Delete Activity Logs
    ActivityLog.query.filter_by(user_id=user.id).delete()

    # Finally, delete user
    db.session.delete(user)

    # Log this action using the current admin user
    log = ActivityLog(user_id=current_user.id, action=f"Hard deleted user {email} and all their data")
    db.session.add(log)

    db.session.commit()
    flash(f"Completely deleted {email} and all associated data.", "success")
    return redirect(url_for('admin.users', plan=request.args.get('plan', 'all')))

@admin_bp.route('/deals', methods=['GET'])
@login_required
@admin_required
def deals():
    creator_filter = request.args.get('creator', '')
    status_filter = request.args.get('status', 'all').lower()

    query = Deal.query

    if status_filter == 'deleted':
        query = query.filter(Deal.deleted_at.isnot(None))
    else:
        query = query.filter(Deal.deleted_at.is_(None))
        if status_filter != 'all':
            query = query.filter(Deal.status == status_filter)

    if creator_filter:
        query = query.join(User).filter(User.email.ilike(f'%{creator_filter}%'))

    deals = query.order_by(Deal.created_at.desc()).all()
    return render_template('admin/deals.html', deals=deals, current_status=status_filter, current_creator=creator_filter)

@admin_bp.route('/deals/<id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_deal(id):
    deal = Deal.query.get_or_404(id)
    new_amount = request.form.get('amount')
    new_status = request.form.get('status')

    updates = []
    if new_amount and float(new_amount) != float(deal.amount):
        updates.append(f"amount from {deal.amount} to {new_amount}")
        deal.amount = new_amount

    if new_status and new_status != deal.status:
        updates.append(f"status from {deal.status} to {new_status}")
        deal.status = new_status

    if updates:
        log = ActivityLog(user_id=current_user.id, action=f"Edited deal {id}: {', '.join(updates)}")
        db.session.add(log)
        db.session.commit()
        flash(f"Deal updated successfully.", "success")

    return redirect(url_for('admin.deals'))

@admin_bp.route('/deals/<id>/mark-paid', methods=['POST'])
@login_required
@admin_required
def mark_deal_paid(id):
    from datetime import datetime, timezone
    deal = Deal.query.get_or_404(id)
    deal.status = 'paid'
    deal.paid_at = datetime.now(timezone.utc)
    log = ActivityLog(user_id=current_user.id, action=f"Marked deal {id} as paid")
    db.session.add(log)
    db.session.commit()
    flash("Deal marked as paid.", "success")
    return redirect(url_for('admin.deals'))

@admin_bp.route('/deals/<id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_deal(id):
    from datetime import datetime, timezone
    deal = Deal.query.get_or_404(id)
    deal.deleted_at = datetime.now(timezone.utc)
    log = ActivityLog(user_id=current_user.id, action=f"Soft deleted deal {id}")
    db.session.add(log)
    db.session.commit()
    flash("Deal deleted.", "success")
    return redirect(url_for('admin.deals'))

@admin_bp.route('/deals/<id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_deal(id):
    deal = Deal.query.get_or_404(id)
    deal.deleted_at = None
    log = ActivityLog(user_id=current_user.id, action=f"Restored deal {id}")
    db.session.add(log)
    db.session.commit()
    flash("Deal restored.", "success")
    return redirect(url_for('admin.deals'))

@admin_bp.route('/impersonate/<id>', methods=['POST'])
@login_required
@admin_required
def impersonate(id):
    target_user = User.query.get_or_404(id)

    # Store admin's ID
    session['impersonator_id'] = current_user.id

    # Log activity
    log = ActivityLog(user_id=current_user.id, action=f"Started impersonating user {target_user.email}")
    db.session.add(log)
    db.session.commit()

    # Log in as target
    login_user(target_user)
    flash(f"You are now impersonating {target_user.email}", "info")
    return redirect(url_for('dashboard.index'))

@admin_bp.route('/stop-impersonation', methods=['POST'])
@login_required
def stop_impersonation():
    impersonator_id = session.pop('impersonator_id', None)
    if not impersonator_id:
        flash("You were not impersonating anyone.", "error")
        return redirect(url_for('dashboard.index'))

    admin_user = User.query.get(impersonator_id)
    if not admin_user or not admin_user.is_admin:
        flash("Invalid impersonation state.", "error")
        return redirect(url_for('auth.logout'))

    # Log activity before switching back
    log = ActivityLog(user_id=admin_user.id, action=f"Stopped impersonating user {current_user.email}")
    db.session.add(log)
    db.session.commit()

    login_user(admin_user)
    flash("Stopped impersonation. Welcome back.", "success")
    return redirect(url_for('admin.analytics'))

@admin_bp.route('/api/users', methods=['GET'])
@login_required
@admin_required
def api_users():
    plan_filter = request.args.get('plan', 'all').lower()
    limit = request.args.get('limit', type=int)

    query = User.query
    if plan_filter in ['free', 'pro']:
        query = query.filter_by(plan=plan_filter)

    query = query.order_by(User.created_at.desc())

    if limit:
        users = query.limit(limit).all()
    else:
        users = query.all()

    return jsonify([{
        'id': u.id,
        'email': u.email,
        'full_name': u.full_name,
        'plan': u.plan,
        'deals_count': len(u.deals),
        'joined_date': u.created_at.isoformat()
    } for u in users])

@admin_bp.route('/api/stats', methods=['GET'])
@login_required
@admin_required
def api_stats():
    total_users = User.query.count()
    pro_users = User.query.filter_by(plan='pro').count()
    mrr = pro_users * 299
    
    total_deals = Deal.query.count()
    active_deals = Deal.query.filter(Deal.status != 'paid').count()
    
    return jsonify({
        'total_signups': total_users,
        'total_pro_users': pro_users,
        'mrr': mrr,
        'total_deals_created': total_deals,
        'active_deals': active_deals
    })

@admin_bp.route('/api/deals', methods=['GET'])
@login_required
@admin_required
def api_deals():
    deals = Deal.query.order_by(Deal.created_at.desc()).all()
    # Simple grouping just to satisfy the payload requirements
    return jsonify([{
        'id': d.id,
        'user': d.user.email,
        'brand': d.brand.name,
        'amount': str(d.amount),
        'status': d.status
    } for d in deals])
