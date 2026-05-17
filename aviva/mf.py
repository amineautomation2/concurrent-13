import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from utils import find_element_or_none, get_xlsx_filepath, isin_from_text, save_xlsx, setup_driver, delay, get_random_user_agent, fetch_with_backoff
from worker import get_xlsx_data, write_csv_by_id
from pypdf import PdfReader
import io


def aviva_mf_runner(funds: list[dict] = []) -> list[dict]:
    xlsx = get_xlsx_filepath("aviva.xlsx")
    if len(funds) == 0:
        funds = get_xlsx_data(xlsx, "MF")
    funds_kiid_w = aviva_kiid_per_worker(funds_per_w=funds)
    for fund in funds_kiid_w:
        isin = isin_from_pdf(fund["url_kiid"])
        fund.update(dict(isin=isin))
    return funds_kiid_w
    # write_csv_by_id(f"aviva_{id_w}_MF.csv", funds, [
    #                "index", "name", "isin", "url"])
    # fields = ["name", "isin", "url"]
    # save_xlsx(xlsx, funds, fields, "MF")


def aviva_kiid_per_worker(funds_per_w: list[dict]) -> list[dict]:
    driver = setup_driver(True)
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)

    for fund in funds_per_w:
        driver.get(fund["url"])

        kiid_xpath = '//a[@title="Link to KIID"]'
        kiid_elm = find_element_or_none(wait, kiid_xpath)
        if kiid_elm:
            url_kiid = kiid_elm.get_attribute("href")
            fund.update(dict(url_kiid=url_kiid))
        delay(3, 5)
    driver.quit()
    return funds_per_w


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
    headers.update(get_random_user_agent())
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
