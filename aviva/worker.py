import time
from cloakbrowser import launch
import random
from utils import get_proxy_endpoint, isin_from_text
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def aviva_pagination_per_worker_backup(base_url: str, total_per_w: list[int]) -> list[dict]:
    # ----------------------------------------------------
    # PRE-FLIGHT INITIAL PROXY HEALTH GATE
    # ----------------------------------------------------
    proxy_dict = get_proxy_endpoint()
    proxy_ip = proxy_dict["ip"]
    proxy_ip = proxy_dict["proxy"]

    browser = launch(headless=True, proxy=proxy_ip,
                     geoip=True, humanize=True)
    page = browser.new_page()
    session_start_time = time.time()

    cookie_accepted = False
    funds = []

    # Explicit pointer management to control retries without dropping data
    page_index = 0
    MAX_TIMEOUT_PER_PROXY_MIN = 7 * 60

    while page_index < len(total_per_w):
        id_page = total_per_w[page_index]
        print(
            f"🕵️ Aviva Processing Page [{id_page}/{len(total_per_w)}]")
        target_url = f"{base_url}?page={id_page}"

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        time_elapsed = time.time() - session_start_time > MAX_TIMEOUT_PER_PROXY_MIN
        if time_elapsed:
            logging.warning(
                f"⚠️ [{proxy_ip}] proxy reached max session time, refreshing proxy...")
            try:
                page.close()
                browser.close()
            except:
                pass
            proxy_dict = get_proxy_endpoint()
            proxy_ip = proxy_dict["proxy"]
            browser = launch(
                headless=True, proxy=proxy_ip, geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            time.sleep(random.uniform(2.0, 4.0))
            page.goto(target_url, wait_until="commit", timeout=90 * 1000)

            # Human Interaction: Target viewport random positioning coordinates
            page.mouse.move(random.randint(200, 700), random.randint(200, 600))
            time.sleep(random.uniform(0.5, 1.2))

            # Human Interaction: Organic scroll steps to pass Akamai telemetry
            for _ in range(random.randint(1, 2)):
                scroll_delta = random.randint(280, 480)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(1.0, 1.5))

            # --- HANDLE ONE-TRUST COOKIE BANNER ---
            if not cookie_accepted:
                cookie_button = page.locator("#onetrust-accept-btn-handler")
                if cookie_button.is_visible():
                    print("🍪 OneTrust banner visible. Executing humanized click...")
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(0.5, 1.5))

            # ----------------------------------------------------
            # SECURE PLAYWRIGHT DATA EXTRACTION
            # ----------------------------------------------------
            row_locators = page.locator(
                "#paginatedResults > fieldset > div").all()
            print(f"📊 Found {len(row_locators)} fund rows on page {id_page}.")

            for row in row_locators:
                f = {}
                try:
                    name = row.locator(
                        "div:nth-child(2) > label > span > span").text_content().strip()
                    anchor = row.locator("div:nth-child(2) > div > div > a")

                    raw_url = anchor.get_attribute("href")
                    if raw_url:
                        absolute_url = anchor.evaluate("el => el.href")
                        isin = isin_from_text(absolute_url)

                        f.update(name=name, url=absolute_url, isin=isin)
                        funds.append(f)

                except Exception as row_error:
                    print(f"⚠️ Skipping row element: {row_error}")
                    continue

            # ✅ SUCCESS: Advance the index pointer to the next target link
            page_index += 1

        except Exception as page_error:
            logging.critical(
                f"❌ Failed processing page {id_page}: {page_error}")
            try:
                page.close()
            except:
                pass
            time.sleep(10)
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

    print(
        f"🏁 Worker execution batch complete. Collected {len(funds)} entries.")
    return funds


