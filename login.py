import os
import asyncio
import time
from datetime import datetime
import requests
from playwright.async_api import async_playwright

LOGIN_URL = "https://ctrl.lunes.host/"
COOKIE_FILE = "cookies/state.json"

ACCOUNTS = os.getenv("ACCOUNTS")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ONLY_ERROR_NOTIFY = os.getenv("ONLY_ERROR_NOTIFY", "true").lower() == "true"

os.makedirs("cookies", exist_ok=True)


def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )


async def detect_cloudflare(page):
    content = await page.content()
    if "Just a moment" in content or "cf-browser-verification" in content:
        return True
    return False


async def login_and_save_cookie(page, username, password):
    await page.fill('input[type="text"]', username)
    await page.fill('input[type="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(5000)

    content = await page.content()
    if "Dashboard" in content or "Logout" in content:
        await page.context.storage_state(path=COOKIE_FILE)
        return True
    return False


async def try_cookie_login(playwright):
    if not os.path.exists(COOKIE_FILE):
        return False

    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(storage_state=COOKIE_FILE)
    page = await context.new_page()

    await page.goto(LOGIN_URL, timeout=60000)
    await page.wait_for_timeout(5000)

    if await detect_cloudflare(page):
        print("⚠️ Cloudflare challenge detected")
        await browser.close()
        return False

    content = await page.content()
    if "Dashboard" in content:
        await browser.close()
        return True

    await browser.close()
    return False


async def full_login(playwright, username, password):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto(LOGIN_URL, timeout=60000)
    await page.wait_for_timeout(5000)

    if await detect_cloudflare(page):
        print("⚠️ Cloudflare challenge blocks login")
        await browser.close()
        return False

    success = await login_and_save_cookie(page, username, password)
    await browser.close()
    return success


async def main():
    if not ACCOUNTS:
        print("No ACCOUNTS configured")
        return

    username, password = ACCOUNTS.split(":")[0].split(":")

    async with async_playwright() as playwright:

        print("🔄 尝试使用 Cookie 登录...")
        cookie_ok = await try_cookie_login(playwright)

        if cookie_ok:
            print("✅ Cookie 登录成功")

            if not ONLY_ERROR_NOTIFY:
                send_tg(f"✅ Lunes 保活成功（Cookie模式）\n时间: {datetime.now()}")
            return

        print("🔐 Cookie失效，尝试完整登录...")
        login_ok = await full_login(playwright, username, password)

        if login_ok:
            print("✅ 完整登录成功并已保存 Cookie")

            if not ONLY_ERROR_NOTIFY:
                send_tg(f"✅ Lunes 完整登录成功\n时间: {datetime.now()}")
        else:
            print("❌ 登录失败（可能被 Cloudflare 阻挡）")

            send_tg(
                f"❌ Lunes 登录失败\n"
                f"时间: {datetime.now()}\n"
                f"原因: Cloudflare Challenge 或账号异常"
            )


asyncio.run(main())
