import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import urllib.parse

async def find_images_playwright(url):
  async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto(url)

    # Wait for the page to load (adjust timeout as needed)
    await page.wait_for_timeout(3000)  # 3 seconds

    # Get the page source after JavaScript rendering
    html_content = await page.content()

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    img_tags = soup.find_all('img')

    image_urls = []
    for img_tag in img_tags:
      src = img_tag.get('src')
      if src:
        parsed_url = urllib.parse.urljoin(url, src)
        if parsed_url.lower().endswith(('.jpg')):
          image_urls.append(parsed_url)

    await browser.close()
    return image_urls

async def main():
  target_url = "https://www.swiggy.com/instamart/item/PP8VVOYNES"
  image_urls = await find_images_playwright(target_url)

  if image_urls:
    print("\nFound image files (using Playwright):")
    for image_url in image_urls:
      print(image_url)
  else:
    print("No .jpg images found at the given URL.")


if __name__ == "__main__":
  asyncio.run(main())