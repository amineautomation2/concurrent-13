import random
from playwright.sync_api import sync_playwright
from camoufox.utils import launch_options

with sync_playwright() as p:
    # 1. Randomize the operating system fingerprint on each run
    target_os = random.choice(["windows", "macos", "linux"])

    options = launch_options(
        headless=True,
        os=target_os,
        block_images=True,  # Saves bandwidth on GitHub Actions

        # proxy={
        #    "server": "http://your-residential-proxy-address.com:8000",
        #    "username": "your_username",
        #    "password": "your_password"
        # }
    )

    browser = p.firefox.launch(**options)
    context = browser.new_context()
    context.on("pageerror", lambda exc: None)  # type: ignore

    page = context.new_page()

    # 3. Add a slight human-like delay before navigating
    page.wait_for_timeout(random.randint(500, 2000))

    url = "https://www.direct.aviva.co.uk/wealth/FundChoice/SelfSelectFundsList/FundDetails/BDR8GG5/SelfSelectFund"
    page.goto(url, wait_until="commit")

    # 4. Give Akamai's background scripts time to process smoothly
    page.wait_for_timeout(2000)

    print("Page Title:", page.title())
    browser.close()
