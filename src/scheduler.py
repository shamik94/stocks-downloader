import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready
from datetime import datetime, timedelta

from src.service.unloader_service import unload_all, init_db

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
    print("Scheduled unload task started")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    countries = ['usa']
    for country in countries:
        print(f"Processing country: {country}")
        unload_all(start_date, end_date, country)
    print("Scheduled unload task completed")

# Signal to initialize the database and trigger the task when the worker is ready
@worker_ready.connect
def at_start(sender, **kwargs):
    print("Worker is ready, initializing database and triggering scheduled_unload_all task.")
    init_db()  # Initialize the database
    scheduled_unload_all.delay()  # Asynchronously trigger the task

# Schedule tasks
app.conf.beat_schedule = {
    'unload-all-weekdays': {
        'task': 'src.scheduler.scheduled_unload_all',
        'schedule': crontab(hour=0, minute=0, day_of_week='1-5'),  # Weekdays at midnight
    },
}

if __name__ == "__main__":
    app.start()
