"""Playwright browser launch and context with a realistic client fingerprint."""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Browser, BrowserContext, Playwright

# https://grep.app/search WAS USED
# STACKOVERFLOW WAS USED
# PW DOCS WERE USED


DEFAULT_USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
	"AppleWebKit/537.36 (KHTML, like Gecko) "
	"Chrome/131.0.0.0 Safari/537.36"
)
# from https://useragents.io/random?limit=10
DEFAULT_LOCALE = "en-US"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}


def launch_browser(playwright):
	launch_kwargs = {
		"headless": False,
		"args": [
			"--disable-blink-features=AutomationControlled",
		],
	}
	# from https://stackoverflow.com/questions/76789600/is-disable-blink-features-automationcontrolled-supposed-to-set-navigator-web
	return playwright.chromium.launch(channel="chrome", **launch_kwargs)

# https://playwright.dev/python/docs/emulation
def new_context(browser):
	return browser.new_context(
		user_agent=DEFAULT_USER_AGENT,
		locale=DEFAULT_LOCALE,
		timezone_id=DEFAULT_TIMEZONE,
		viewport=DEFAULT_VIEWPORT,
		java_script_enabled=True,
		has_touch=False,
		is_mobile=False,
		extra_http_headers={
			"Accept-Language": "en-US,en;q=0.9",
		},
	)
