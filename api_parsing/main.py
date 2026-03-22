from api_parsing.alphavantage_fx import parse_to_db
from db.db import connect_from_env, init_schema


def main():
	conn = connect_from_env()
	try:
		init_schema(conn)
		total_bars = parse_to_db(conn)
		print("Added:", total_bars)
	finally:
		conn.close()


if __name__ == "__main__":
	main()
