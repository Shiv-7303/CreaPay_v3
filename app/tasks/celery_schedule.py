from celery.schedules import crontab
from app.config import Config

# Need to configure beat schedule in celery app
def configure_celery_beat(celery_app):
    celery_app.conf.beat_schedule = {
        'mark-overdue-daily': {
            'task': 'check_and_mark_overdue',
            # Run at 2:00 AM every day
            'schedule': crontab(minute=0, hour=2),
        },
    }
