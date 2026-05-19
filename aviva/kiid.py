import random
import re
from typing import List, Dict
from cloakbrowser import launch
from pypdf import PdfReader
import io
from utils import get_xlsx_filepath, fetch_with_backoff, get_random_user_agent
from worker import get_xlsx_data, merge_csv_to_xlsx, write_csv_by_id


def check_nowsecure() -> bool:
    """
    Dedicated diagnostic function targeting nowsecure.nl.
    Launches CloakBrowser to verify if the custom C++ patched binary 
    successfully clears Cloudflare challenges without automation stalls.
    """
    print("🕵️ Running CloakBrowser diagnostic against nowsecure.nl...")

    # Launch CloakBrowser's stealth Chromium build
    browser = launch(
        headless=True,
        humanize=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    is_successful = False
    try:
        page = browser.new_page()
        page.goto("https://nowsecure.nl", wait_until="commit", timeout=60000)

        # Settle window to let Cloudflare Turnstile token evaluation finish
        page.wait_for_timeout(6000)

        page_title = page.title()
        print(f"Captured Diagnostic Title: '{page_title}'")

        if "Cloudflare" in page_title or not page_title:
            print("❌ Diagnostic Verdict: Blocked or suspended by Turnstile.")
        else:
            print("✅ Diagnostic Verdict: Clean bypass! Browser stayed hidden.")
            is_successful = True

        # Capture verification snapshot safely
        page.screenshot(path="nowsecure_diagnostic.png")
        print("Diagnostic screen snapshot saved to nowsecure_diagnostic.png")

    except Exception as e:
        print(f"⚠️ Diagnostic error encountered: {e}")
    finally:
        browser.close()

    return is_successful


def parse_url_list(data_list: List[Dict]) -> List[Dict]:
    """
    Independent parsing function that isolates standard dict loops.
    Re-uses a single CloakBrowser process context to safely crawl 
    the provided data array and record runtime title resolutions.
    """
    print(
        f"\n🚀 Starting loop process over payload array ({len(data_list)} items)...")

    browser = launch(
        headless=True,
        humanize=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    try:
        page = browser.new_page()
        page.set_default_navigation_timeout(10000)
        timeout_counter = 0
        for idx, item in enumerate(data_list, start=1):
            url = item.get("url")
            if not url:
                print(f"[{idx}] Skipping empty or invalid entry URL data format.")
                continue

            try:
                print(f"[{idx}/{len(data_list)}] Processing: {url}")
                page.route("**/geolocation.onetrust.com/**",
                           lambda route: route.abort())

                page.wait_for_timeout(random.randint(2000, 3000))
                page.goto(url, wait_until="commit", timeout=10000)
                page.wait_for_timeout(random.randint(1500, 2000))

                kiid_url = None
                href = page.locator(
                    "a[title='Link to KIID']").get_attribute("href")
                if href:
                    kiid_url = href
                item.update(dict(kiid=kiid_url))

            except Exception as e:
                print(f"⚠️ Error occurred crawling entry [{idx}]: {e}")
                if timeout_counter == 5:
                    page.screenshot(
                        path="screenshot/timeout.png", full_page=True)
                    print(
                        f"️️⚠️ Max timeout[{timeout_counter}] reached, gracefully exit.")
                    browser.close()
                    return []
                timeout_counter += 1

    finally:
        print("Crawl complete. Securing background engine context.")
        browser.close()

    return data_list


# Get missing isin from xlsx


def isin_from_pdf(url: str) -> str:
    cookies = {
        'ApplicationGatewayAffinityCORS': 'e1dd5c8d8f0aaac8dbef88daaa63d498',
        'ApplicationGatewayAffinity': 'e1dd5c8d8f0aaac8dbef88daaa63d498',
        'ASLBSA': '000308b0a98344aa5136cd97f89db34e2e86c9a9a23672c7290ae25904d97b86dce7',
        'ASLBSACORS': '000308b0a98344aa5136cd97f89db34e2e86c9a9a23672c7290ae25904d97b86dce7',
        'SessionSettingsID': 'b10bd8a1-4394-4e28-904f-ca4f17ec573f',
        '__RequestVerificationToken_L0NsaWVudHMvQWR2aXNlclNpdGU1': '8HIkdl9VLWU1k8AfLnhrAfynp83GKAARqbtQDuDxc8NECcdZibKX2qkgWB66sEV0mN1gGttu34LQ0Ob06rvIMcCG-0bQlaqdS1JflaweRaI1',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        # 'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        # 'Cookie': 'ApplicationGatewayAffinityCORS=e1dd5c8d8f0aaac8dbef88daaa63d498; ApplicationGatewayAffinity=e1dd5c8d8f0aaac8dbef88daaa63d498; ASLBSA=000308b0a98344aa5136cd97f89db34e2e86c9a9a23672c7290ae25904d97b86dce7; ASLBSACORS=000308b0a98344aa5136cd97f89db34e2e86c9a9a23672c7290ae25904d97b86dce7; SessionSettingsID=b10bd8a1-4394-4e28-904f-ca4f17ec573f; __RequestVerificationToken_L0NsaWVudHMvQWR2aXNlclNpdGU1=8HIkdl9VLWU1k8AfLnhrAfynp83GKAARqbtQDuDxc8NECcdZibKX2qkgWB66sEV0mN1gGttu34LQ0Ob06rvIMcCG-0bQlaqdS1JflaweRaI1',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Priority': 'u=0, i',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }
    headers.update(get_random_user_agent(platform=["linux"]))
    if len(url) == 0:
        return ""

    response = fetch_with_backoff(url, headers=headers, cookies=cookies)
    if response:
        if response.content:
            try:
                pdf_bytes = io.BytesIO(response.content)
                reader = PdfReader(pdf_bytes)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
            except Exception as e:
                print(f"[{url}]isin_from_pdf: ", e)
                return ""

            isin_pattern = r"[A-Z]{2}[A-Z0-9]{9}[0-9]"
            isin = re.findall(isin_pattern, text)
            if len(isin) > 0:
                return isin[0]
    return ""


def get_kiid_url(id_w, max_w):
    xlsx = get_xlsx_filepath("aviva.xlsx")
    data_xlsx = get_xlsx_data(xlsx, "MF")

    # distribute data per worker
    data_per_worker = data_xlsx[id_w::max_w]
    updated_data_per_worker = parse_url_list(data_per_worker)

    # get isin from pdf
    for data in updated_data_per_worker:
        if data.get("kiid"):
            isin = isin_from_pdf(data["kiid"])
            data.update(dict(isin=isin))

    # save worker data to csv
    out = f"aviva_{id_w}_KIID.csv"
    write_csv_by_id(out, updated_data_per_worker, [
                    "index", "name", "isin", "url"])
