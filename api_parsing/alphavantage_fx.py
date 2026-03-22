import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from db.db import write_ohlc_batch

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = "https://www.alphavantage.co/query"
MAINKEY = "Time Series FX (Daily)"
TO_USD = "USD"

FX_BAR_CUTOFF = "2023-12-31"

FROM_SYMBOLS_VS_USD = ("AUD","CAD","CHF","CNY","EUR","GBP","JPY","NZD") #calculate usd later


def cutoff_bars(payload):
	series = payload.get(MAINKEY)

	if not series:
		return {}

	bars = {}
	for date_str, ohlc in series.items():
		if date_str >= FX_BAR_CUTOFF:
			bars[date_str] = ohlc

	return bars

# used https://www.alphavantage.co/documentation/
def fetch_alphav(from_cur, api_key):

	params = {
		"function": "FX_DAILY",
		"from_symbol": from_cur,
		"to_symbol": TO_USD,
		"apikey": api_key,
		"outputsize": "full",
	}

	r = requests.get(
		BASE_URL,
		params=params,
		timeout=(30, 600)
	)

	payload = r.json()
	bars = cutoff_bars(payload)
	
	if not bars:
		raise RuntimeError("no bars")
	else:
		return bars


def parse_to_db(conn, api_key=None):
	if api_key is None:
		api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
	if not api_key or not str(api_key).strip():
		raise RuntimeError(".env not set")

	api_key = str(api_key).strip()

	n = 0

	for currency_index, from_cur in enumerate(FROM_SYMBOLS_VS_USD):

		if currency_index:
			time.sleep(1.5)

		bars = fetch_alphav(from_cur, api_key)
		bars_written = write_ohlc_batch(conn, from_cur, TO_USD, bars)

		n += bars_written

	return n
