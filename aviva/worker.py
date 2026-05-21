import time
from cloakbrowser import launch
import random
from utils import isin_from_text
from aviva.total import get_current_exit_ip


def aviva_pagination_per_worker(base_url: str, total_per_w: list[int], assigned_proxy: str) -> list[dict]:
    # ----------------------------------------------------
    # PRE-FLIGHT INITIAL PROXY HEALTH GATE
    # ----------------------------------------------------
    session_ip = None
    max_init_retries = 5

    for attempt in range(1, max_init_retries + 1):
        print(
            f"📡 Verifying proxy connection... (Attempt {attempt}/{max_init_retries})")
        session_ip = get_current_exit_ip(assigned_proxy)

        if session_ip:
            print(f"✅ Proxy verified healthy. Active IP: {session_ip}")
            break

        if attempt < max_init_retries:
            # Scale backing wait periods: 15s, 30s, 45s, 60s
            sleep_duration = attempt * 15
            print(
                f"⚠️ Proxy port dropped or timing out. Sleeping {sleep_duration}s before re-checking...")
            time.sleep(sleep_duration)

    # Fatal Fail-Safe: Terminate worker before launching an unprotected browser
    if not session_ip:
        print("❌ [Fatal] Proxy failed health validation across 5 checks. Aborting worker initialization to prevent raw IP leak.")
        return []

    # Safe to spin up CloakBrowser now that proxy integrity is verified
    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()
    session_start_time = time.time()

    cookie_accepted = False
    funds = []

    # Explicit pointer management to control retries without dropping data
    page_index = 0
    page_retry_count = 0
    max_page_retries = 3

    while page_index < len(total_per_w):
        id_page = total_per_w[page_index]
        print(
            f"🕵️ Aviva Processing Page [{id_page}] (Attempt {page_retry_count + 1}/{max_page_retries})")
        target_url = f"{base_url}?page={id_page}"

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        time_elapsed = time.time() - session_start_time > 10 * 60
        current_ip = session_ip
        if page_index > 0:
            current_ip = get_current_exit_ip(assigned_proxy)

            # Handle mid-run pipeline drops cleanly without skipping pages
            if not current_ip:
                print(f"⚠️ Proxy lost connection mid-run on page {id_page}.")
                page_retry_count += 1

                if page_retry_count >= max_page_retries:
                    print(
                        f"❌ Target page {id_page} hit the failure ceiling. Closing context and sleeping 60s for auto-rotation...")
                    try:
                        page.close()
                        browser.close()
                    except:
                        pass

                    time.sleep(60)

                    # Attempt to completely resurrect the browser layer
                    session_ip = get_current_exit_ip(assigned_proxy)
                    if session_ip:
                        browser = launch(
                            headless=True, proxy=assigned_proxy, geoip=True, humanize=True)
                        page = browser.new_page()
                        session_start_time = time.time()
                        cookie_accepted = False

                    page_retry_count = 0
                    page_index += 1  # Intentionally drop the broken link to avoid endless thread lockup
                else:
                    time.sleep(15)
                continue

        # Handle normal expected session expiration or dynamic IP switch
        if time_elapsed or (current_ip != session_ip):
            reason = "Session time limit reached" if time_elapsed else f"Proxy IP changed ({session_ip} -> {current_ip})"
            print(f"🔄 Re-housing browser footprint. Reason: {reason}")
            try:
                page.close()
                browser.close()
            except:
                pass

            session_ip = current_ip
            browser = launch(headless=True, proxy=assigned_proxy,
                             geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            time.sleep(random.uniform(4.0, 7.0))
            page.goto(target_url, wait_until="commit", timeout=45000)

            # Human Interaction: Target viewport random positioning coordinates
            page.mouse.move(random.randint(200, 700), random.randint(200, 600))
            time.sleep(random.uniform(0.5, 1.2))

            # Human Interaction: Organic scroll steps to pass Akamai telemetry
            for _ in range(random.randint(2, 3)):
                scroll_delta = random.randint(280, 480)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(1.0, 2.5))

            # --- HANDLE ONE-TRUST COOKIE BANNER ---
            if not cookie_accepted:
                cookie_button = page.locator("#onetrust-accept-btn-handler")
                if cookie_button.is_visible():
                    print("🍪 OneTrust banner visible. Executing humanized click...")
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(1.5, 2.5))

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
            page_retry_count = 0

        except Exception as page_error:
            print(f"❌ Failed processing page {id_page}: {page_error}")
            page_retry_count += 1

            try:
                page.close()
            except:
                pass
            page = browser.new_page()

            if page_retry_count >= max_page_retries:
                print(
                    f"❌ Failed navigation max limits on page {id_page}. Moving forward.")
                page_index += 1
                page_retry_count = 0
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


