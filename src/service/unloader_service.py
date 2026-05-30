import os
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import yfinance as yf
from jugaad_data.nse import stock_df

from src.mapper.country_columns import country_columns

Base = declarative_base()

DATE_FORMAT = '%Y-%m-%d'

# Set STOCK_START_ENABLED=true and STOCK_START_SYMBOL=<symbol> to resume from a specific stock
STOCK_START_ENABLED = os.environ.get('STOCK_START_ENABLED', 'false').lower() == 'true'
STOCK_START_SYMBOL = os.environ.get('STOCK_START_SYMBOL', '')


class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    country = Column(String)


def _build_database_url() -> str:
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    name = os.environ.get('DB_NAME', 'stockdata')
    user = os.environ.get('DB_USER', 'user')
    password = os.environ.get('DB_PASSWORD', 'password')
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


engine = create_engine(_build_database_url())
Session = sessionmaker(bind=engine)


@contextmanager
def _session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    try:
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")


def fetch_data(symbol: str, from_date: str, to_date: str, country: str):
    if country == 'india':
        return stock_df(
            symbol,
            datetime.strptime(from_date, DATE_FORMAT),
            datetime.strptime(to_date, DATE_FORMAT),
            series="EQ",
        )

    if country in country_columns:
        try:
            df = yf.download(symbol, start=from_date, end=to_date)
            if df.empty:
                print(f"No data available for {symbol} from {from_date} to {to_date}")
                return None
            # yfinance >=1.0 returns MultiIndex columns (Price, Ticker); flatten to single level
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df.reset_index()
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    print(f"Data fetching not implemented for country: {country}")
    return None


def _normalize_columns(df, country: str):
    cols = country_columns[country]
    required = [cols["date"], cols["open"], cols["high"], cols["low"], cols["close"], cols["volume"]]
    df = df[required].copy()
    df = df.sort_values(cols["date"])
    df.rename(columns={v: k for k, v in cols.items()}, inplace=True)
    return df


def _save_stock_data(df, symbol: str, country: str):
    rows = [
        StockData(
            symbol=symbol,
            date=row['date'],
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume'],
            country=country,
        )
        for _, row in df.iterrows()
    ]
    with _session() as session:
        session.add_all(rows)


def unload(start_date: str, end_date: str, country: str, stock: str):
    print(f'Processing stock: {stock}')

    with _session() as session:
        latest = (
            session.query(StockData)
            .filter(StockData.symbol == stock)
            .order_by(StockData.date.desc())
            .first()
        )
        if latest:
            start_date = (latest.date + timedelta(days=1)).strftime(DATE_FORMAT)
            print(f"Resuming {stock} from {start_date}")
        else:
            print(f"No existing data for {stock}, starting from {start_date}")

    if datetime.strptime(start_date, DATE_FORMAT) > datetime.strptime(end_date, DATE_FORMAT):
        print(f"No new data to fetch for {stock}")
        return

    print(f'Fetching {stock}: {start_date} → {end_date}')
    try:
        df = fetch_data(symbol=stock, from_date=start_date, to_date=end_date, country=country)
        if df is None or df.empty:
            print(f"No data returned for {stock}")
            return
        df = _normalize_columns(df, country)
        _save_stock_data(df, stock, country)
    except Exception as e:
        print(f"Error processing {stock}: {e}")


def unload_all(start_date: str, end_date: str, country: str):
    print(f"Starting unload for country: {country}")
    stock_list_path = Path(__file__).parent.parent / f"resources/stock_list/{country}"

    try:
        stock_list = stock_list_path.read_text().splitlines()
    except FileNotFoundError:
        print(f"Stock list not found: {stock_list_path}")
        return

    if not stock_list:
        print(f"No stocks found for country: {country}")
        return

    start_processing = not STOCK_START_ENABLED

    for stock in stock_list:
        if not start_processing:
            if stock == STOCK_START_SYMBOL:
                start_processing = True
                print(f"Found start symbol: {stock}")
            else:
                print(f"Skipping {stock}")
            continue

        unload(start_date, end_date, country, stock)
        time.sleep(2)

    print(f"Finished unload for country: {country}")
