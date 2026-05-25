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


def _block_assets(p):
    """Abort CSS, font and other non-essential requests to save bandwidth."""
    p.route(
        "**/*",
        lambda route: route.abort()
        if route.request.resource_type in {"stylesheet", "font", "image", "media"}
        else route.continue_()
    )


def get_kiid_urls_per_worker_backup(id_worker: int, funds: list[dict]) -> list[dict]:

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


def get_kiid_urls_per_worker(id_worker: int, funds: list[dict]) -> list[dict]:
    # ----------------------------------------------------
    # PRE-FLIGHT INITIAL PROXY HEALTH GATE
    # ----------------------------------------------------
    proxy_dict = get_proxy_endpoint()
    proxy_ip = proxy_dict["ip"]
    assigned_proxy = proxy_dict["proxy"]

    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()
    _block_assets(page)
    session_start_time = time.time()

    cookie_accepted = False

    # ----------------------------------------------------
    # POINTER & RETRY STATE
    # ----------------------------------------------------
    fund_index = 0
    MAX_TIMEOUT_PER_PROXY_MIN = 10 * 60

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

    # Guard: reading pause can fire at most once every N successful pages
    MIN_PAGES_BETWEEN_READING_PAUSE = 3
    # allow on first eligible page
    pages_since_last_reading_pause = MIN_PAGES_BETWEEN_READING_PAUSE

    while fund_index < len(funds):
        id_page = funds[fund_index]
        fund = funds[fund_index]
        url = fund["url"]
        print(
            f"🕵️ Aviva Processing Page [{id_page}/{len(funds)}] "
            f"| Attempt {retry_count + 1}/{MAX_RETRIES_PER_PAGE}"
        )

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
            _block_assets(page)
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
        # 15% chance of a longer "distracted user" reading pause,
        # but gated so it cannot fire on consecutive pages
        # ----------------------------------------------------
        reading_pause_eligible = pages_since_last_reading_pause >= MIN_PAGES_BETWEEN_READING_PAUSE
        if reading_pause_eligible and random.random() < 0.15:
            reading_pause = random.uniform(5.0, 10.0)
            logging.info(f"📖 Simulating reading pause: {reading_pause:.1f}s")
            time.sleep(reading_pause)
            pages_since_last_reading_pause = 0  # reset gate
        else:
            time.sleep(random.uniform(2.0, 3.5))
            pages_since_last_reading_pause += 1

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            page.goto(url, wait_until="commit", timeout=120 * 1000)

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

            # ✅ SUCCESS: Advance pointer and reset all retry/pacing state
            fund_index += 1
            retry_count = 0
            proxy_rotation_count = 0
            page_count_since_break += 1  # Only count successful page loads

            logging.info(
                f"✅ Page {id_page} scraped successfully — "
                f"progress {fund_index}/{len(funds)} | "
            )

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
                    fund_index += 1
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
                        fund_index += 1
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
                    fund_index += 1
                    retry_count = 0
                    proxy_rotation_count = 0
                    PAGES_BEFORE_COOLDOWN = random.randint(7, 11)

            page = browser.new_page()
            _block_assets(page)

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
