import time
from curl_cffi import ProxySpec, requests as cloaked_requests
from cloakbrowser import launch
import random
from re import findall
from utils import delay, get_proxy_endpoint, write_json


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
        proxy_dict = get_proxy_endpoint()
        session_ip = proxy_dict["ip"]
        assigned_proxy = proxy_dict["proxy"]

        browser = launch(headless=True, proxy=assigned_proxy,
                         geoip=True, humanize=True)
        page = browser.new_page()
        cookie_accepted = False

        # ----------------------------------------------------
        # NAVIGATION & BEHAVIORAL HUMANIZATION
        # ----------------------------------------------------
        print(
            f"📡 [{investment.get("name")}] Getting total pages.")
        try:
            # Humanized thinking pause before hitting the site
            time.sleep(random.uniform(2.0, 4.0))

            # Fast-return navigation to reduce server tracker exposure window
            page.goto(investment["url"],
                      wait_until="commit", timeout=90 * 1000)

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
        delay(3, 5)
    write_json("json/total.json", investment_types)
