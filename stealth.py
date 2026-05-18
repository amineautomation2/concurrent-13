from camoufox.sync_api import Camoufox

with Camoufox(headless='virtual') as browser:
    page = browser.new_page()
    url = "https://www.direct.aviva.co.uk/wealth/FundChoice/SelfSelectFundsList/FundDetails/BDR8GG5/SelfSelectFund"
    page.goto(url)
    print(page.title())
