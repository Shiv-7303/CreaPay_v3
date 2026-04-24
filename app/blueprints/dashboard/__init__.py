from flask import Blueprint, render_template
from flask_login import login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from app.models.deal import Deal
from sqlalchemy import func

import csv
import io
from flask import make_response, current_app
from app.utils.decorators import pro_required
from datetime import datetime
from flask_login import current_user

from flask import jsonify

@dashboard_bp.route('/brand-report')
@login_required
@pro_required
def brand_report():
    deals = Deal.query.filter_by(user_id=current_user.id, deleted_at=None).all()
    
    report = {}
    for deal in deals:
        brand_name = deal.brand.name
        if brand_name not in report:
            report[brand_name] = {
                'brand': brand_name,
                'earned': 0,
                'pending': 0,
                'count': 0,
                'last_deal': None
            }
            
        report[brand_name]['count'] += 1
        
        if deal.status == 'paid':
            report[brand_name]['earned'] += float(deal.amount)
        else:
            report[brand_name]['pending'] += float(deal.amount)
            
        deal_date = deal.created_at.strftime('%Y-%m-%d')
        if not report[brand_name]['last_deal'] or deal_date > report[brand_name]['last_deal']:
            report[brand_name]['last_deal'] = deal_date
            
    # Sort by earned desc
    sorted_report = sorted(report.values(), key=lambda x: x['earned'], reverse=True)
    return jsonify(sorted_report)

@dashboard_bp.route('/export-csv')
@login_required
@pro_required
def export_csv():
    deals = Deal.query.filter_by(user_id=current_user.id, deleted_at=None).all()
    
    # In memory string file
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Header
    cw.writerow(['Brand', 'Amount (₹)', 'TDS (₹)', 'Net Amount (₹)', 'Status', 'Content Type', 'Due Date', 'Created Date', 'Invoice Number'])
    
    for deal in deals:
        invoice = getattr(deal, 'invoice', None)
        tds_amount = invoice.tds_amount if invoice else (deal.amount * 0.1 if deal.tds_applicable else 0)
        net_amount = invoice.net_amount if invoice else (deal.amount - tds_amount)
        invoice_num = invoice.invoice_number if invoice else 'N/A'
        
        cw.writerow([
            deal.brand.name,
            deal.amount,
            tds_amount,
            net_amount,
            deal.status,
            deal.content_type,
            deal.due_date.isoformat(),
            deal.created_at.strftime('%Y-%m-%d'),
            invoice_num
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=creapay_deals_{datetime.now().strftime('%Y%m%d')}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@dashboard_bp.route('/')
@login_required
def index():
    # Check subscription expiry
    from app import db
    if current_user.plan == 'pro' and current_user.plan_expires_at and current_user.plan_expires_at < datetime.now():
        current_user.plan = 'free'
        db.session.commit()

    deals = Deal.query.filter_by(user_id=current_user.id, deleted_at=None).all()
    
    # Custom sorting logic based on the spec
    def deal_sort_key(d):
        if d.status == 'overdue': return 0
        if d.status == 'active': return 1
        if d.status == 'negotiating': return 2
        if d.status == 'paid': return 3
        return 4
        
    deals.sort(key=deal_sort_key)
    
    total_earned = sum(d.amount for d in deals if d.status == 'paid')
    total_pending = sum(d.amount for d in deals if d.status in ['negotiating', 'active', 'invoice_sent'])
    overdue_count = sum(1 for d in deals if d.status == 'overdue')
    total_tds = sum(d.invoice.tds_amount for d in deals if getattr(d, 'invoice', None) and d.tds_applicable)
    
    return render_template('dashboard/index.html',
                           deals=deals,
                           total_earned=total_earned,
                           total_pending=total_pending,
                           overdue_count=overdue_count,
                           total_tds=total_tds)

@dashboard_bp.route('/upgrade')
@login_required
def upgrade():
    return render_template('dashboard/upgrade.html')


@dashboard_bp.route('/monthly-report')
@login_required
@pro_required
def monthly_report():
    deals = Deal.query.filter_by(user_id=current_user.id, deleted_at=None).all()
    
    report = {}
    for deal in deals:
        month = deal.created_at.strftime('%Y-%m')
        if month not in report:
            report[month] = {
                'month': month,
                'earned': 0,
                'pending': 0
            }
            
        if deal.status == 'paid':
            report[month]['earned'] += float(deal.amount)
        else:
            report[month]['pending'] += float(deal.amount)
            
    # Sort by month desc
    sorted_report = sorted(report.values(), key=lambda x: x['month'], reverse=True)
    return jsonify(sorted_report)
