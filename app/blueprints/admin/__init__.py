from flask import Blueprint, jsonify
from flask_login import login_required
from app.utils.decorators import admin_required
from app.models.user import User
from app.models.deal import Deal
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/', methods=['GET'])
@login_required
@admin_required
def index():
    # Will be a proper HTML template in production, matching checklist
    # For now, API returning data as the spec also mentions /admin/api/... endpoints
    return jsonify({"message": "Admin dashboard"}), 200

@admin_bp.route('/api/users', methods=['GET'])
@login_required
@admin_required
def api_users():
    users = User.query.order_by(User.created_at.desc()).all()
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
