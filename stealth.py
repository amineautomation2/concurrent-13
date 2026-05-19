from cloakbrowser import launch


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

        print("🕵️ Running CloakBrowser diagnostic against creepjs.org...")
        page.goto("https://creepjs.org/checker",
                  wait_until="commit", timeout=60000)
        page.wait_for_timeout(20000)
        page.screenshot(path="creepjs.png", full_page=True)

    except Exception as e:
        print(f"⚠️ Diagnostic error encountered: {e}")
    finally:
        browser.close()

    return is_successful


check_nowsecure()
