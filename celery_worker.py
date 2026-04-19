from app import create_app, celery
from app.tasks.celery_schedule import configure_celery_beat

app = create_app(config_name='development')
configure_celery_beat(celery)
