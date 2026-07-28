import os

from src.service.unloader_service import init_db, unload_earnings_all

COUNTRIES = [c.strip() for c in os.environ.get('COUNTRIES', 'usa').split(',')]
EARNINGS_SKIP_COUNTRIES = {'crypto'}


def populate_all():
    init_db()
    for country in COUNTRIES:
        if country in EARNINGS_SKIP_COUNTRIES:
            print(f"Skipping earnings for {country}")
            continue
        unload_earnings_all(country)


if __name__ == '__main__':
    populate_all()
