
# Stock Downloader (Unloader)
This project is designed to download stock data for specific countries over a time range, store it in a PostgreSQL database, and schedule recurring tasks using Python's schedule library.

## Prerequisites

- Docker
- Docker Compose

## Services Overview

- **PostgreSQL**: Stores stock data.
- **yfinance**: Python library used to fetch stock data.

## Getting Started

### 1. Clone the Repository

```bash
git clone git@github.com:shamik94/stocks-downloader.git
cd stocks-downloader
```

### 2. Build and Run the Docker Containers

First, ensure that Docker is running. Then, run the following commands to start the services:

```bash
docker-compose up --build
```

This will:
- Build the app Docker image.
- Start PostgreSQL

### 3. Access the Services

- PostgreSQL will be accessible on port `5433` (as configured in the `docker-compose.yml` file).

### 4. Running Scheduler

After setting up the database, you can run the Python scheduler. It will initialize the database and download stock data:

python src/scheduler.py


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
  

## Stock Data Fetching

The stock data is fetched using the `yfinance` API. The service retrieves data based on predefined stock lists located in `src/resources/stock_list/`. These lists include stock symbols for different countries (e.g., `usa`, `crypto`, `germany`, etc.).

### Adding More Stocks

To add more stocks, modify the relevant country file in the `src/resources/stock_list/` directory. Each line in these files should contain a stock symbol.

## Task Scheduling

By default, the `unload_all` task is scheduled to run every weekday at midnight:

```python
app.conf.beat_schedule = {
    'unload-all-weekdays': {
        'task': 'src.scheduler.scheduled_unload_all',
        'schedule': crontab(hour=0, minute=0, day_of_week='1-5'),  # Weekdays at midnight
    },
}
```

## Common Issues

### Port Conflicts

- PostgreSQL uses port `5433`. If this port are already in use on your machine, you can change them in the `docker-compose.yml` file.

### Module Import Errors

If you encounter module import errors (e.g., `ModuleNotFoundError`), ensure that your working directory is set up correctly, and the Python path includes `/app` (this is set in the Dockerfile).

## License

This project is licensed under the MIT License.
