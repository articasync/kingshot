import asyncio
import os
import random
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def get_active_kingshot_codes(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
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

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return []

async def redeem_for_alliance(members, codes):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        url = "https://ks-giftcode.centurygame.com/"

        for fid in members:
            print(f"=== Starting Alliance Member: {fid} ===")
            
            for code in codes:
                try:
                    await page.goto(url)
                    await page.fill('input[placeholder*="Player ID"]', fid)
                    await page.click('span:has-text("Login")')
                    await asyncio.sleep(2)
                    await page.fill('input[placeholder*="Gift Code"]', code)
                    await page.click('div.exchange_btn:has-text("Confirm")')
                    
                    # Wait for site to process
                    await asyncio.sleep(2) 
                    print(f"  Attempted {code} for {fid}")
                except Exception as e:
                    print(f"  Error for {fid} on {code}: {e}")

            # Random sleep between 10-20 seconds before moving to the NEXT member
            cooldown = random.uniform(10, 20)
            print(f"Waiting {cooldown:.2f}s before next member to prevent IP block...")
            await asyncio.sleep(cooldown)

        await browser.close()

async def main():
    alliance_file = os.path.join(os.path.dirname(__file__), "alliance.txt")
    if os.path.exists(alliance_file):
        with open(alliance_file, "r") as f:
            all_members = [line.strip() for line in f.readlines() if line.strip()]
        url = "https://kingshot.net/gift-codes"
        codes = get_active_kingshot_codes(url)
        print(f"--- Found {len(codes)} Valid Codes ---")
        for code in codes:
            print(f"Code: {code}")
        if codes and all_members:
            await redeem_for_alliance(all_members, codes)
        else:
            print("No valid codes or missing members!")
    else:
        print("Missing alliance.txt file!")

if __name__ == "__main__":
    # GitHub Actions command line execution
    asyncio.run(main())