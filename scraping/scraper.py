"""Open, interact with FF, get the calendar table HTML"""
from playwright.sync_api import Page, Response

FOREX_FACTORY_URL = "https://www.forexfactory.com/"

OPTIONS_LABEL_SPAN = "a.highlight.light.options span"
DATE_RANGE_SHORTCUTS = "div.calendar__date-range-shortcuts"
APPLY_SETTINGS = 'input[type="submit"].overlay__button--submit[value="Apply Settings"]'
CALENDAR_TABLE = "table.calendar__table"
CALENDAR_BLOCK = "div.flexBox.calendar"
DETAIL_LINK = 'td.calendar__detail a.calendar__detail-link[title="Open Detail"]'


# Used https://playwright.dev/python/docs/locators and other pages


class ForexFactoryScraper:
	def __init__(self, page: Page):

		self._page = page

	def open_homepage(self, *, wait_until= "domcontentloaded"):

		return self._page.goto(FOREX_FACTORY_URL, wait_until=wait_until)

	def wait_for_homepage_calendar(self):

		table = self._page.locator(CALENDAR_TABLE).first

		table.wait_for(state="visible", timeout=60_000)
		table.scroll_into_view_if_needed()

	def get_calendar_table_outer_html(self):

		loc = self._page.locator(CALENDAR_TABLE).first
		loc.wait_for(state="attached", timeout=30_000)

		return loc.evaluate("el => el.outerHTML")

	def get_current_options_label(self):

		loc = self._page.locator(OPTIONS_LABEL_SPAN).first
		loc.wait_for(state="visible", timeout=60_000)

		return loc.inner_text().strip()

	def apply_calendar_filter_settings(self, date_range):
		
		before = self.get_current_options_label()

		self._page.locator("a.highlight.light.options").first.click()
		self._page.locator(DATE_RANGE_SHORTCUTS).wait_for(state="visible", timeout=30_000)
		self._page.locator(f"{DATE_RANGE_SHORTCUTS} a.internal", has_text=date_range).click()
		self._page.locator(APPLY_SETTINGS).click()

		self.wait_for_calendar_table_refresh(before)

	def wait_for_calendar_table_refresh(self, previous):
		"""Wait for calendar table to update"""
		#https://playwright.dev/python/docs/api/class-page#page-wait-for-function
		self._page.wait_for_function( 
			"""(prev) => {
				const el = document.querySelector('a.highlight.light.options span');
				if (!el) return false;
				return (el.textContent || '').trim() !== prev;
			}""",
			arg=previous.strip(),
			timeout=90_000,
		)
		self._page.locator(CALENDAR_TABLE).wait_for(state="visible", timeout=60_000)

	def expand_all_event_details(self):
		"""Open details: tr.calendar__details row appears"""

		row_loc = self._page.locator("tr.calendar__row[data-event-id]")
		ids = []

		for i in range(row_loc.count()):
			event_id = row_loc.nth(i).get_attribute("data-event-id")
			if event_id:
				ids.append(event_id)

		for event_id in ids:
			row = self._page.locator(f'tr.calendar__row[data-event-id="{event_id}"]')
			link = row.locator(DETAIL_LINK)

			if link.count() == 0:
				continue

			link.first.scroll_into_view_if_needed()
			link.first.click(timeout=20000)
			self._page.wait_for_timeout(100)
			
		self._page.wait_for_timeout(500)

	def go_to_next_calendar_page(self):
		cal = self._page.locator(CALENDAR_BLOCK).first
		nxt = cal.locator("a.calendar__pagination--prev")

		before = self.get_current_options_label()
		nxt.first.scroll_into_view_if_needed()
		nxt.first.click()
		self.wait_for_calendar_table_refresh(before)

		return True
