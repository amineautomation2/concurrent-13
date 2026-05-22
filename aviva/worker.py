import time
from cloakbrowser import launch
import random
from utils import get_proxy_endpoint, isin_from_text


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

    # Explicit pointer management to control retries without dropping data
    page_index = 0
    MAX_TIMEOUT_PER_PROXY_MIN = 5 * 60

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
            print(
                f"⚠️ [{proxy_ip}] proxy reached max session time, refreshing proxy...")
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
            print(f"❌ Failed processing page {id_page}: {page_error}")
            try:
                page.close()
            except:
                pass
            page = browser.new_page()
            page_index -= 1
            time.sleep(10)

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
