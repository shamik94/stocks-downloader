import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yfinance as yf

# Assuming country_columns is imported correctly
from src.mapper.country_columns import country_columns

Base = declarative_base()

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

# Get the DATABASE_URL from Heroku's environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    # Fallback to local settings if DATABASE_URL is not set
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'stockdata')
    DB_USER = os.environ.get('DB_USER', 'user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    try:
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")


def save_stock_data(df, symbol, country):
    session = Session()
    try:
        for _, row in df.iterrows():
            stock_data = StockData(
                symbol=symbol,
                date=row['date'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                country=country
            )
            session.add(stock_data)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving data: {e}")
    finally:
        session.close()

def unload(start_date, end_date, country, stock):
    print(f'Unloading Stock {stock} from start_date = {start_date} to end_date = {end_date}')
    try:
        df = get_sorted_data(stock, start_date, end_date, country)
        save_stock_data(df, stock, country)
    except Exception as e:
        print(f"Error Fetching Data: {e}")

def unload_all(start_date, end_date, country):
    stock_list_path = Path(__file__).parent / f"../resources/stock_list/{country}"
    print(f"Looking for stock list file at: {stock_list_path}")

    try:
        with stock_list_path.open() as f:
            stock_list = f.read().splitlines()

        if not stock_list:
            print(f"No stocks found for country: {country}")
            return

        for stock in stock_list:
            unload(start_date, end_date, country, stock)
    except FileNotFoundError:
        print(f"Stock list file not found for country: {country}")
    except Exception as e:
        print(f"Error in unload_all: {e}")

def get_sorted_data(stock, start_date, end_date, country):
    df = fetchData(symbol=stock, from_date=start_date, to_date=end_date, country=country)
    if df is None or df.empty:
        raise ValueError(f"No data fetched for stock: {stock}")
    
    required_columns = [
        country_columns[country]["date"],
        country_columns[country]["open"],
        country_columns[country]["high"],
        country_columns[country]["low"],
        country_columns[country]["close"],
        country_columns[country]["volume"],
    ]
    
    df = df[required_columns].copy()
    df = df.sort_values(country_columns[country]["date"])
    df.rename(columns={
        country_columns[country]["open"]: "open",
        country_columns[country]["high"]: "high",
        country_columns[country]["low"]: "low",
        country_columns[country]["date"]: "date",
        country_columns[country]["close"]: "close",
        country_columns[country]["volume"]: "volume",
    }, inplace=True)
    return df

def fetchData(symbol, from_date, to_date, country):
    if country in ['usa', 'crypto', 'germany']:
        try:
            df = yf.download(symbol, start=from_date, end=to_date)
            if df.empty:
                print(f"No data available for {symbol} from {from_date} to {to_date}")
                return None
            return df.reset_index()
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    else:
        print(f"Data fetching not implemented for country: {country}")
        return None

if __name__ == "__main__":
    init_db()
    print("Database initialized")