def aviva_pagination_per_worker(base_url: str, total_per_w: list[int]) -> list[dict]:
    # ----------------------------------------------------
    # PRE-FLIGHT INITIAL PROXY HEALTH GATE
    # ----------------------------------------------------
    proxy_dict = get_proxy_endpoint()
    proxy_ip = proxy_dict["ip"]
    assigned_proxy = proxy_dict["proxy"]

    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()
    session_start_time = time.time()

    cookie_accepted = False
    funds = []

    page_index = 0
    MAX_TIMEOUT_PER_PROXY_MIN = 7 * 60

    # --- NEW: Retry state ---
    MAX_RETRIES_PER_PAGE = 3
    MAX_PROXY_ROTATIONS = 2          # Hard cap on proxy swaps per page
    retry_count = 0
    proxy_rotation_count = 0

    while page_index < len(total_per_w):
        id_page = total_per_w[page_index]
        print(
            f"🕵️ Aviva Processing Page [{id_page}/{len(total_per_w)}] | Attempt {retry_count + 1}/{MAX_RETRIES_PER_PAGE}")
        target_url = f"{base_url}?page={id_page}"

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        time_elapsed = time.time() - session_start_time > MAX_TIMEOUT_PER_PROXY_MIN
        if time_elapsed:
            logging.warning(
                f"⚠️ [{proxy_ip}] proxy reached max session time, refreshing proxy...")
            try:
                page.close()
                browser.close()
            except:
                pass
            proxy_dict = get_proxy_endpoint()
            # 🔧 FIX: was never updated on session refresh
            proxy_ip = proxy_dict["ip"]
            assigned_proxy = proxy_dict["proxy"]
            browser = launch(headless=True, proxy=assigned_proxy,
                             geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            time.sleep(random.uniform(2.0, 4.0))
            page.goto(target_url, wait_until="commit", timeout=90 * 1000)

            page.mouse.move(random.randint(200, 700), random.randint(200, 600))
            time.sleep(random.uniform(0.5, 1.2))

            for _ in range(random.randint(1, 2)):
                scroll_delta = random.randint(280, 480)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(1.0, 1.5))

            if not cookie_accepted:
                cookie_button = page.locator("#onetrust-accept-btn-handler")
                if cookie_button.is_visible():
                    print("🍪 OneTrust banner visible. Executing humanized click...")
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(0.5, 1.5))

            # ----------------------------------------------------
            # SECURE PLAYWRIGHT DATA EXTRACTION
            # ----------------------------------------------------
            row_locators = page.locator(
                "#paginatedResults > fieldset > div").all()
            print(f"📊 Found {len(row_locators)} fund rows on page {id_page}.")

            for row in row_locators:
                f = {}
                try:
                    name = row.locator(
                        "div:nth-child(2) > label > span > span").text_content().strip()
                    anchor = row.locator("div:nth-child(2) > div > div > a")
                    raw_url = anchor.get_attribute("href")
                    if raw_url:
                        absolute_url = anchor.evaluate("el => el.href")
                        isin = isin_from_text(absolute_url)
                        f.update(name=name, url=absolute_url, isin=isin)
                        funds.append(f)
                except Exception as row_error:
                    print(f"⚠️ Skipping row element: {row_error}")
                    continue

            # ✅ SUCCESS: Advance pointer and reset retry state
            page_index += 1
            retry_count = 0
            proxy_rotation_count = 0

        except Exception as page_error:
            logging.critical(
                f"❌ Failed processing page {id_page} (attempt {retry_count + 1}): {page_error}")
            retry_count += 1

            try:
                page.close()
            except:
                pass

            # --- GRADUATED BACKOFF ---
            backoff = min(10 * retry_count, 60)  # 10s → 20s → 60s cap
            logging.info(f"⏳ Backing off {backoff}s before retry...")
            time.sleep(backoff)

            if retry_count >= MAX_RETRIES_PER_PAGE:
                if proxy_rotation_count < MAX_PROXY_ROTATIONS:
                    # --- FORCE PROXY ROTATION ON REPEATED FAILURE ---
                    logging.warning(
                        f"🔄 Page {id_page} failed {retry_count}x. Rotating proxy ({proxy_rotation_count + 1}/{MAX_PROXY_ROTATIONS})...")
                    try:
                        browser.close()
                    except:
                        pass
                    proxy_dict = get_proxy_endpoint()
                    proxy_ip = proxy_dict["ip"]
                    assigned_proxy = proxy_dict["proxy"]
                    browser = launch(
                        headless=True, proxy=assigned_proxy, geoip=True, humanize=True)
                    session_start_time = time.time()
                    cookie_accepted = False
                    retry_count = 0
                    proxy_rotation_count += 1
                else:
                    # --- HARD SKIP: page is unrecoverable ---
                    logging.error(
                        f"🚫 Page {id_page} unrecoverable after {MAX_PROXY_ROTATIONS} proxy rotations. Skipping.")
                    page_index += 1
                    retry_count = 0
                    proxy_rotation_count = 0

            page = browser.new_page()

    # ----------------------------------------------------
    # CLEAN RUNTIME TEARDOWN
    # ----------------------------------------------------
    try:
        page.close()
        browser.close()
    except:
        pass

    print(
        f"🏁 Worker execution batch complete. Collected {len(funds)} entries.")
    return funds
