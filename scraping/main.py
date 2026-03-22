import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
	sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# To run as a script - found of grep.app

from playwright.sync_api import sync_playwright

from scraping.browser import launch_browser, new_context
from scraping.parser import ForexFactoryParser
from scraping.scraper import ForexFactoryScraper

MAX_CALENDAR_ROWS = 80


def main():
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
			all_rows = []

			while len(all_rows) < MAX_CALENDAR_ROWS:
				scraper.expand_all_event_details()
				batch = parser.parse_calendar_page(scraper.get_calendar_table_outer_html())
				all_rows.extend(batch)
				if len(all_rows) >= MAX_CALENDAR_ROWS:
					break
				if not scraper.go_to_next_calendar_page():
					break
			
			print(len(all_rows), all_rows)
		finally:
			page.close()
			context.close()
			browser.close()
			# https://playwright.dev/python/docs/api/class-browser


main()
