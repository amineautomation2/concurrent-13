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
            time.sleep(random.uniform(2.0, 3.0))
            page.goto(target_url, wait_until="commit", timeout=120 * 1000)

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


def aviva_pagination_per_worker_2nd(base_url: str, total_per_w: list[int]) -> list[dict]:
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
            time.sleep(random.uniform(2.0, 3.0))
            page.goto(target_url, wait_until="commit", timeout=120 * 1000)

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


def aviva_pagination_per_worker_except(base_url: str, total_per_w: list[int]) -> list[dict]:
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

    # ----------------------------------------------------
    # POINTER & RETRY STATE
    # ----------------------------------------------------
    page_index = 0
    MAX_TIMEOUT_PER_PROXY_MIN = 7 * 60

    MAX_RETRIES_PER_PAGE = 3
    MAX_PROXY_ROTATIONS = 2
    retry_count = 0
    proxy_rotation_count = 0

    # ----------------------------------------------------
    # AKAMAI CADENCE BREAKER STATE
    # ----------------------------------------------------
    page_count_since_break = 0
    PAGES_BEFORE_COOLDOWN = random.randint(7, 11)
    COOLDOWN_DURATION = (25, 45)

    while page_index < len(total_per_w):
        id_page = total_per_w[page_index]
        print(
            f"🕵️ Aviva Processing Page [{id_page}/{len(total_per_w)}] "
            f"| Attempt {retry_count + 1}/{MAX_RETRIES_PER_PAGE}"
        )
        target_url = f"{base_url}?page={id_page}"

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        time_elapsed = time.time() - session_start_time > MAX_TIMEOUT_PER_PROXY_MIN
        if time_elapsed:
            logging.warning(
                f"⚠️ [{proxy_ip}] proxy reached max session time, refreshing proxy..."
            )
            try:
                page.close()
                browser.close()
            except Exception:
                pass

            proxy_dict = get_proxy_endpoint()
            proxy_ip = proxy_dict["ip"]
            assigned_proxy = proxy_dict["proxy"]
            browser = launch(headless=True, proxy=assigned_proxy,
                             geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False

        # ----------------------------------------------------
        # PROACTIVE AKAMAI CADENCE BREAKER
        # Fires BEFORE the request, not after a failure
        # ----------------------------------------------------
        if page_count_since_break >= PAGES_BEFORE_COOLDOWN:
            cooldown = random.uniform(*COOLDOWN_DURATION)
            logging.info(
                f"🧘 Cadence break after {page_count_since_break} pages "
                f"— cooling down {cooldown:.1f}s..."
            )
            # Idle: scroll to top
            page.evaluate("window.scrollBy(0, -window.scrollY)")
            time.sleep(cooldown)
            page_count_since_break = 0
            PAGES_BEFORE_COOLDOWN = random.randint(
                7, 11)  # Re-randomize next window

        # ----------------------------------------------------
        # VARIABLE INTER-PAGE DELAY
        # 15% chance of a longer "distracted user" reading pause
        # ----------------------------------------------------
        if random.random() < 0.15:
            reading_pause = random.uniform(6.0, 12.0)
            logging.info(f"📖 Simulating reading pause: {reading_pause:.1f}s")
            time.sleep(reading_pause)
        else:
            time.sleep(random.uniform(2.5, 5.5))

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
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
                        "div:nth-child(2) > label > span > span"
                    ).text_content().strip()
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

            # ✅ SUCCESS: Advance pointer and reset all retry/pacing state
            page_index += 1
            retry_count = 0
            proxy_rotation_count = 0
            page_count_since_break += 1  # Only count successful page loads

        # ----------------------------------------------------
        # FAILURE HANDLING: GRADUATED BACKOFF + PROXY ROTATION
        # ----------------------------------------------------
        except Exception as page_error:
            logging.critical(
                f"❌ Failed processing page {id_page} "
                f"(attempt {retry_count + 1}): {page_error}"
            )
            retry_count += 1

            try:
                page.close()
            except Exception:
                pass

            # Longer forced cooldown on timeout — gives Akamai time to lift slow-lane flag
            forced_cooldown = random.uniform(30.0, 50.0)
            logging.info(
                f"🔥 Timeout detected — forced cooldown {forced_cooldown:.1f}s "
                f"to reset Akamai scoring..."
            )
            time.sleep(forced_cooldown)

            # Reset cadence window after penalty; be more conservative next round
            page_count_since_break = 0
            PAGES_BEFORE_COOLDOWN = random.randint(5, 8)

            if retry_count >= MAX_RETRIES_PER_PAGE:
                if proxy_rotation_count < MAX_PROXY_ROTATIONS:
                    # --- FORCE PROXY ROTATION ON REPEATED FAILURE ---
                    logging.warning(
                        f"🔄 Page {id_page} failed {retry_count}x. "
                        f"Rotating proxy ({proxy_rotation_count + 1}/{MAX_PROXY_ROTATIONS})..."
                    )
                    try:
                        browser.close()
                    except Exception:
                        pass

                    proxy_dict = get_proxy_endpoint()
                    proxy_ip = proxy_dict["ip"]
                    assigned_proxy = proxy_dict["proxy"]
                    browser = launch(
                        headless=True, proxy=assigned_proxy, geoip=True, humanize=True
                    )
                    session_start_time = time.time()
                    cookie_accepted = False
                    retry_count = 0
                    proxy_rotation_count += 1

                else:
                    # --- HARD SKIP: page is unrecoverable ---
                    logging.error(
                        f"🚫 Page {id_page} unrecoverable after "
                        f"{MAX_PROXY_ROTATIONS} proxy rotations. Skipping."
                    )
                    page_index += 1
                    retry_count = 0
                    proxy_rotation_count = 0
                    PAGES_BEFORE_COOLDOWN = random.randint(
                        7, 11)  # Reset to normal window

            page = browser.new_page()

    # ----------------------------------------------------
    # CLEAN RUNTIME TEARDOWN
    # ----------------------------------------------------
    try:
        page.close()
        browser.close()
    except Exception:
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

    # ----------------------------------------------------
    # POINTER & RETRY STATE
    # ----------------------------------------------------
    page_index = 0
    MAX_TIMEOUT_PER_PROXY_MIN = 7 * 60

    MAX_RETRIES_PER_PAGE = 3
    MAX_PROXY_ROTATIONS = 2
    retry_count = 0
    proxy_rotation_count = 0

    # ----------------------------------------------------
    # AKAMAI CADENCE BREAKER STATE
    # ----------------------------------------------------
    page_count_since_break = 0
    PAGES_BEFORE_COOLDOWN = random.randint(7, 11)
    COOLDOWN_DURATION = (25, 45)

    while page_index < len(total_per_w):
        id_page = total_per_w[page_index]
        print(
            f"🕵️ Aviva Processing Page [{id_page}/{len(total_per_w)}] "
            f"| Attempt {retry_count + 1}/{MAX_RETRIES_PER_PAGE}"
        )
        target_url = f"{base_url}?page={id_page}"

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        time_elapsed = time.time() - session_start_time > MAX_TIMEOUT_PER_PROXY_MIN
        if time_elapsed:
            logging.warning(
                f"⚠️ [{proxy_ip}] proxy reached max session time, refreshing proxy..."
            )
            try:
                page.close()
                browser.close()
            except Exception:
                pass

            proxy_dict = get_proxy_endpoint()
            proxy_ip = proxy_dict["ip"]
            assigned_proxy = proxy_dict["proxy"]
            browser = launch(headless=True, proxy=assigned_proxy,
                             geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False

        # ----------------------------------------------------
        # PROACTIVE AKAMAI CADENCE BREAKER
        # Fires BEFORE the request, not after a failure
        # ----------------------------------------------------
        if page_count_since_break >= PAGES_BEFORE_COOLDOWN:
            cooldown = random.uniform(*COOLDOWN_DURATION)
            logging.info(
                f"🧘 Cadence break after {page_count_since_break} pages "
                f"— cooling down {cooldown:.1f}s..."
            )
            # Idle: scroll to top
            page.evaluate("window.scrollBy(0, -window.scrollY)")
            time.sleep(cooldown)
            page_count_since_break = 0
            PAGES_BEFORE_COOLDOWN = random.randint(
                7, 11)  # Re-randomize next window

        # ----------------------------------------------------
        # VARIABLE INTER-PAGE DELAY
        # 15% chance of a longer "distracted user" reading pause
        # ----------------------------------------------------
        if random.random() < 0.15:
            reading_pause = random.uniform(6.0, 12.0)
            logging.info(f"📖 Simulating reading pause: {reading_pause:.1f}s")
            time.sleep(reading_pause)
        else:
            time.sleep(random.uniform(2.0, 3.5))

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            page.goto(target_url, wait_until="commit", timeout=120 * 1000)

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
                        "div:nth-child(2) > label > span > span"
                    ).text_content().strip()
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

            # ✅ SUCCESS: Advance pointer and reset all retry/pacing state
            page_index += 1
            retry_count = 0
            proxy_rotation_count = 0
            page_count_since_break += 1  # Only count successful page loads

        # ----------------------------------------------------
        # FAILURE HANDLING: ERROR-TYPE AWARE + GRADUATED RESPONSE
        # ----------------------------------------------------
        except Exception as page_error:
            error_msg = str(page_error)

            # Classify the error type to apply the correct recovery strategy
            if "ERR_CONNECTION_CLOSED" in error_msg or "ERR_CONNECTION_RESET" in error_msg:
                error_type = "connection_closed"   # Akamai hard block — TCP level rejection
            elif "Timeout" in error_msg:
                error_type = "timeout"             # Akamai slow-lane — request hangs
            elif "net::" in error_msg:
                error_type = "network"             # Generic network error
            else:
                error_type = "unknown"

            retry_count += 1
            logging.critical(
                f"❌ [{error_type.upper()}] Failed page {id_page} "
                f"(attempt {retry_count}/{MAX_RETRIES_PER_PAGE}): {page_error}"
            )

            try:
                page.close()
            except Exception:
                pass

            # Reset cadence window after any failure; be conservative next round
            page_count_since_break = 0
            PAGES_BEFORE_COOLDOWN = random.randint(5, 8)

            # ----------------------------------------------------------------
            # CONNECTION_CLOSED: Hard TCP block — rotate proxy immediately,
            # cooldown alone won't recover this
            # ----------------------------------------------------------------
            if error_type == "connection_closed":
                logging.warning(
                    f"🚨 TCP connection closed by server on page {id_page}. "
                    f"Forcing immediate proxy rotation..."
                )
                try:
                    browser.close()
                except Exception:
                    pass

                proxy_dict = get_proxy_endpoint()
                proxy_ip = proxy_dict["ip"]
                assigned_proxy = proxy_dict["proxy"]
                browser = launch(
                    headless=True, proxy=assigned_proxy, geoip=True, humanize=True
                )
                session_start_time = time.time()
                cookie_accepted = False
                proxy_rotation_count += 1

                # Short settle pause — new IP needs a clean start
                time.sleep(random.uniform(5.0, 10.0))

                # If proxy budget exhausted, hard skip this page
                if proxy_rotation_count > MAX_PROXY_ROTATIONS:
                    logging.error(
                        f"🚫 Page {id_page} unrecoverable — "
                        f"TCP blocked across {proxy_rotation_count} proxies. Skipping."
                    )
                    page_index += 1
                    retry_count = 0
                    proxy_rotation_count = 0
                    PAGES_BEFORE_COOLDOWN = random.randint(7, 11)

            # ----------------------------------------------------------------
            # TIMEOUT: Akamai slow-lane — force cooldown to reset session score,
            # escalate to proxy rotation only after MAX_RETRIES exhausted
            # ----------------------------------------------------------------
            elif error_type == "timeout":
                forced_cooldown = random.uniform(30.0, 50.0)
                logging.info(
                    f"🔥 Timeout — forced cooldown {forced_cooldown:.1f}s "
                    f"to reset Akamai scoring..."
                )
                time.sleep(forced_cooldown)

                if retry_count >= MAX_RETRIES_PER_PAGE:
                    if proxy_rotation_count < MAX_PROXY_ROTATIONS:
                        logging.warning(
                            f"🔄 Page {id_page} timed out {retry_count}x. "
                            f"Rotating proxy ({proxy_rotation_count + 1}/{MAX_PROXY_ROTATIONS})..."
                        )
                        try:
                            browser.close()
                        except Exception:
                            pass

                        proxy_dict = get_proxy_endpoint()
                        proxy_ip = proxy_dict["ip"]
                        assigned_proxy = proxy_dict["proxy"]
                        browser = launch(
                            headless=True, proxy=assigned_proxy, geoip=True, humanize=True
                        )
                        session_start_time = time.time()
                        cookie_accepted = False
                        retry_count = 0
                        proxy_rotation_count += 1
                    else:
                        logging.error(
                            f"🚫 Page {id_page} unrecoverable after "
                            f"{MAX_PROXY_ROTATIONS} proxy rotations. Skipping."
                        )
                        page_index += 1
                        retry_count = 0
                        proxy_rotation_count = 0
                        PAGES_BEFORE_COOLDOWN = random.randint(7, 11)

            # ----------------------------------------------------------------
            # NETWORK / UNKNOWN: Standard graduated backoff, skip after MAX_RETRIES
            # ----------------------------------------------------------------
            else:
                backoff = min(10 * retry_count, 60)
                logging.info(
                    f"⏳ [{error_type.upper()}] backing off {backoff}s before retry..."
                )
                time.sleep(backoff)

                if retry_count >= MAX_RETRIES_PER_PAGE:
                    logging.error(
                        f"🚫 Page {id_page} skipped after {retry_count} "
                        f"{error_type} errors."
                    )
                    page_index += 1
                    retry_count = 0
                    proxy_rotation_count = 0
                    PAGES_BEFORE_COOLDOWN = random.randint(7, 11)

            page = browser.new_page()

    # ----------------------------------------------------
    # CLEAN RUNTIME TEARDOWN
    # ----------------------------------------------------
    try:
        page.close()
        browser.close()
    except Exception:
        pass

    print(
        f"🏁 Worker execution batch complete. Collected {len(funds)} entries.")
    return funds
