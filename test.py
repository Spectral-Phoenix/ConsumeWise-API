import asyncio
import re
import os
import uuid
from io import BytesIO
from PIL import Image
from crawl4ai import AsyncWebCrawler
import google.generativeai as genai
import aiohttp

genai.configure(api_key=os.environ["API_KEY"])

# Gemini Model Configuration (used for both models)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1000,
}


async def extract_product_info_from_images(image_files):
    """Extracts product information from images using Gemini."""
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

    # Convert each image to a file and upload using genai.upload_file
    uploaded_files = []
    for image_data in image_files:
        image = Image.open(BytesIO(image_data))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")  # Save image as JPEG into buffer
        file_path = f"temp_image_{uuid.uuid4()}.jpg"
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())
        
        # Upload the image to the File API
        uploaded_file = genai.upload_file(path=file_path, display_name=f"Product Image {uuid.uuid4()}")
        uploaded_files.append(uploaded_file)
        print(f"Uploaded file '{uploaded_file.display_name}' as: {uploaded_file.uri}")

    prompt = """
    Carefully analyze the given images of food products and their packaging.
    Extract useful information like Product Info, Ingredients, Nutritional Information, Claims.
    Return the response in markdown format.
    """

    # Generate content using the uploaded files and the prompt
    response = model.generate_content([prompt, *uploaded_files])