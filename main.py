import asyncio
import os
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def parse_kingshot_codes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    active_codes = []

    containers = soup.find_all('div', class_='space-y-2')

    for container in containers:
        code_element = container.find('p', class_='font-mono text-xl font-bold tracking-wider')
        status_element = container.find('span')
        
        if code_element and status_element:
            code_text = code_element.get_text(strip=True)
            status_text = status_element.get_text(strip=True)

            if "Expires:" in status_text and "Expired" not in status_text:
                active_codes.append(code_text)

    return active_codes

async def main():
    alliance_file = os.path.join(os.path.dirname(__file__), "alliance.txt")
    if not os.path.exists(alliance_file):
        print("Missing alliance.txt file!")
        return

    with open(alliance_file, "r") as f:
        all_members = [line.strip() for line in f.readlines() if line.strip()]

    if not all_members:
        print("No members found in alliance.txt!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) 
        
        # Add a realistic User-Agent to the context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Apply stealth techniques to the page
        from playwright_stealth import stealth_async
        await stealth_async(page)

        # --- 1. Scrape Active Codes Using Playwright ---
        print("--- Scraping Codes ---")
        try:
            await page.goto("https://kingshot.net/gift-codes")
            await asyncio.sleep(10) 
            html_content = await page.content()
            codes = parse_kingshot_codes(html_content)
            
            print(f"--- Found {len(codes)} Valid Codes ---")
            for code in codes:
                print(f"Code: {code}")
        except Exception as e:
            print(f"Error scraping codes: {e}")
            codes = []

        if not codes:
            print("No valid codes found!")
            await browser.close()
            return

        # --- 2. Redeem Codes ---
        url = "https://ks-giftcode.centurygame.com/"
        
        for fid in all_members:
            print(f"=== Starting Alliance Member: {fid} ===")
            
            for code in codes:
                try:
                    await page.goto(url)
                    await asyncio.sleep(2)
                    await page.fill('input[placeholder*="Player ID"]', fid)
                    await page.click('span:has-text("Login")')
                    await asyncio.sleep(2)
                    await page.fill('input[placeholder*="Gift Code"]', code)
                    await page.click('div.exchange_btn:has-text("Confirm")')
                    await asyncio.sleep(2) 
                    print(f"  Input {code} for {fid}")
                except Exception as e:
                    print(f"  Error for {code} on {fid}: {e}")

            await asyncio.sleep(random.uniform(0, 10))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())