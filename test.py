import time
from cloakbrowser import launch
import random
from curl_cffi import ProxySpec, requests as cloaked_requests
from re import compile
from utils import get_xlsx_filepath, save_xlsx
from worker import get_xlsx_data
url = "https://www.direct.aviva.co.uk/wealth/FundChoice/SelfSelectFundsList/FundDetails/B2PB2C7/SelfSelectFund"
url = "https://www.direct.aviva.co.uk/wealth/FundChoice/SelfSelectFundsList/FundDetails/3395327/SelfSelectFund"
xlsx = get_xlsx_filepath("aviva.xlsx")
data = get_xlsx_data(xlsx, "MF")

for fund in data:
    sedol_re = compile(r"[A-Z0-9]{7}")
    sedol = sedol_re.findall(fund["url"])
    if len(sedol) == 1:
        sedol = sedol[0]
        fund.update(dict(sedol=sedol))

save_xlsx(xlsx, data, ["name", "sedol", "url"], "MF")


def get_current_exit_ip(proxy_url) -> str | None:
    socks_proxies = ProxySpec({"http": proxy_url, "https": proxy_url})
    try:
        response = cloaked_requests.get(
            "https://api.ipify.org",
            proxies=socks_proxies,
            impersonate="chrome",
            timeout=8
        )
        if response.status_code == 200:
            return response.text.strip()
    except:
        return None
    return None


def execute_worker_task_real(worker_id: int, funds: list[dict], assigned_proxy: str) -> list[dict]:
    """
    Executes tasks with full stealth while monitoring for 
    unpredictable residential IP rotation.
    """
    # 1. Establish initial tracking metrics
    session_ip = get_current_exit_ip(assigned_proxy)
    print(f"📡 [Worker {worker_id}] Initializing. Active IP: {session_ip}")

    # Launch CloakBrowser with automatic GeoIP matching for the current IP
    browser = launch(headless=True, proxy=assigned_proxy,
                     geoip=True, humanize=True)
    page = browser.new_page()

    session_start_time = time.time()

    for idx, fund in enumerate(funds, start=1):
        # ----------------------------------------------------
        # THE PRE-FLIGHT VERIFICATION
        # ----------------------------------------------------
        # Measure maximum safe time threshold (20 mins)
        session_start_time = time.time()
        time_elapsed = time.time() - session_start_time > (10 * 60)

        # Verify if the proxy provider dropped/swapped the IP out early
        current_ip = get_current_exit_ip(assigned_proxy)

        # If the proxy is completely dead or rotated early, handle gracefully
        if not current_ip:
            print(
                f"⚠️ [Worker {worker_id}] Proxy port dropped connection. Retrying...")
            time.sleep(5)
            continue

        if time_elapsed or (current_ip != session_ip):
            reason = "Max session age reached" if time_elapsed else f"Sticky IP rotated dynamically ({session_ip} -> {current_ip})"
            print(
                f"🔄 [Worker {worker_id}] Resetting browser state. Reason: {reason}")

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
                f"❌ [Worker {worker_id}] Navigation / Interaction failure: {fund} {e}")
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
    print(f"🏁 [Worker {worker_id}] Task processing batch complete.")
    return funds
