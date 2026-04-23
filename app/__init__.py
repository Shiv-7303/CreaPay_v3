import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from celery import Celery
from .config import config
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def make_celery(app_name=__name__):
    celery = Celery(app_name)
    celery.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    celery.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    return celery

celery = make_celery()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Initialize celery with app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # Import celery tasks so they are registered
    from app.tasks import overdue
    from app.tasks import reminders

    # user loader
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Make sure all models are imported so Alembic can see them
    from app.models.user import User
    from app.models.brand import Brand
    from app.models.invoice import Invoice
    from app.models.subscription import Subscription
    from app.models.activity_log import ActivityLog

    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    sentry_dsn = app.config.get('SENTRY_DSN') or os.environ.get('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FlaskIntegration(),
                CeleryIntegration(),
                SqlalchemyIntegration()
            ],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.deals import api_bp, deals_bp
    from app.blueprints.invoices import invoices_bp
    from app.blueprints.payments import payments_bp
    from app.blueprints.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(deals_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)
    
    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for
        
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
            
        # Basic landing page logic as requested in "empty dashboard loads at /"
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CreaPay</title>
            <style>
                body { font-family: sans-serif; text-align: center; margin-top: 50px; }
                a { display: inline-block; padding: 10px 20px; background: #6C47FF; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <h1>Welcome to CreaPay</h1>
            <p>Manage your deals and invoices.</p>
            <a href="/auth/login">Login</a>
            <a href="/auth/register">Register</a>
        </body>
        </html>
        """
        
    @app.route('/health')
    def health():
        return "OK", 200

    return app
