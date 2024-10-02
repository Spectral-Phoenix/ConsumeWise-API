import asyncio
from typing import List
import os
import hashlib

from google.cloud import firestore
from app.src.config import aiohttp, download_image
from app.src.generate import (
    extract_product_info_from_images,
    generate_structured_product_data,
    analyze_product_info,
)
from app.src.scrape import scrape_product_page

# Initialize Firestore client
# Replace 'your-project-id' with your actual project ID or use environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp.json"
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "consumewise-437114")
firestore_client = firestore.Client()

async def process_product_url(url):
    # Create a unique ID for the document using a hash
    doc_id = hashlib.sha256(url.encode()).hexdigest()
    doc_ref = firestore_client.collection('products').document(doc_id)

    # Check if data exists in Firestore
    doc = doc_ref.get()
    if doc.exists:
        print(f"Data for URL {url} already exists in Firestore.")
        return doc.to_dict()

    # Data not found, proceed with analysis
    markdown_content, image_links, product_image_url = await scrape_product_page(url)

    async with aiohttp.ClientSession() as session:
        image_files = [
            img for img in await asyncio.gather(
                *[download_image(session, link, i) for i, link in enumerate(image_links)]
            ) if img
        ]
    print(len(image_files))
    image_analysis_output = await extract_product_info_from_images(image_files)
    structured_data = await generate_structured_product_data(markdown_content, image_analysis_output)

    structured_data['product_image_url'] = product_image_url

    # Store data in Firestore
    doc_ref.set(structured_data)
    print(f"Data for URL {url} stored in Firestore.")

    return structured_data

async def process_product_image(image_contents: List[bytes]):
    image_analysis_output = await extract_product_info_from_images(image_contents)
    structured_data = await generate_structured_product_data(None, image_analysis_output)
    return structured_data


async def analyze_data(text):

    analysis_output = await analyze_product_info(text)
    return analysis_output

# Example usage:
# asyncio.run(process_product_url("https://example.com/product"))
