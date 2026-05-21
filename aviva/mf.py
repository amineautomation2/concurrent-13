import time
import random
from cloakbrowser import launch
from aviva.total import get_current_exit_ip


def get_kiid_urls_per_worker(id_worker: int, funds: list[dict], assigned_proxy: str) -> list[dict]:

    # ----------------------------------------------------
    # PRE-FLIGHT INITIAL PROXY HEALTH GATE
    # ----------------------------------------------------
    session_ip = None
    max_init_retries = 5

    for attempt in range(1, max_init_retries + 1):
        print(
            f"📡 [Worker {id_worker}] Verifying proxy connection... (Attempt {attempt}/{max_init_retries})")
        session_ip = get_current_exit_ip(assigned_proxy)

        if session_ip:
            print(
                f"✅ [Worker {id_worker}] Proxy verified healthy. Active IP: {session_ip}")
            break

        if attempt < max_init_retries:
            sleep_duration = attempt * 15
            print(
                f"⚠️ [Worker {id_worker}] Proxy port down/timed out. Sleeping {sleep_duration}s before retry...")
            time.sleep(sleep_duration)

    # Emergency Fallback: Terminate thread if the residential proxy port completely fails validation
    if not session_ip:
        print(
            f"❌ [Fatal - Worker {id_worker}] Proxy failed health validation across 5 passes. Aborting execution.")
        return funds

    # Initialize CloakBrowser safely behind our verified residential tunnel
    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()
    session_start_time = time.time()

    cookie_accepted = False

    # Explicit pointer management to handle mid-loop faults without losing track of funds
    fund_index = 0
    fund_retry_count = 0
    max_fund_retries = 3

    while fund_index < len(funds):
        fund = funds[fund_index]
        print(
            f"🕵️ [Worker {id_worker}] Processing Fund Record [{fund_index + 1}/{len(funds)}] (Attempt {fund_retry_count + 1}/{max_fund_retries})")
        url = fund["url"]

        # ----------------------------------------------------
        # RUNTIME PROXY INTEGRITY MONITORING
        # ----------------------------------------------------
        # Measure continuous time drift relative to initial context birth (10 min safety cap)
        time_elapsed = time.time() - session_start_time > (10 * 60)
        current_ip = session_ip
        if fund_index > 0:
            current_ip = get_current_exit_ip(assigned_proxy)

        # Handle hard proxy drop errors mid-scrape
        if not current_ip:
            print(
                f"⚠️ [Worker {id_worker}] Proxy dropped connection mid-run on item index {fund_index}.")
            fund_retry_count += 1

            if fund_retry_count >= max_fund_retries:
                print(
                    f"❌ [Worker {id_worker}] Proxy down consistently for 3 checks. Restarting stack context...")
                try:
                    page.close()
                    browser.close()
                except:
                    pass

                # Allow 60 seconds of cool-down time for your provider gateway to cycle nodes
                time.sleep(60)

                session_ip = get_current_exit_ip(assigned_proxy)
                if session_ip:
                    browser = launch(
                        headless=True, proxy=assigned_proxy, geoip=True, humanize=True)
                    page = browser.new_page()
                    session_start_time = time.time()
                    cookie_accepted = False

                fund_retry_count = 0
                fund_index += 1  # Increment index to step over broken links and avoid endless stalls
            else:
                time.sleep(15)
            continue

        # Handle normal session timeout or dynamic IP switch seamlessly
        if time_elapsed or (current_ip != session_ip):
            reason = "Max session age reached" if time_elapsed else f"Sticky IP rotated dynamically ({session_ip} -> {current_ip})"
            print(
                f"🔄 [Worker {id_worker}] Re-housing browser footprint. Reason: {reason}")
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
            time.sleep(random.uniform(3.0, 5.0))
            page.goto(url, wait_until="commit", timeout=45000)

            # Human Interaction: Trigger smooth cursor landing
            page.mouse.move(random.randint(150, 600), random.randint(150, 600))
            time.sleep(random.uniform(0.5, 1.2))

            # Human Interaction: Variable scrolling behavior to satisfy Akamai trackers
            for _ in range(random.randint(2, 3)):
                scroll_delta = random.randint(300, 500)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(0.6, 1.5))

            # --- HANDLE ONE-TRUST COOKIE BANNER ---
            if not cookie_accepted:
                cookie_button = page.locator("#onetrust-accept-btn-handler")
                if cookie_button.is_visible():
                    print(
                        f"🍪 [Worker {id_worker}] OneTrust banner found. Clicking...")
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(1, 1.5))

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
                print(
                    f"⚠️ [Worker {id_worker}] No matching KIID link element present on layout.")

            # ✅ SUCCESS: Shift index pointer to process the next fund in the queue
            fund_index += 1
            fund_retry_count = 0

        except Exception as e:
            print(
                f"❌ [Worker {id_worker}] Pipeline navigation / extraction failure: {e}")
            fund_retry_count += 1

            try:
                page.close()
            except:
                pass
            page = browser.new_page()

            if fund_retry_count >= max_fund_retries:
                print(
                    f"❌ [Worker {id_worker}] Max extraction retries hit for current index. Advancing forward.")
                fund_index += 1
                fund_retry_count = 0
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


