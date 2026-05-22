import re
import time
from pypdf import PdfReader
import io
from utils import delay, fetch_with_backoff, get_proxy_endpoint, get_random_user_agent
from worker import write_csv_by_id


def isin_from_pdf(url: str, proxy: str) -> str:
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

    response = fetch_with_backoff(
        url, headers=headers, cookies=cookies, proxy=proxy)
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

            # 1. Relaxed regex to find ISINs even if they have a random space inside
            isin_extract_rx = re.compile(
                r"[A-Z]{2}(?:[?\s]*[A-Z0-9]){9}[?\s]*[0-9]")

            # 2. Strict regex to validate after cleaning
            isin_strict_rx = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
            matches = isin_extract_rx.findall(text)

            for match in matches:
                # Clean the extracted string by removing all spaces
                cleaned_isin = match.replace(" ", "")

                # Strictly validate
                if isin_strict_rx.match(cleaned_isin):
                    return cleaned_isin
    return ""


def get_kiid_url(id_w: int, data_per_worker: list[dict]):
    # get isin from pdf
    isins = []
    session_start_time = time.time()
    MAX_SESSION_TIME_SECOND = 5 * 60
    proxy_dict = get_proxy_endpoint()
    session_proxy = proxy_dict["proxy"]
    for data in data_per_worker:
        session_expired = time.time() - session_start_time > MAX_SESSION_TIME_SECOND
        if session_expired:
            proxy_dict = get_proxy_endpoint()
            session_proxy = proxy_dict["proxy"]

        if data.get("kiid"):
            isin = isin_from_pdf(data["kiid"], session_proxy)
            isins.append(dict(name=data.get("name"),
                         isin=isin, url=data.get("url")))
            delay(1.5, 2.5)
        # TEST
        # break
    return isins
    # save worker data to csv
    out = f"aviva_{id_w}_KIID_ISIN.csv"
    write_csv_by_id(out, data_per_worker, [
                    "index", "name", "isin", "url"])
