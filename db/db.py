import os
import re
from datetime import date, datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# USED https://www.psycopg.org/docs/usage.html#passing-parameters-to-sql-queries
_SCHEMA_DDL = [
	"""
	CREATE TABLE IF NOT EXISTS events (
		id SERIAL PRIMARY KEY,
		event_id VARCHAR UNIQUE NOT NULL,
		datetime TIMESTAMP,
		currency VARCHAR,
		currency_full VARCHAR,
		impact VARCHAR,
		title TEXT,
		actual VARCHAR,
		forecast VARCHAR,
		previous VARCHAR
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS event_specs (
		id SERIAL PRIMARY KEY,
		event_id INTEGER NOT NULL REFERENCES events (id),
		label TEXT,
		value TEXT
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS event_history (
		id SERIAL PRIMARY KEY,
		event_id INTEGER NOT NULL REFERENCES events (id),
		date DATE,
		actual VARCHAR,
		forecast VARCHAR,
		previous VARCHAR
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS currency_ohlc (
		id SERIAL PRIMARY KEY,
		from_currency VARCHAR NOT NULL,
		to_currency VARCHAR NOT NULL,
		bar_date DATE NOT NULL,
		open VARCHAR,
		high VARCHAR,
		low VARCHAR,
		close VARCHAR,
		UNIQUE (from_currency, to_currency, bar_date)
	)
	""",
]


def connect_from_env():

	load_dotenv(Path(__file__).resolve().parent.parent / ".env")
	db = (os.environ.get("POSTGRES_DB") or "").strip()
	user = (os.environ.get("POSTGRES_USER") or "").strip()
	password = os.environ.get("POSTGRES_PASSWORD").strip()

	if not db or not user or password is None:
		raise RuntimeError(".env not set")

	host = (os.environ.get("POSTGRES_HOST")).strip()
	port = (os.environ.get("POSTGRES_PORT")).strip()

	return psycopg.connect(host=host,port=port,dbname=db,user=user,password=password,client_encoding="UTF8",)


def init_schema(conn):
	with conn.cursor() as cur:
		for stmt in _SCHEMA_DDL:
			cur.execute(stmt)
	conn.commit()


def _norm(s): #Want NONE in db for eda
	if s is None:
		return None
	normed = str(s).strip()
	return normed if normed else None


def _parse_history_date(s):
	s = (s or "").strip()
	if not s:
		return None
	try:
		return datetime.strptime(s, "%b %d, %Y").date()
	except ValueError:
		return None
	


def _combine_date_time(base, time_str):
	midnight = datetime.combine(base, datetime.min.time())
	# datetime.min.time() == 00:00:00.000000
	raw = (time_str or "").strip().lower()
	if not raw:
		return midnight
	token = re.sub(r"\s+", "", raw).upper()
	try:
		t = datetime.strptime(token, "%I:%M%p").time()
		return datetime.combine(base, t)
	except ValueError:
		return midnight


def _parse_month_day(day_str):
	parts = (day_str or "").split()
	if len(parts) < 2:
		return None
	try:
		parsed = datetime.strptime(f"{parts[-2]} {parts[-1]}", "%b %d")
		return parsed.month, parsed.day
	except ValueError:
		return None


# Year was lost while parsing. Came up with this
_year_chain = {"year": None, "prev_month": None}


