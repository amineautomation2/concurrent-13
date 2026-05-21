import time
from cloakbrowser import launch
import random
from utils import isin_from_text
from aviva import get_current_exit_ip


def aviva_pagination_per_worker(base_url: str, total_per_w: list[int], assigned_proxy: str) -> list[dict]:
    # 1. Fetch initial IP and launch browser engine with automated context sync profiles
    session_ip = get_current_exit_ip(assigned_proxy)
    print(f"📡 Initializing Aviva Worker. Active IP: {session_ip}")

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
            time.sleep(random.uniform(4.0, 7.0))

            # Fast-return navigation to reduce server tracker exposure window
            page.goto(target_url, wait_until="commit", timeout=45000)

            # Move cursor smoothly into the reading viewport space
            page.mouse.move(random.randint(200, 700), random.randint(200, 600))
            time.sleep(random.uniform(0.5, 1.2))

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
                    time.sleep(random.uniform(1.5, 2.5))

            # Simulate reading by gently scrolling down to where the results render
            for _ in range(random.randint(2, 3)):
                scroll_delta = random.randint(280, 480)
                page.evaluate(f"window.scrollBy(0, {scroll_delta})")
                time.sleep(random.uniform(1.5, 2.8))

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
                        "div:nth-child(2) > div:nth-child(1) > div > a")

                    if anchor.count() > 0:
                        # Grab the literal string attribute
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
