from functools import wraps
from flask import jsonify, abort, redirect, url_for
from flask_login import current_user

def pro_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.plan != 'pro':
            # Could be handled globally by a custom error handler in a real app
            # For APIs, return JSON
            return jsonify({'error': 'Pro plan required', 'upgrade_required': True}), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import flash, request
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not getattr(current_user, 'is_admin', False):
            if request.path.startswith('/admin/api'):
                return jsonify({'error': 'Admin access required'}), 403
            flash("Admin access required.", "error")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