def write_events_batch(conn, rows):

	ref = date.today()

	insert_sql = """
		INSERT INTO events (
			event_id, datetime, currency, currency_full, impact, title,
			actual, forecast, previous
		)
		VALUES (%(event_id)s, %(datetime)s, %(currency)s, %(currency_full)s,
			%(impact)s, %(title)s, %(actual)s, %(forecast)s, %(previous)s)
		ON CONFLICT (event_id) DO UPDATE SET
			datetime = EXCLUDED.datetime,
			currency = EXCLUDED.currency,
			currency_full = EXCLUDED.currency_full,
			impact = EXCLUDED.impact,
			title = EXCLUDED.title,
			actual = EXCLUDED.actual,
			forecast = EXCLUDED.forecast,
			previous = EXCLUDED.previous
		RETURNING id
	"""
	del_specs_sql = "DELETE FROM event_specs WHERE event_id = %s"
	del_hist_sql = "DELETE FROM event_history WHERE event_id = %s"
	insert_spec_sql = "INSERT INTO event_specs (event_id, label, value) VALUES (%s, %s, %s)"
	insert_hist_sql = """
		INSERT INTO event_history (event_id, date, actual, forecast, previous)
		VALUES (%s, %s, %s, %s, %s)
	"""
	n = 0
	with conn.transaction():
		with conn.cursor() as cur:
			for row in rows:
				event_id = str(row["event_id"])

				# year recovery, build datetime
				md = _parse_month_day(row.get("day"))
				if md is None:
					dt = None
				else:
					month, day = md
					if _year_chain["year"] is None:
						_year_chain["year"] = ref.year
					elif month - _year_chain["prev_month"] > 6:
						_year_chain["year"] -= 1
					elif month - _year_chain["prev_month"] < -6:
						_year_chain["year"] += 1
					_year_chain["prev_month"] = month
					try:
						base = date(_year_chain["year"], month, day)
					except ValueError:
						base = date(_year_chain["year"], month, 28)
					dt = _combine_date_time(base, str(row.get("time") or ""))
				

				payload = {
					"event_id": event_id,
					"datetime": dt,
					"currency": _norm(row.get("currency")),
					"currency_full": _norm(row.get("currency_full")),
					"impact": _norm(row.get("impact_title")),
					"title": _norm(row.get("title")),
					"actual": _norm(row.get("actual")),
					"forecast": _norm(row.get("forecast")),
					"previous": _norm(row.get("previous")),
				}
				cur.execute(insert_sql, payload)


				pk = cur.fetchone()[0]
				detail = row.get("detail")

				if detail is not None:
					# delete if exists before inserting
					cur.execute(del_specs_sql, (pk,))
					cur.execute(del_hist_sql, (pk,))

					for spec in detail.get("specs") or []:

						label = _norm(spec.get("label"))
						value = _norm(spec.get("value"))
						if label is None and value is None:
							continue
						cur.execute(insert_spec_sql, (pk, label, value))

					for history_row in detail.get("history") or []:
						hist_date = _parse_history_date(str(history_row.get("date") or ""))
						if hist_date is None:
							continue
						cur.execute(
							insert_hist_sql,
							(
								pk,
								hist_date,
								_norm(history_row.get("actual")),
								_norm(history_row.get("forecast")),
								_norm(history_row.get("previous")),
							),
						)
				
				n += 1
	return n


def _ohlc_from_bar(bar):
	if not bar:
		return None, None, None, None

	return (
		_norm(bar.get("1. open", "")),
		_norm(bar.get("2. high", "")),
		_norm(bar.get("3. low", "")),
		_norm(bar.get("4. close", "")),
	)


def write_ohlc_batch(conn, from_currency, to_currency, bars):
	from_c = _norm(from_currency)
	to_c = _norm(to_currency)

	sql = """
		INSERT INTO currency_ohlc (
			from_currency, to_currency, bar_date, open, high, low, close
		)
		VALUES (%s, %s, %s, %s, %s, %s, %s)
		ON CONFLICT (from_currency, to_currency, bar_date) DO UPDATE SET
			open = EXCLUDED.open,
			high = EXCLUDED.high,
			low = EXCLUDED.low,
			close = EXCLUDED.close
	"""
	n = 0
	with conn.transaction():
		with conn.cursor() as cur:
			for date_key, bar in (bars or {}).items():
				try:
					bar_date = datetime.strptime(str(date_key).strip(), "%Y-%m-%d").date()
				except ValueError:
					continue
				o, h, l, c = _ohlc_from_bar(bar)
				cur.execute(sql, (from_c, to_c, bar_date, o, h, l, c))
				n += 1
	return n
