import schedule
import time
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

# Schedule the unload task to run on weekdays at midnight
schedule.every().monday.at("00:00").do(scheduled_unload_all)
schedule.every().tuesday.at("00:00").do(scheduled_unload_all)
schedule.every().wednesday.at("00:00").do(scheduled_unload_all)
schedule.every().thursday.at("00:00").do(scheduled_unload_all)
schedule.every().friday.at("00:00").do(scheduled_unload_all)

if __name__ == "__main__":
    at_start()  # Initialize the database and run the task at startup
    
    print("Scheduler started. Running tasks at the scheduled time...")
    
    # Run the schedule in an infinite loop
    while True:
        schedule.run_pending()
        time.sleep(1)
