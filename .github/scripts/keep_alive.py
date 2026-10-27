"""Open the Streamlit app in a real browser so it counts as a visit,
and click the wake-up button if the app has already gone to sleep."""

import sys

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

APP_URL = "https://app-12345.streamlit.app/"

with sync_playwright() as p:
  browser = p.chromium.launch()
  page = browser.new_page()
  page.goto(APP_URL, wait_until="domcontentloaded", timeout=60_000)

  # Sleeping apps show "Yes, get this app back up!" instead of the app
  wake_button = page.get_by_role("button", name="Yes, get this app back up")
  try:
    wake_button.wait_for(timeout=15_000)
    print("App was asleep, clicking wake-up button...")
    wake_button.click()
  except PlaywrightTimeoutError:
    print("App is awake.")

  # The app itself runs inside an iframe on *.streamlit.app; wait for it to render
  try:
    page.frame_locator('iframe[title="streamlitApp"]').get_by_text(
        "Akhil's Professional Assistant Bot"
    ).first.wait_for(timeout=180_000)
    print("App loaded successfully.")
  except PlaywrightTimeoutError:
    page.screenshot(path="keep_alive_failure.png", full_page=True)
    print("App did not load in time.")
    browser.close()
    sys.exit(1)

  # Stay connected briefly so the session registers as real activity
  page.wait_for_timeout(10_000)
  browser.close()
