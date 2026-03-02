import os
import asyncio
from datetime import datetime
import requests
from playwright.async_api import async_playwright

LOGIN_URL = "https://ctrl.lunes.host/"

ACCOUNTS = os.getenv("ACCOUNTS")
SERVER_ID = os.getenv("SERVER_ID")
SERVER_UUID = os.getenv("SERVER_UUID")
NODE_HOST = os.getenv("NODE_HOST")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ONLY_ERROR_NOTIFY = os.getenv("ONLY_ERROR_NOTIFY", "true").lower() == "true"

os.makedirs("cookies", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)


def send_tg(text, photo_path=None):
    if not BOT_TOKEN or not CHAT_ID:
        return

    if photo_path:
        with open(photo_path, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": text},
                files={"photo": f}
            )
    else:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text}
        )


async def detect_cloudflare(page):
    content = await page.content()
    return "Just a moment" in content or "cf-browser-verification" in content


async def verify_server(page):
    content = await page.content()

    checks = []
    if SERVER_ID:
        checks.append(SERVER_ID in content)
    if SERVER_UUID:
        checks.append(SERVER_UUID in content)
    if NODE_HOST:
        checks.append(NODE_HOST in content)

    if not checks:
        return True

    return all(checks)


async def login_account(playwright, username, password):
    cookie_file = f"cookies/{username}.json"
    screenshot_path = f"screenshots/{username}.png"

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        storage_state=cookie_file if os.path.exists(cookie_file) else None
    )
    page = await context.new_page()

    await page.goto(LOGIN_URL, timeout=60000)
    await page.wait_for_timeout(8000)

    # 检测 Cloudflare
    if await detect_cloudflare(page):
        await page.screenshot(path=screenshot_path)
        await browser.close()
        return False, "Cloudflare Challenge", screenshot_path

    content = await page.content()

    # 如果未进入 Dashboard，则执行登录
    if "Dashboard" not in content:
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(8000)

    content = await page.content()

    if "Dashboard" not in content:
        await page.screenshot(path=screenshot_path)
        await browser.close()
        return False, "Login Failed", screenshot_path

    # 校验服务器信息
    if not await verify_server(page):
        await page.screenshot(path=screenshot_path)
        await browser.close()
        return False, "Server Info Not Matched", screenshot_path

    await context.storage_state(path=cookie_file)
    await browser.close()
    return True, "Success", None


async def main():
    if not ACCOUNTS:
        print("No ACCOUNTS provided")
        return

    accounts = ACCOUNTS.split(",")

    async with async_playwright() as playwright:
        for acc in accounts:
            username, password = acc.split(":")
            print(f"🔄 Checking {username}")

            ok, msg, screenshot = await login_account(playwright, username, password)

            if ok:
                print(f"✅ {username} success")
                if not ONLY_ERROR_NOTIFY:
                    send_tg(f"✅ {username} 保活成功\n时间: {datetime.now()}")
            else:
                print(f"❌ {username} failed: {msg}")
                send_tg(
                    f"❌ {username} 保活失败\n原因: {msg}\n时间: {datetime.now()}",
                    screenshot
                )


asyncio.run(main())
