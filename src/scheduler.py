import os
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta

from src.unloader_service import unload_all
from src.unloader_service import init_db  # Import the init_db function

# Set up Celery with environment variables
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')
app = Celery('tasks', broker=f'redis://{redis_host}:{redis_port}/0')

# Configure Celery
app.conf.update(
    result_backend=f'redis://{redis_host}:{redis_port}/0',
    timezone='UTC'
)

@app.task
def scheduled_unload_all():
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    countries = ['usa']
    for country in countries:
        unload_all(start_date, end_date, country)

@app.task
def init_database():
    init_db()

# Schedule tasks
app.conf.beat_schedule = {
    'unload-all-weekdays': {
        'task': 'src.scheduler.scheduled_unload_all',
        'schedule': crontab(hour=0, minute=0, day_of_week='1-5'),  # Run on weekdays (Monday=1, Friday=5) at midnight
    },
}

if __name__ == "__main__":
    init_db()  # Initialize the database once when the application starts
    print("Database initialized")
    app.start()  # Start Celery worker with scheduled tasks
