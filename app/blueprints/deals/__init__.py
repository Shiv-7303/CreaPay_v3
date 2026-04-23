from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.brand import Brand
from app.blueprints.deals.crud import deals_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/brands/search', methods=['GET'])
@login_required
def search_brands():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
        
    brands = Brand.query.filter(
        Brand.user_id == current_user.id,
        Brand.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify([
        {'id': b.id, 'name': b.name} for b in brands
    ])
