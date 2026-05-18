import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from aviva.mf import aviva_mf_runner
from utils import find_element_or_none, isin_from_text, setup_driver, delay, write_json, get_fund_type_total
from worker import write_csv_by_id


def aviva_runner(id_w: int, max_w: int, sheet: str):
    csv_out = f"aviva_{id_w}_{sheet}.csv"
    runner_config: dict = {
        "total": get_fund_type_total(sheet),

    }
    match sheet:
        case "Investment":
            url = "https://www.direct.aviva.co.uk/wealth/InvestmentChoice/InvestmentTrustSearch"
            worker_data = runner_config["total"][id_w::max_w]
            config = dict(worker_data=worker_data, url=url)
            runner_config.update(config)
        case "ETF":
            url = "https://www.direct.aviva.co.uk/wealth/InvestmentChoice/ExchangeTradedFundSearch"
            worker_data = runner_config["total"][id_w::max_w]
            config = dict(worker_data=worker_data, url=url)
            runner_config.update(config)
        case "MF":
            url = "https://www.direct.aviva.co.uk/wealth/FundChoice/SelfSelectFundsList"
            worker_data = runner_config["total"][id_w::max_w]
            config = dict(worker_data=worker_data, url=url)
            runner_config.update(config)
            funds = aviva_result_per_worker(
                base_url=url, total_per_w=worker_data)
            # delay(10, 30)
            isin_funds = aviva_mf_runner(funds=funds)
            write_csv_by_id(csv_out, isin_funds, ["name", "isin", "url"])
            return

    funds = aviva_result_per_worker(
        base_url=runner_config["url"], total_per_w=runner_config["worker_data"])
    write_csv_by_id(csv_out, funds, ["name", "isin", "url"])


def aviva_result_per_worker(base_url: str, total_per_w: list[int], is_MF: bool = False) -> list[dict]:
    driver = setup_driver(True)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)
    driver.get(f"{base_url}?page={total_per_w[0]}")

    cookies_xpath = '//*[@id="onetrust-accept-btn-handler"]'
    cookies = find_element_or_none(wait, cookies_xpath)
    if cookies:
        # move_mouse_bezier(driver, cookies_xpath)
        cookies.click()

    funds = []
    for id_page in total_per_w:
        print(f'Aviva Investment [{id_page}/{len(total_per_w)}]')
        u = f'{base_url}?page={id_page}'
        if id_page > 1:
            driver.get(u)

        table = driver.find_elements(
            By.XPATH, '//*[@id="paginatedResults"]/fieldset/div')
        for row in table:
            f = dict()
            name = row.find_element(By.XPATH, './div[2]/label/span/span').text
            url = row.find_element(
                By.XPATH, './div[2]/div[1]/div/a').get_attribute('href')
            f.update(dict(name=name))
            if url:
                isin = isin_from_text(url) if not is_MF else ""
                f.update(dict(url=url, isin=isin))
            funds.append(f)
        delay(3, 5)
    driver.quit()
    return funds


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
    driver = setup_driver(True)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)
    for investment in investment_types:
        driver.get(investment["url"])

        cookies_xpath = '//*[@id="onetrust-accept-btn-handler"]'
        cookies = find_element_or_none(wait, cookies_xpath)
        if cookies:
            # move_mouse_bezier(driver, cookies_xpath)
            cookies.click()

        total_pages = 0
        total_pages_elm = find_element_or_none(
            wait, '//p[@data-qa-text="showingPage"]')
        if total_pages_elm:
            total_pages_re = re.findall(r'\d+$', total_pages_elm.text)
            if len(total_pages_re) == 1:
                total_pages = int(total_pages_re[0])
        investment.update(dict(total=total_pages))
        delay(5, 8)
    write_json("json/total.json", investment_types)
