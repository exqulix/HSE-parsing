from bs4 import BeautifulSoup

# USED https://www.crummy.com/software/BeautifulSoup/bs4/doc/ для справки

def _norm_cell(td):
	if not td:
		return ""
	return " ".join(td.stripped_strings)


def _find_td(tr, class_substr):
	return tr.find("td", class_=lambda c: c and class_substr in c) 


def _parse_details_tr(tr):
	td = tr.find("td")

	if not td:
		return {}

	shell = td.select_one(".shell.nest") or td
	specs = []
	for table in shell.select("table.calendarspecs"):
		for row in table.find_all("tr"):
			cells = row.find_all("td")
			if len(cells) >= 2:
				specs.append(
					{
						"label": _norm_cell(cells[0]),
						"value": _norm_cell(cells[1]),
					}
				)

	history = []

	hist = shell.select_one("table.calendarhistory")

	if hist:
		for row in hist.find_all("tr"):
			row_cls = " ".join(row.get("class") or []) 

			if "calendarhistory__header" in row_cls:
				continue

			cells = row.find_all("td")
			if len(cells) >= 4:
				history.append(
					{
						"date": _norm_cell(cells[0]),
						"actual": _norm_cell(cells[1]),
						"forecast": _norm_cell(cells[2]),
						"previous": _norm_cell(cells[3]),
					}
				)

	related = shell.select_one("ul.body.flexposts, div.relatedstories")
	related_text = related.get_text("\n", strip=True) if related else ""

	return {
		"specs": specs,
		"history": history,
		"related_stories_text": related_text,
	}


def _parse_impact_field(impact_td):
	if not impact_td:
		return ""
	span = impact_td.find("span", title=True)
	title = (span.get("title") or "").strip() if span else ""
	return title


def _parse_currency_field(cur_td):
	if not cur_td:
		return "", ""
	abbr = cur_td.find("abbr")
	if not abbr:
		return _norm_cell(cur_td), ""
	return abbr.get_text(strip=True), (abbr.get("title") or "").strip()


def _parse_event_title(ev_td):
	if not ev_td:
		return ""
	el = ev_td.select_one(".calendar__event-title")
	return el.get_text(strip=True) if el else _norm_cell(ev_td)


def _pick_calendar_table(soup):
	tables = soup.select("table.calendar__table")
	if not tables:
		return None
	return max(tables, key=lambda t: len(t.select("tr[data-event-id]")))


def _iter_main_calendar_rows(table):
	tbodies = table.find_all("tbody", recursive=False)
	if tbodies:
		for main_tbody in tbodies:
			for tr in main_tbody.find_all("tr"):
				if tr.find_parent("tbody") is not main_tbody:
					continue
				yield tr
		return
	#used https://www.geeksforgeeks.org/python/python-yield-keyword/


class ForexFactoryParser:
	def parse_calendar_page(self, html):
		
		soup = BeautifulSoup(html, "html.parser")
		table = _pick_calendar_table(soup)
		if not table:
			return []

		rows_out = []

		last_day = ""

		for tr in _iter_main_calendar_rows(table):
			# iter through days AND events
			classes = tr.get("class") or []

			# html uses 2 ways to show date so we support both
			if "calendar__row--day-breaker" in classes:
				cell = tr.find("td")
				if cell:
					last_day = cell.get_text(" ", strip=True)
				continue

			if "calendar__details" in classes:
				if rows_out:
					rows_out[-1]["detail"] = _parse_details_tr(tr)
				continue

			eid = tr.get("data-event-id")
			if not eid:
				continue

			# html uses 2 ways to show date so we support both
			date_td = _find_td(tr, "calendar__date")
			if date_td:
				d = date_td.get_text(" ", strip=True)
				if d:
					last_day = d

			time_td = _find_td(tr, "calendar__time")
			cur_td = _find_td(tr, "calendar__currency")
			impact_td = _find_td(tr, "calendar__impact")
			event_td = _find_td(tr, "calendar__event")
			actual_td = _find_td(tr, "calendar__actual")
			forecast_td = _find_td(tr, "calendar__forecast")
			prev_td = _find_td(tr, "calendar__previous")

			impact_title = _parse_impact_field(impact_td)
			currency, currency_full = _parse_currency_field(cur_td)

			rows_out.append(
				{
					"event_id": eid,
					"day": last_day,
					"time": _norm_cell(time_td),
					"currency": currency,
					"currency_full": currency_full,
					"impact_title": impact_title,
					"title": _parse_event_title(event_td),
					"actual": _norm_cell(actual_td),
					"forecast": _norm_cell(forecast_td),
					"previous": _norm_cell(prev_td),
					"detail": None,
				}
			)

		return rows_out
