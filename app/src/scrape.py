import asyncio
import re
from urllib.parse import urlparse

import aiohttp

from app.src.config import AsyncWebCrawler

async def scrape_product_page(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if "blinkit" in domain:
        website = "blinkit"
    elif "swiggy.com" in domain:
        website = "instamart"
    elif "bigbasket.com" in domain:
        website = "bigbasket"
    else:
        raise ValueError(f"Unsupported website domain: {domain}")

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)
        markdown_content = result.markdown

        if website == "blinkit":
            header_line = next((line.strip() for line in markdown_content.splitlines() if re.match(r"^#+\s", line)), None)
            start_index, end_index = markdown_content.find("My Cart"), markdown_content.find("Disclaimer")
            cleaned_content = markdown_content[start_index + len("My Cart"):end_index] if start_index != -1 and end_index != -1 else markdown_content
            final_markdown_content = (header_line + "\n" + cleaned_content) if header_line else cleaned_content

            image_links = []
            lines = final_markdown_content.splitlines()
            for i, line in enumerate(lines):
                potential_links = re.findall(r"https?://[^\s\)\"]+", line)
                for link in potential_links:
                    if "cdn.grofers.com" in link:
                        if not link.endswith((".jpg", ".jpeg")) and i + 1 < len(lines) and "cdn.grofers.com" not in lines[i + 1]:
                            link += lines[i + 1].strip()
                        cleaned_link = re.sub(r"https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=85,metadata=none,[^/]+/[^/]+/", "https://cdn.grofers.com/app/", link) \
                            .replace("\\", "")
                        cleaned_link = re.sub(r"(\.jpg|\.jpeg).*", r"\1", cleaned_link)
                        image_links.append(cleaned_link)

            if len(image_links) >= 2:
                image_links = image_links[:-2]

            product_image_url = image_links[0] if image_links else None

        elif website == "bigbasket":
            # Extract image links using regex
            image_matches = re.findall(r'(https://www\.bigbasket\.com/media/uploads/[^)]+\.(?:jpg|jpeg))', markdown_content)
            
            image_links = []
            for base_image_link in image_matches:
                parts = base_image_link.split("_")
                for j in range(1, 10):
                    extrapolated_link = f"{parts[0]}-{j}_{parts[1]}"
                    image_links.append(extrapolated_link)

            valid_image_links = []

            conn = aiohttp.TCPConnector(limit=10)
            async with aiohttp.ClientSession(connector=conn) as session:
                async def validate_link(link):
                    try:
                        async with session.head(link, timeout=5) as response:
                            if response.status == 200:
                                return link
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        pass
                    return None

                tasks = [validate_link(link) for link in image_links]
                results = await asyncio.gather(*tasks)
                valid_image_links = [link for link in results if link is not None]

            # Extract cleaned content
            start_index = markdown_content.find("No Question asked")
            end_index = markdown_content.find("## Rating and Reviews", start_index)
            final_markdown_content = markdown_content[start_index + len("My Cart"):end_index] if start_index != -1 and end_index != -1 else markdown_content

            product_image_url = valid_image_links[0] if valid_image_links else None

        elif website == "instamart":
            # Implement Instamart specific scraping logic here
            # ...
            final_markdown_content, image_links, product_image_url = "", [], None

        return final_markdown_content, image_links, product_image_url