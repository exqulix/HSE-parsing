import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
	sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# To run as a script - found of grep.app

from playwright.sync_api import sync_playwright

from db.db import connect_from_env, init_schema, write_events_batch
from scraping.browser import launch_browser, new_context
from scraping.parser import ForexFactoryParser
from scraping.scraper import ForexFactoryScraper

MAX_CALENDAR_ROWS = 10000


def _save_batch(batch):
	"""Fresh connection each time: avoids idle disconnect during long browser runs."""
	with connect_from_env() as conn:
		return write_events_batch(conn, batch)


def main():
	all_rows = []
	total_saved = 0

	with connect_from_env() as conn:
		init_schema(conn)

	with sync_playwright() as pw:

		browser = launch_browser(pw)
		context = new_context(browser)
		page = context.new_page()

		try:
			scraper = ForexFactoryScraper(page)
			scraper.open_homepage()
			scraper.wait_for_homepage_calendar()
			scraper.apply_calendar_filter_settings(date_range="This Week")

			parser = ForexFactoryParser()

			while len(all_rows) < MAX_CALENDAR_ROWS:
				scraper.expand_all_event_details()
				batch = parser.parse_calendar_page(scraper.get_calendar_table_outer_html())
				all_rows.extend(batch)
				if batch:
					total_saved += _save_batch(batch)
				if len(all_rows) >= MAX_CALENDAR_ROWS:
					break
				if not scraper.go_to_next_calendar_page():
					break
		finally:
			page.close()
			context.close()
			browser.close()
			# https://playwright.dev/python/docs/api/class-browser

	print("scraped", len(all_rows), "rows,", total_saved, "row-writes upserted to Postgres (by batch)")


main()
