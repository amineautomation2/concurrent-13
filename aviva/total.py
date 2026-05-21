import time
from curl_cffi import ProxySpec, requests as cloaked_requests
from cloakbrowser import launch
import random
from re import findall
from utils import delay, write_json


def aviva_total() -> None:
    investment_types: list[dict] = [
        {
            "name": "Investment",
            "url": "https://www.direct.aviva.co.uk/wealth/InvestmentChoice/InvestmentTrustSearch",
        },
        {
            "name": "ETF",
            "url": "https://www.direct.aviva.co.uk/wealth/InvestmentChoice/ExchangeTradedFundSearch",
        },
        {
            "name": "MF",
            "url": "https://www.direct.aviva.co.uk/wealth/FundChoice/SelfSelectFundsList",
        },
    ]
    for idx, investment in enumerate(investment_types):
        assigned_proxy = f"socks5://c23aa2273d4cf55a8726__cr.gb:be209b0843f58c7e@gw.dataimpulse.com:1000{idx}"
        session_ip = None
        max_init_retries = 5

        for attempt in range(1, max_init_retries + 1):
            print(
                f"📡 [Worker] Verifying proxy connection... (Attempt {attempt}/{max_init_retries})")
            session_ip = get_current_exit_ip(assigned_proxy)

            if session_ip:
                print(
                    f"✅ [Worker] Proxy verified healthy. Active IP: {session_ip}")
                break

            if attempt < max_init_retries:
                sleep_duration = attempt * 15
                print(
                    f"⚠️ [Worker] Proxy port down/timed out. Sleeping {sleep_duration}s before retry...")
                time.sleep(sleep_duration)

        # Emergency Fallback: Terminate thread if the residential proxy port completely fails validation
        if not session_ip:
            print(
                "❌ [Fatal - Worker] Proxy failed health validation across 5 passes. Aborting execution.")

        browser = launch(headless=True, proxy=assigned_proxy,
                         geoip=True, humanize=True)
        page = browser.new_page()
        # Track cookie consent banner state across page loads
        cookie_accepted = False

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        print(
            f"📡 [{investment.get("name")}] Getting total pages.")
        try:
            # Humanized thinking pause before hitting the site
            time.sleep(random.uniform(3.0, 5.0))

            # Fast-return navigation to reduce server tracker exposure window
            page.goto(investment["url"],
                      wait_until="commit", timeout=45000)

            # Move cursor smoothly into the reading viewport space
            page.mouse.move(random.randint(200, 700),
                            random.randint(200, 600))
            time.sleep(random.uniform(0.5, 1.2))

            # --- HANDLE ONE-TRUST COOKIE BANNER ---
            if not cookie_accepted:
                # Locate the button natively using its unique HTML ID
                cookie_button = page.locator(
                    "#onetrust-accept-btn-handler")
                # Check if it has popped into view on the layout
                if cookie_button.is_visible():
                    print(
                        "🍪 OneTrust banner detected. Executing humanized click...")
                    # CloakBrowser automatically curves the mouse path here because humanize=True
                    cookie_button.click()
                    cookie_accepted = True
                    time.sleep(random.uniform(1.0, 1.5))

            # Simulate reading by gently scrolling down to where the results render
            for _ in range(random.randint(2, 3)):
                scroll_delta = random.randint(280, 480)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(0.5, 1.2))
            total_pages = 0
            total_el = page.locator('p[data-qa-text="showingPage"]')
            if total_el:
                total_pages_re = findall(
                    r'\d+$', total_el.text_content().strip())
                if len(total_pages_re) == 1:
                    total_pages = int(total_pages_re[0])
            investment.update(dict(total=total_pages))

        except Exception as row_error:
            # Individual row parsing failures won't break the page loop execution
            print(f"⚠️ Skipping damaged row: {row_error}")

        # ----------------------------------------------------
        # CLEAN RUNTIME TEARDOWN
        # ----------------------------------------------------
        try:
            page.close()
            browser.close()
        except:
            pass

        print(
            f"🏁 Worker execution batch complete. Found {investment.get("total")} pages.")
        delay(5, 8)
    write_json("json/total.json", investment_types)


def get_current_exit_ip(proxy_url):
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
