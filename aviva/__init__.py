from curl_cffi import ProxySpec, requests as cloaked_requests
from aviva.kiid import get_kiid_url, isin_from_pdf
from aviva.mf import get_kiid_urls_per_worker
from utils import delay, get_fund_type_total
from worker import write_csv_by_id
from aviva.worker import aviva_pagination_per_worker


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

    funds = aviva_pagination_per_worker(
        base_url=runner_config["url"], total_per_w=runner_config["worker_data"])
    write_csv_by_id(csv_out, funds, ["name", "isin", "url"])
