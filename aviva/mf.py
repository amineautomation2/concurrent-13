import time
import random
from cloakbrowser import launch
from utils import get_proxy_endpoint
import logging
# Configure log format to include time
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_kiid_urls_per_worker(id_worker: int, funds: list[dict]) -> list[dict]:

    # ----------------------------------------------------
    # PRE-FLIGHT INITIAL PROXY HEALTH GATE
    # ----------------------------------------------------
    proxy_dict = get_proxy_endpoint()
    proxy_ip = proxy_dict["ip"]
    assigned_proxy = proxy_dict["proxy"]

    # Initialize residential tunnel
    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()
    session_start_time = time.time()

    cookie_accepted = False

    # Explicit pointer management to handle mid-loop faults without losing track of funds
    fund_index = 0
    while fund_index < len(funds):
        fund = funds[fund_index]
        logging.info(
            f"🕵️ [Worker {id_worker}] Processing Fund Record [{fund_index + 1}/{len(funds)}]")
        url = fund["url"]

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        # Measure continuous time drift relative to initial context birth (10 min safety cap)
        time_elapsed = time.time() - session_start_time > (5 * 60)
        if time_elapsed:
            logging.warning(
                f"⚠️ [{proxy_ip}] proxy reached max session time, generating fresh endpoint.")
            try:
                page.close()
                browser.close()
            except:
                pass
            proxy_dict = get_proxy_endpoint()
            assigned_proxy = proxy_dict["proxy"]
            browser = launch(
                headless=True, proxy=assigned_proxy, geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            time.sleep(random.uniform(2.0, 4.0))
            page.goto(url, wait_until="commit", timeout=90 * 1000)

            # Human Interaction: Trigger smooth cursor landing
            page.mouse.move(random.randint(150, 600), random.randint(150, 600))
            time.sleep(random.uniform(1, 1.2))

            # Human Interaction: Variable scrolling behavior to satisfy Akamai trackers
            for _ in range(random.randint(1, 2)):
                scroll_delta = random.randint(300, 500)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(1.0, 1.5))

            # --- HANDLE ONE-TRUST COOKIE BANNER ---
            if not cookie_accepted:
                cookie_button = page.locator("#onetrust-accept-btn-handler")
                if cookie_button.is_visible():
                    logging.info(
                        f"🍪 [Worker {id_worker}] OneTrust banner found. Clicking...")
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(1, 2.5))

            # ----------------------------------------------------
            # SECURE EXTRACTION
            # ----------------------------------------------------
            kiid_locator = page.locator("a[title='Link to KIID']")

            if kiid_locator.count() > 0:
                # Use evaluate to guarantee capturing the fully qualified absolute URL property
                kiid_url = kiid_locator.evaluate("el => el.href")
                fund.update(kiid=kiid_url)
                print(
                    f"✅ [Worker {id_worker}] Target extracted successfully: {kiid_url[-30:]}")
            else:
                fund.update(kiid=None)
                logging.warning(
                    f"⚠️ [Worker {id_worker}] No matching KIID link element present on layout.")

            fund_index += 1

        except Exception as e:
            logging.exception(
                f"❌ [Worker {id_worker}] Pipeline navigation / extraction failure: {e}")
            try:
                page.close()
            except:
                pass
            page = browser.new_page()
        # TEST
        # break

    # ----------------------------------------------------
    # CLEAN RUNTIME TEARDOWN
    # ----------------------------------------------------
    try:
        page.close()
        browser.close()
    except:
        pass

    print(f"🏁 [Worker {id_worker}] Task processing batch complete.")
    return funds
