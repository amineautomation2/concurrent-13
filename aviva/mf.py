import time
import random
from cloakbrowser import launch
from aviva.total import get_current_exit_ip


def get_kiid_urls_per_worker(id_worker: int, funds: list[dict], assigned_proxy: str) -> list[dict]:
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

        # ----------------------------------------------------
        # NAVIGATE & EMULATE HUMAN BEHAVIOR
        # ----------------------------------------------------
        try:
            # Humanized pre-navigation delay
            time.sleep(random.uniform(4.0, 7.0))

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
                time.sleep(random.uniform(1.5, 3.0))  # Reading buffer

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

    # Final cleanup
    try:
        page.close()
        browser.close()
    except:
        pass
    print(f"🏁 [Worker {id_worker}] Task processing batch complete.")
    return funds
