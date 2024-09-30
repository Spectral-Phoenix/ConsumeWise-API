import asyncio
from typing import List
import httpx
from app.src.generate import (
    extract_product_info_from_images,
    generate_structured_product_data,
)
from app.src.scrape import scrape_product_page


async def download_image(client: httpx.AsyncClient, url: str, index: int) -> bytes:
    # Implementation to download image using httpx
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.google.com"
    }
    response = await client.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    print(f"Error downloading image {index} from {url}: {response.status_code}")
    return None


async def process_product_url(url):
    markdown_content, image_links, product_image_url = await scrape_product_page(url)

    async with httpx.AsyncClient() as client:
        image_files = [img for img in await asyncio.gather(*[download_image(client, link, i) for i, link in enumerate(image_links)]) if img]
    
    if not image_files:
        print("No images were successfully downloaded.")
        return None

    print(f"Number of images downloaded: {len(image_files)}")
    
    # Log the first few bytes of each image to inspect the data
    for i, img in enumerate(image_files):
        print(f"Image {i} first 10 bytes: {img[:10]}")

    try:
        image_analysis_output = await extract_product_info_from_images(image_files)
        print(f"Image Analysis Output:\n{image_analysis_output}")
    except Exception as e:
        print(f"An error occurred during image analysis: {e}")
        return None

    structured_data = await generate_structured_product_data(markdown_content, image_analysis_output)
    # print(f"Structured Output:\n{structured_data}")

    structured_data['product_image_url'] = product_image_url 

    return structured_data

async def process_product_image(image_contents: List[bytes]):

    try:
        image_analysis_output = await extract_product_info_from_images(image_contents)
        print(f"Image Analysis Output:\n{image_analysis_output}")
    except Exception as e:
        print(f"An error occurred during image analysis: {e}")
        return None
    
    structured_data = await generate_structured_product_data(None, image_analysis_output)
    
    return structured_data