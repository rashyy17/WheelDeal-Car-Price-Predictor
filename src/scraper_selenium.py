from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from urllib.parse import urljoin


def _parse_price(text):
    """Extract numeric price from text like '₹ 3,45,000' or '3,45,000'. Returns int or None."""
    if not text:
        return None
    # Remove currency symbols and commas, extract digits
    nums = re.findall(r"\d+", text.replace(',', ''))
    if not nums:
        return None
    try:
        return int(''.join(nums))
    except Exception:
        return None





def scrape_olx_listings(model_name="swift", pages=1, headless=True, wait=3):
    """Scrape OLX listings for a model_name. Returns list of dicts with basic fields.

    Notes:
    - Uses webdriver-manager to install Chrome driver if needed.
    - This is a simple scraper; OLX layout may change so selectors may need updates.
    - Keep `pages` small for interactive use (1-3 pages).
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        raise RuntimeError("Could not start Chrome webdriver. Ensure Chrome is installed and chromedriver is available") from e

    all_listings = []
    base = "https://www.olx.in"

    try:
        for page in range(1, pages + 1):
            # URL encode the query properly
            query = model_name.replace(' ', '-')
            url = f"https://www.olx.in/items/q-{query}?page={page}"
            print(f"🌐 Fetching {url} ...")
            driver.get(url)
            
            # Wait for content to load
            time.sleep(wait)
            
            # Try to wait for listings to appear
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-aut-id]"))
                )
            except:
                print("⚠️ Timeout waiting for listings to load")

            # Try multiple selectors (OLX changes their structure frequently)
            items = []
            selectors = [
                "ul > li[data-aut-id]",
                "li.EIR5N",
                "div[data-aut-id='itemBox']",
                "li._1DNjI",
                "div._2ZxqI"
            ]
            
            for selector in selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        print(f"✅ Found {len(items)} items using selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not items:
                print(f"⚠️ Page {page}: No items found with any selector")
                # Save page source for debugging
                if not headless:
                    print("Page title:", driver.title)
                continue

            print(f"✅ Page {page}: Processing {len(items)} items")

            for idx, it in enumerate(items):
                try:
                    # Get all text from the item
                    text = it.text.strip()
                    if not text:
                        continue
                    
                    # Extract title - try multiple selectors
                    title = None
                    title_selectors = ["h2", "span[data-aut-id='itemTitle']", "div._2tW1I"]
                    for sel in title_selectors:
                        try:
                            title_el = it.find_element(By.CSS_SELECTOR, sel)
                            title = title_el.text.strip()
                            if title:
                                break
                        except:
                            continue
                    
                    # Extract price - try multiple selectors
                    price = None
                    price_selectors = ["span._2xKfz", "span[data-aut-id='itemPrice']", "div._1zgtX"]
                    for sel in price_selectors:
                        try:
                            price_el = it.find_element(By.CSS_SELECTOR, sel)
                            price = _parse_price(price_el.text)
                            if price:
                                break
                        except:
                            continue
                    
                    # Fallback: search for price in text
                    if not price:
                        price = _parse_price(text)
                    
                    # Extract link
                    href = None
                    try:
                        a = it.find_element(By.CSS_SELECTOR, "a")
                        href = a.get_attribute("href")
                        if href and href.startswith('/'):
                            href = urljoin(base, href)
                    except:
                        pass
                    
                    # Extract location
                    location = None
                    location_selectors = ["p._2TVI3", "span[data-aut-id='item-location']", "div._1KOFM"]
                    for sel in location_selectors:
                        try:
                            loc_el = it.find_element(By.CSS_SELECTOR, sel)
                            location = loc_el.text.strip()
                            if location:
                                break
                        except:
                            continue
                    
                    # Only add if we have at least a title or price
                    if title or price:
                        all_listings.append({
                            "title": title or text.split('\n')[0] if text else "Unknown",
                            "price": price,
                            "url": href,
                            "meta": location or "Location not specified",
                            "raw": text,
                        })
                        
                except Exception as e:
                    print(f"Error processing item {idx}: {e}")
                    continue
            
            print(f"✅ Page {page}: Extracted {len(all_listings)} total listings so far")

    except Exception as e:
        print(f"❌ Scraping error: {e}")
        raise
    finally:
        driver.quit()

    print(f"🎉 Total listings scraped: {len(all_listings)}")
    return all_listings


if __name__ == "__main__":
    # Test with a common search term
    print("Testing OLX scraper...")
    data = scrape_olx_listings("maruti swift delhi", pages=1, headless=False, wait=4)
    print(f"\nScraped {len(data)} listings")
    if data:
        print("\nFirst 3 listings:")
        for i, item in enumerate(data[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Price: ₹{item['price']:,}" if item['price'] else "   Price: N/A")
            print(f"   Location: {item['meta']}")
            print(f"   URL: {item['url']}")