import asyncio
from typing import List
import httpx
import io
from PIL import Image
from app.src.generate import (
    extract_product_info_from_images,
    generate_structured_product_data,
)
from app.src.scrape import scrape_product_page

async def download_image(client: httpx.AsyncClient, url: str, index: int) -> Image.Image:

    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()  # Raise an exception for non-200 status codes

        # Verify the downloaded data is a valid image using Pillow
        
        image = Image.open(io.BytesIO(response.content))
        return image 

    except httpx.HTTPError as e:
        print(f"Error downloading image {index} from {url}: {e}")
    except Exception as e:
        print(f"Unexpected error downloading image {index} from {url}: {e}")
    
    return None

async def process_product_url(url):
    markdown_content, image_links, product_image_url = await scrape_product_page(url)

    async with httpx.AsyncClient() as client:
        image_files = [img for img in await asyncio.gather(*[download_image(client, link, i) for i, link in enumerate(image_links)]) if img]
    
    if not image_files:
        print("No images were successfully downloaded.")
        return None

    print(f"Number of images downloaded: {len(image_files)}")
    
    # Log the first few bytes of each image to inspect the data and check the format
    for i, img in enumerate(image_files):
        print(f"Image {i} format: {img.format}") 
        image_bytes = img.tobytes() 
        print(f"Image {i} first 10 bytes: {image_bytes[:10]}")

    # Convert PIL Image objects to byte strings (optionally specify format)
    image_bytes_list = []
    for img in image_files:
        with io.BytesIO() as output:
            img.save(output, format="JPEG")  # Replace "JPEG" with the actual format if needed
            image_bytes_list.append(output.getvalue())

    try:
        image_analysis_output = await extract_product_info_from_images(image_bytes_list)  # Pass byte strings
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