
# Stock Data Unloader

This project is a stock data unloader service that fetches stock data using `yfinance`, processes it, and stores it in a PostgreSQL database. The service uses Celery for task scheduling and Redis as a broker. The application is containerized using Docker and orchestrated with Docker Compose.

## Project Structure

```
/app
│
├── docker-compose.yml          # Orchestrates the services (app, db, redis)
├── Dockerfile                  # Builds the app image
├── requirements.txt            # Python dependencies
├── src/                        # Source files
│   ├── unloader_service.py     # Stock data fetching and database storage logic
│   ├── scheduler.py            # Celery task scheduling and periodic tasks
│   ├── country_columns.py      # Country-specific stock column mappings
│   └── resources/stock_list/   # Stock lists for different countries
│       ├── usa
│       ├── crypto
│       ├── germany
│       └── india
└── README.md                   # Project documentation (this file)
```

## Prerequisites

- Docker
- Docker Compose

## Services Overview

- **PostgreSQL**: Stores stock data.
- **Redis**: Acts as the broker for Celery tasks.
- **Celery**: Handles scheduled tasks for stock data fetching and processing.
- **yfinance**: Python library used to fetch stock data.

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Build and Run the Docker Containers

First, ensure that Docker is running. Then, run the following commands to start the services:

```bash
docker-compose up --build
```

This will:
- Build the app Docker image.
- Start PostgreSQL and Redis.
- Start the Celery worker with beat to handle periodic tasks.

### 3. Access the Services

- The Celery worker will automatically start fetching stock data based on the scheduled tasks defined in `src/scheduler.py`.
- PostgreSQL will be accessible on port `5433` (as configured in the `docker-compose.yml` file).
- Redis will be running on port `6380`.

### 4. Running Celery Tasks

The main Celery tasks are defined in the `src/scheduler.py` file:

- **`scheduled_unload_all`**: This task fetches stock data for predefined stock lists (e.g., for the USA) over a specified date range.
- **`init_database`**: Initializes the PostgreSQL database schema.

Celery automatically schedules these tasks according to the `app.conf.beat_schedule` defined in `scheduler.py`.

### 5. Database Initialization

The PostgreSQL database schema will be initialized when the application starts. If you need to reinitialize the database manually, you can call the `init_db()` function in `src/unloader_service.py`.

## Configuration

You can configure the following environment variables in `docker-compose.yml`:

- **Database**:
  - `DB_HOST`: The hostname of the PostgreSQL service (default: `db`).
  - `DB_PORT`: The port of the PostgreSQL service (default: `5432`).
  - `DB_NAME`: The name of the database (default: `stockdata`).
  - `DB_USER`: The database user (default: `user`).
  - `DB_PASSWORD`: The database password (default: `password`).
  
- **Redis**:
  - `REDIS_HOST`: The Redis service hostname (default: `redis`).
  - `REDIS_PORT`: The Redis service port (default: `6379`).

## Stock Data Fetching

The stock data is fetched using the `yfinance` API. The service retrieves data based on predefined stock lists located in `src/resources/stock_list/`. These lists include stock symbols for different countries (e.g., `usa`, `crypto`, `germany`, etc.).

### Adding More Stocks

To add more stocks, modify the relevant country file in the `src/resources/stock_list/` directory. Each line in these files should contain a stock symbol.

## Task Scheduling

Celery tasks are scheduled in `src/scheduler.py` using the `celery.schedules.crontab` function. By default, the `unload_all` task is scheduled to run every weekday at midnight:

```python
app.conf.beat_schedule = {
    'unload-all-weekdays': {
        'task': 'src.scheduler.scheduled_unload_all',
        'schedule': crontab(hour=0, minute=0, day_of_week='1-5'),  # Weekdays at midnight
    },
}
```

## Customization

- Modify the task schedule in `src/scheduler.py` to fit your needs.
- Add new countries or stock exchanges by creating new files in `src/resources/stock_list/` and updating `country_columns.py` for the appropriate column mappings.

## Common Issues

### Port Conflicts

- PostgreSQL uses port `5433` and Redis uses port `6380`. If these ports are already in use on your machine, you can change them in the `docker-compose.yml` file.

### Module Import Errors

If you encounter module import errors (e.g., `ModuleNotFoundError`), ensure that your working directory is set up correctly, and the Python path includes `/app` (this is set in the Dockerfile).

## License

This project is licensed under the MIT License.
