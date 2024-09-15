from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from src.service.unloader_service import unload_all, init_db

def scheduled_unload_all():
    print("Scheduled unload task started")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    countries = ['usa']
    for country in countries:
        print(f"Processing country: {country}")
        unload_all(start_date, end_date, country)
    print("Scheduled unload task completed")

def at_start():
    print("Initializing database...")
    init_db()  # Initialize the database

    # Trigger the first task immediately at startup
    scheduled_unload_all()

# Create the scheduler
scheduler = BlockingScheduler()

# Schedule the task to run on weekdays (Monday-Friday) at midnight
scheduler.add_job(scheduled_unload_all, CronTrigger(day_of_week='mon-sat', hour=10, minute=47))

if __name__ == "__main__":
    at_start()  # Initialize the database and run the first task at startup

    print("Scheduler started. Running tasks at the scheduled time...")

    # Start the APScheduler event loop
    scheduler.start()
