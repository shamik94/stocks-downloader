import os
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.service.unloader_service import init_db, unload_all

COUNTRIES = os.environ.get('COUNTRIES', 'india,usa').split(',')
START_DATE = os.environ.get('HISTORY_START_DATE', '2020-01-01')


def run_unload():
    end_date = datetime.now().strftime('%Y-%m-%d')
    print(f"Running unload for: {COUNTRIES}")
    for country in COUNTRIES:
        unload_all(START_DATE, end_date, country)
    print("Unload complete.")


if __name__ == "__main__":
    init_db()
    run_unload()

    scheduler = BlockingScheduler()
    scheduler.add_job(run_unload, CronTrigger(day_of_week='mon-fri', hour=0, minute=0))
    print("Scheduler running. Tasks fire weekdays at midnight.")
    scheduler.start()
