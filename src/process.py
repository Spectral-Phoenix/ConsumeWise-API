import asyncio
from typing import List

from src.config import aiohttp, download_image
from src.generate import (
    extract_product_info_from_images,
    generate_structured_product_data,
)
from src.scrape import scrape_product_page


async def process_product_url(url):
    markdown_content, image_links, product_image_url = await scrape_product_page(url)

    async with aiohttp.ClientSession() as session:
        image_files = [img for img in await asyncio.gather(*[download_image(session, link, i) for i, link in enumerate(image_links)]) if img]

    image_analysis_output = await extract_product_info_from_images(image_files)
    structured_data = await generate_structured_product_data(markdown_content, image_analysis_output)

    structured_data['product_image_url'] = product_image_url 

    return structured_data

async def process_product_image(image_contents: List[bytes]):

    image_analysis_output = await extract_product_info_from_images(image_contents)
    
    structured_data = await generate_structured_product_data(None, image_analysis_output)
    
    return structured_data