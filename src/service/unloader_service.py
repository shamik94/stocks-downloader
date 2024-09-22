import os
import time  # Import time module for sleep
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yfinance as yf
from jugaad_data.nse import stock_df

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

engine = create_engine(DATABASE_URL)

# Create engine and session
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
            # Create a new StockData object
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
    print(f'Processing Stock {stock}')
    session = Session()
    try:
        # Check for the latest date we have data for this stock
        latest_entry = session.query(StockData).filter(StockData.symbol == stock).order_by(StockData.date.desc()).first()
        if latest_entry:
            # Set start_date to the day after the latest date we have
            start_date_in_db = latest_entry.date
            start_date = (start_date_in_db + timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"Data already exists up to {latest_entry.date} for {stock}. Updating start_date to {start_date}")
            
            # Check if start_date is Friday and end_date is a weekend
            start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
            if start_date_dt.weekday() == 4 and end_date_dt.weekday() in [5, 6]:
                print(f"Skipping {stock}: start_date is Friday and end_date is a weekend")
                return
        else:
            print(f"No existing data found for {stock}. Using start_date {start_date}")
        session.close()

        # Check if start_date is after end_date
        if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
            print(f"No new data to fetch for {stock}")
            return

        print(f'Unloading Stock {stock} from start_date = {start_date} to end_date = {end_date}')
        df = get_sorted_data(stock, start_date, end_date, country)
        save_stock_data(df, stock, country)
        time.sleep(2)  # Sleep for 2 seconds after processing each stock
    except Exception as e:
        print(f"Error fetching data for {stock}: {e}")

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
    if country == 'india':
        from_date_dt = datetime.strptime(from_date, '%Y-%m-%d')
        to_date_dt = datetime.strptime(to_date, '%Y-%m-%d')
        return stock_df(symbol, from_date_dt, to_date_dt, series="EQ")
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
    
    # Set start_date to January 1, 2020, and end_date to current date
    start_date = '2020-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    country = 'usa'  # Specify the country you want to process

    unload_all(start_date, end_date, country)
