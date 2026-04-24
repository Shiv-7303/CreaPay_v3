from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from app import db
from app.models.user import User
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not full_name or not email or not password:
            flash("All fields are required.", "error")
            return render_template('auth/register.html')
            
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template('auth/register.html')
            
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=password_hash
        )
        
        # Since we use hard deletes, existing email means active/suspended user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Account already exists with this email.", "error")
            return render_template('auth/register.html')

        try:
            db.session.add(new_user)
            db.session.commit()
            # Log the user in immediately after registration
            login_user(new_user)
            flash("Registration successful!", "success")
            return redirect(url_for('dashboard.index'))
        except IntegrityError:
            db.session.rollback()
            flash("Account already exists with this email.", "error")
            
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            if not user.is_active:
                flash("This account has been suspended by the administrator.", "error")
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash("Invalid email or password.", "error")
            
    return render_template('auth/login.html')

from app.utils.decorators import pro_required
from app.utils.storage import upload_image_to_r2
from werkzeug.utils import secure_filename
import uuid

@auth_bp.route('/settings/logo-upload', methods=['POST'])
@login_required
@pro_required
def logo_upload():
    if 'logo' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['logo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Ensure unique name
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in ['png', 'jpg', 'jpeg']:
             return jsonify({'error': 'Only PNG and JPG are allowed'}), 400
             
        new_filename = f"logo_{current_user.id}_{uuid.uuid4().hex[:6]}.{ext}"
        
        file_bytes = file.read()
        # limit size to 2MB
        if len(file_bytes) > 2 * 1024 * 1024:
            return jsonify({'error': 'File too large (max 2MB)'}), 400
            
        url = upload_image_to_r2(file_bytes, new_filename, file.content_type)
        if not url:
            return jsonify({'error': 'Upload failed'}), 500
            
        current_user.logo_url = url
        db.session.commit()
        return jsonify({'logo_url': url}), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/dev/toggle-pro', methods=['GET'])
@login_required
def toggle_pro():
    from app.models.subscription import Subscription
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)

    if current_user.plan == 'pro':
        current_user.plan = 'free'
        current_user.plan_expires_at = None
        # Cancel active subscriptions
        active_subs = Subscription.query.filter_by(user_id=current_user.id, status='active').all()
        for sub in active_subs:
            sub.status = 'cancelled'
        flash("You are now a Free user.", "info")
    else:
        current_user.plan = 'pro'
        current_user.plan_expires_at = now + timedelta(days=30)
        # Create a mock subscription record
        sub = Subscription(
            user_id=current_user.id,
            razorpay_payment_id='dev_toggle_upgrade',
            plan='pro',
            amount_paid=0.0,
            starts_at=now,
            expires_at=current_user.plan_expires_at,
            status='active'
        )
        db.session.add(sub)
        flash("You are now a Pro user for testing.", "success")

    db.session.commit()
    return redirect(url_for('dashboard.index'))
