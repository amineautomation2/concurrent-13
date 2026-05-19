import re
from selenium.webdriver.support.wait import WebDriverWait
from utils import find_element_or_none, get_xlsx_filepath, setup_driver, delay, get_random_user_agent, fetch_with_backoff
from worker import get_xlsx_data
from pypdf import PdfReader
import io


def aviva_kiid_per_worker(funds_per_w: list[dict]) -> list[dict]:
    driver = setup_driver(True)
    driver.maximize_window()
    wait = WebDriverWait(driver, 3)

    cookies_xpath = '//*[@id="onetrust-reject-all-handler"]'
    cookies = find_element_or_none(wait, cookies_xpath)
    if cookies:
        # move_mouse_bezier(driver, cookies_xpath)
        cookies.click()

    for fund in funds_per_w:
        driver.get(fund["url"])

        kiid_xpath = '//a[@title="Link to KIID"]'
        kiid_elm = find_element_or_none(wait, kiid_xpath)
        if kiid_elm:
            url_kiid = kiid_elm.get_attribute("href")
            fund.update(dict(url_kiid=url_kiid))
        else:
            print("kiid not found =", fund['url'])
            fund.update(dict(url_kiid=None))
        delay(4, 7)
    driver.quit()
    return funds_per_w
