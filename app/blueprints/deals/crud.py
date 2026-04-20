from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.deal import Deal
from app.models.brand import Brand
from datetime import datetime, timedelta
from app.utils.decorators import pro_required
from app.tasks.reminders import send_reminder

deals_bp = Blueprint('deals', __name__, url_prefix='/deals')

@deals_bp.route('/', methods=['GET'])
@login_required
def list_deals():
    deals = Deal.query.filter_by(user_id=current_user.id, deleted_at=None).all()
    # Provide simple json for API/frontend integration
    return jsonify([{
        'id': d.id,
        'brand_id': d.brand_id,
        'brand_name': d.brand.name,
        'amount': str(d.amount),
        'content_type': d.content_type,
        'due_date': d.due_date.isoformat(),
        'status': d.status,
        'tds_applicable': d.tds_applicable
    } for d in deals])

@deals_bp.route('/create', methods=['POST'])
@login_required
def create_deal():
    data = request.json or request.form
    
    brand_name = data.get('brand_name')
    if not brand_name or not brand_name.strip():
        return jsonify({'error': 'Please provide a valid brand name.'}), 400
        
    brand_name = brand_name.strip()
    if len(brand_name) > 255:
        return jsonify({'error': 'Brand name is too long. Please keep it under 255 characters.'}), 400
        
    amount = data.get('amount')
    if not amount or float(amount) < 0:
        return jsonify({'error': 'Please enter a valid deal amount.'}), 400
        
    content_type = data.get('content_type')
    if not content_type:
        return jsonify({'error': 'Please select a content type.'}), 400
    due_date_str = data.get('due_date')
    tds_applicable = str(data.get('tds_applicable', 'false')).lower() == 'true'
    notes = data.get('notes')
    
    # Auto-create brand if it doesn't exist
    brand = Brand.query.filter_by(user_id=current_user.id, name=brand_name).first()
    if not brand:
        brand = Brand(user_id=current_user.id, name=brand_name)
        db.session.add(brand)
        db.session.flush() # To get brand.id
    
    # Parse due date or default to +30 days
    if due_date_str:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    else:
        due_date = (datetime.now() + timedelta(days=30)).date()
        
    # Free Plan Gate (Step 7 logic incorporated partially here)
    if current_user.plan == 'free':
        deal_count = Deal.query.filter_by(user_id=current_user.id, deleted_at=None).count()
        from flask import current_app
        limit = current_app.config.get('FREE_DEAL_LIMIT', 3)
        if deal_count >= limit:
            return jsonify({
                "error": "Upgrade required",
                "upgrade_required": True,
                "limit": limit,
                "current": deal_count
            }), 402

    deal = Deal(
        user_id=current_user.id,
        brand_id=brand.id,
        amount=amount,
        content_type=content_type,
        due_date=due_date,
        tds_applicable=tds_applicable,
        notes=notes,
        status='negotiating'
    )
    
    brand.total_deals += 1
    db.session.add(deal)
    db.session.flush() # flush to get deal.id
    
    # Auto-generate invoice
    from app.blueprints.invoices import auto_generate_invoice
    auto_generate_invoice(deal)
    
    db.session.commit()
    
    return jsonify({'id': deal.id, 'status': deal.status, 'brand_id': brand.id}), 201

@deals_bp.route('/<deal_id>', methods=['GET'])
@login_required
def get_deal(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id, deleted_at=None).first_or_404()
    return jsonify({
        'id': deal.id,
        'brand_id': deal.brand_id,
        'brand_name': deal.brand.name,
        'amount': str(deal.amount),
        'content_type': deal.content_type,
        'due_date': deal.due_date.isoformat(),
        'status': deal.status,
        'notes': deal.notes,
        'tds_applicable': deal.tds_applicable
    })

@deals_bp.route('/<deal_id>/status', methods=['PATCH'])
@login_required
def update_deal_status(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id, deleted_at=None).first_or_404()
    new_status = request.json.get('status')
    
    valid_transitions = {
        'negotiating': ['active', 'overdue'],
        'active': ['invoice_sent', 'overdue'],
        'invoice_sent': ['paid', 'overdue'],
        'paid': [],
        'overdue': ['paid']
    }
    
    if new_status not in valid_transitions.get(deal.status, []):
        return jsonify({'error': f'Invalid status transition from {deal.status} to {new_status}'}), 400
        
    deal.status = new_status
    if new_status == 'paid':
        deal.paid_at = datetime.now()
        
    db.session.commit()
    return jsonify({'id': deal.id, 'status': deal.status})

@deals_bp.route('/<deal_id>/mark-paid', methods=['POST'])
@login_required
def mark_deal_paid(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id, deleted_at=None).first_or_404()
    deal.status = 'paid'
    deal.paid_at = datetime.now()
    db.session.commit()
    return jsonify({'id': deal.id, 'status': deal.status})

@deals_bp.route('/<deal_id>/remind', methods=['POST'])
@login_required
@pro_required
def remind_deal(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id, deleted_at=None).first_or_404()
    
    msg = request.json.get('message') if request.is_json and request.json else None
    
    # Enqueue celery task
    send_reminder.delay(deal.id, msg)
    
    return jsonify({'status': 'reminder queued', 'deal_id': deal.id}), 200

@deals_bp.route('/<deal_id>', methods=['DELETE'])
@login_required
def delete_deal(deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id, deleted_at=None).first_or_404()
    deal.deleted_at = datetime.now()
    deal.brand.total_deals -= 1
    db.session.commit()
    return jsonify({'message': 'Deal deleted successfully'}), 200