def get_kiid_urls_per_worker_backup(id_worker: int, funds: list[dict], assigned_proxy: str) -> list[dict]:
    # 1. Establish initial tracking metrics
    session_ip = get_current_exit_ip(assigned_proxy)
    print(f"📡 [Worker {id_worker}] Initializing. Active IP: {session_ip}")

    # Launch CloakBrowser with automatic GeoIP matching for the current IP
    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()

    session_start_time = time.time()

    for idx, fund in enumerate(funds, start=1):
        # Measure maximum safe time threshold (10 mins)
        session_start_time = time.time()
        time_elapsed = time.time() - session_start_time > (10 * 60)

        # Verify if the proxy provider dropped/swapped the IP out early
        current_ip = get_current_exit_ip(assigned_proxy)
        cookie_accepted = False  # Reset since cookie data was purged on close

        # If the proxy is completely dead or rotated early, sleep for 5 minutes
        if not current_ip:
            print(
                f"⚠️ [Worker {id_worker}] Proxy port dropped connection. Retrying...")
            time.sleep(5 * 60)

        if time_elapsed or (current_ip != session_ip):
            reason = "Max session age reached" if time_elapsed else f"Sticky IP rotated dynamically ({session_ip} -> {current_ip})"
            print(
                f"🔄 [Worker {id_worker}] Resetting browser state. Reason: {reason}")

            # Wipe page context completely to flush mismatched Akamai session headers
            page.close()
            browser.close()

            # Re-launch dynamically to realign the engine's Canvas/WebGL and Timezone profiles
            session_ip = current_ip
            browser = launch(headless=True, proxy=assigned_proxy,
                             geoip=True, humanize=True)
            page = browser.new_page()
            session_start_time = time.time()
            cookie_accepted = False  # Reset since cookie data was purged on close

        # ----------------------------------------------------
        # NAVIGATE & EMULATE HUMAN BEHAVIOR
        # ----------------------------------------------------
        try:
            # Humanized pre-navigation delay
            time.sleep(random.uniform(3.0, 5.0))

            # Fast return execution to shield browser logic from heavy background fingerprinting
            url = fund["url"]
            page.goto(url, wait_until="commit", timeout=45000)

            # Human Interaction: Trigger cursor positioning on viewport
            page.mouse.move(random.randint(150, 600), random.randint(150, 600))
            time.sleep(random.uniform(0.5, 1.2))

            # Human Interaction: Variable scrolling cadence to feed Akamai telemetry
            for _ in range(random.randint(2, 3)):
                scroll_delta = random.randint(300, 500)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(0.5, 2.0))  # Reading buffer

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
            # SECURE EXTRACTION
            # ----------------------------------------------------
            kiid_url = None
            href = page.locator(
                "a[title='Link to KIID']").get_attribute("href")
            if href:
                kiid_url = href
            fund.update(dict(kiid=kiid_url))

        # ----------------------------------------------------
        except Exception as e:
            print(
                f"❌ [Worker {id_worker}] Navigation / Interaction failure: {fund} {e}")
            # Ensure the tab stays functional even if a single scrape fails
            try:
                page.close()
            except:
                pass
            page = browser.new_page()
        # TEST
        # break

    # Final cleanup
    try:
        page.close()
        browser.close()
    except:
        pass
    print(f"🏁 [Worker {id_worker}] Task processing batch complete.")
    return funds
