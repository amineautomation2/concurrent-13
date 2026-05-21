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
    PROXY_PER_WORKER = f"socks5h://c23aa2273d4cf55a8726:be209b0843f58c7e@gw.dataimpulse.com:1000{id_w}"
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
            funds_pagination = aviva_pagination_per_worker(
                base_url=runner_config["url"], total_per_w=runner_config["worker_data"], assigned_proxy=PROXY_PER_WORKER)
            delay(10, 30)
            funds_kiid = get_kiid_urls_per_worker(
                id_worker=id_w, funds=funds_pagination, assigned_proxy=PROXY_PER_WORKER)
            funds_with_isin = get_kiid_url(
                id_w=id_w, data_per_worker=funds_kiid)
            write_csv_by_id(csv_out, funds_with_isin, [
                            "name", "isin", "url"])
            return

    funds = aviva_pagination_per_worker(
        base_url=runner_config["url"], total_per_w=runner_config["worker_data"], assigned_proxy=PROXY_PER_WORKER)
    write_csv_by_id(csv_out, funds, ["name", "isin", "url"])


def get_current_exit_ip(proxy_url) -> str | None:
    """Checks the active exit IP from the SOCKS5 port using curl_cffi."""
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