def aviva_pagination_per_worker_backup(base_url: str, total_per_w: list[int], assigned_proxy: str) -> list[dict]:
    # 1. Fetch initial IP and launch browser engine with automated context sync profiles
    # Handle a dead connection or early IP shift dynamically
    # If the proxy is completely dead or rotated early, sleep for 5 minutes
    session_ip = None
    max_init_retries = 5

    for attempt in range(1, max_init_retries + 1):
        print(
            f"📡 Verifying proxy connection... (Attempt {attempt}/{max_init_retries})")
        session_ip = get_current_exit_ip(assigned_proxy)

        if session_ip:
            print(f"✅ Proxy verified healthy. Active IP: {session_ip}")
            break

        if attempt < max_init_retries:
            # Scale backing wait periods: 15s, 30s, 45s, 60s
            sleep_duration = attempt * 15
            print(
                f"⚠️ Proxy port dropped or timing out. Sleeping {sleep_duration}s before re-checking...")
            time.sleep(sleep_duration)
    if not session_ip:
        print("❌ [Fatal] Proxy failed health validation across 5 checks. Aborting worker initialization to prevent raw IP leak.")
        return []
    # OLD
    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()
    session_start_time = time.time()

    # Track cookie consent banner state across page loads
    cookie_accepted = False
    funds = []

    for idx, id_page in enumerate(total_per_w, start=1):
        print(
            f"🕵️ Aviva Investment Processing Page [{id_page} (Index {idx}/{len(total_per_w)})]")
        target_url = f"{base_url}?page={id_page}"

        # ----------------------------------------------------
        # PRE-FLIGHT IP ROTATION RESILIENCE CHECK
        # ----------------------------------------------------
        time_elapsed = time.time() - session_start_time > 1200  # 20 minutes limit
        current_ip = get_current_exit_ip(assigned_proxy)

        # Handle a dead connection or early IP shift dynamically
        # If the proxy is completely dead or rotated early, sleep for 5 minutes
        if not current_ip:
            print(
                "⚠️ [Worker ] Proxy port dropped connection. Retrying...")
            time.sleep(5 * 60)

        if time_elapsed or (current_ip != session_ip):
            reason = "Max session age reached" if time_elapsed else f"Proxy IP changed ({session_ip} -> {current_ip})"
            print(f"🔄 Resetting CloakBrowser engine profile. Reason: {reason}")

            page.close()
            browser.close()

            # Reset session state parameters
            session_ip = current_ip
            browser = launch(headless=True, proxy=assigned_proxy,
                             geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False  # Reset since cookie data was purged on close

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        try:
            # Humanized thinking pause before hitting the site
            time.sleep(random.uniform(3.0, 5.0))

            # Fast-return navigation to reduce server tracker exposure window
            page.goto(target_url, wait_until="commit", timeout=45000)

            # Move cursor smoothly into the reading viewport space
            page.mouse.move(random.randint(200, 700), random.randint(200, 600))
            time.sleep(random.uniform(0.5, 1.2))

            # Simulate reading by gently scrolling down to where the results render
            for _ in range(random.randint(2, 3)):
                scroll_delta = random.randint(280, 480)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(0.5, 2.0))

            # --- HANDLE ONE-TRUST COOKIE BANNER ---
            if not cookie_accepted:
                # Locate the button natively using its unique HTML ID
                cookie_button = page.locator("#onetrust-accept-btn-handler")

                # Check if it has popped into view on the layout
                if cookie_button.is_visible():
                    print("🍪 OneTrust banner detected. Executing humanized click...")
                    # CloakBrowser automatically curves the mouse path here because humanize=True
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(0.5, 1.5))
            # ----------------------------------------------------
            # SECURE PLAYWRIGHT DATA EXTRACTION
            # ----------------------------------------------------
            # Isolate the container block elements
            row_locators = page.locator(
                "#paginatedResults > fieldset > div").all()
            print(f"📊 Found {len(row_locators)} fund rows on page {id_page}.")

            for row in row_locators:
                f = {}
                try:
                    # Cleanly extract text content
                    name = row.locator(
                        "div:nth-child(2) > label > span > span").text_content().strip()

                    # Target the anchor element safely
                    anchor = row.locator(
                        "div:nth-child(2) > div > div > a")

                    # if anchor.count() > 0:
                    #    # Grab the literal string attribute
                    #    raw_url = anchor.get_attribute("href")

                    raw_url = anchor.get_attribute("href")
                    if raw_url:
                        # Evaluate browser property to guarantee a full, clean absolute path
                        absolute_url = anchor.evaluate("el => el.href")

                        # Standard internal text extraction functions (e.g. your isin utility)
                        isin = isin_from_text(absolute_url)

                        f.update(name=name, url=absolute_url, isin=isin)
                        funds.append(f)

                except Exception as row_error:
                    # Individual row parsing failures won't break the page loop execution
                    print(f"⚠️ Skipping damaged row: {row_error}")
                    continue

        except Exception as page_error:
            print(
                f"❌ Failed processing page {id_page} due to connection error: {page_error}")
            # Refresh context tab if communication gets cut off mid-scrape
            try:
                page.close()
            except:
                pass
            page = browser.new_page()
        # TEST
        break

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
