import os
import time
from pathlib import Path
from typing import Optional

import yfinance as yf
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.service.unloader_service import StockInfo, _session, init_db

COUNTRIES = [c.strip() for c in os.environ.get('COUNTRIES', 'usa').split(',')]


def _yf_symbol(symbol: str, country: str) -> str:
    if country == 'india':
        return symbol + '.NS'
    return symbol


def _fetch_info(symbol: str, country: str) -> Optional[dict]:
    yf_symbol = _yf_symbol(symbol, country)
    try:
        info = yf.Ticker(yf_symbol).info
        if not info or info.get('trailingPegRatio') is None and info.get('symbol') is None:
            print(f"  No info returned for {yf_symbol}")
            return None
        return {
            'symbol': symbol,
            'country': country,
            'company_name': info.get('longName'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency'),
            'exchange': info.get('exchange'),
        }
    except Exception as e:
        print(f"  Error fetching info for {yf_symbol}: {e}")
        return None


def _upsert(data: dict):
    stmt = (
        pg_insert(StockInfo)
        .values(**data)
        .on_conflict_do_update(
            index_elements=['symbol', 'country'],
            set_={k: data[k] for k in data if k not in ('symbol', 'country')},
        )
    )
    with _session() as session:
        session.execute(stmt)


def populate_all():
    init_db()
    for country in COUNTRIES:
        stock_list_path = Path(__file__).parent / f"resources/stock_list/{country}"
        try:
            stocks = [s for s in stock_list_path.read_text().splitlines() if s.strip()]
        except FileNotFoundError:
            print(f"Stock list not found for country: {country}")
            continue

        print(f"\nPopulating stock info for {country} ({len(stocks)} stocks)")
        for stock in stocks:
            print(f"  {stock}", end=' ', flush=True)
            data = _fetch_info(stock, country)
            if data:
                _upsert(data)
                print(f"→ {data.get('industry') or 'N/A'}")
            else:
                print("→ skipped")
            time.sleep(1)

        print(f"Done with {country}")


if __name__ == '__main__':
    populate_all()
