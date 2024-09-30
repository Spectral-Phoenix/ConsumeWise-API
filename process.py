import asyncio
import re
import os
import json
from io import BytesIO
from PIL import Image
from crawl4ai import AsyncWebCrawler
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import aiohttp
import base64

genai.configure(api_key=os.environ["API_KEY"])

GENERATION_CONFIG = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1000,
}

async def download_image(session, url, index):
    try:
        async with session.get(url, timeout=30, allow_redirects=True) as response:
            if response.status == 200 and 'image' in response.headers.get('Content-Type', ''):
                return base64.b64encode(await response.read()).decode('utf-8')
    except Exception as e:
        print(f"Error downloading image {index} from {url}: {str(e)}")
    return None

async def verify_image_url(session, url):
    try:
        async with session.head(url, allow_redirects=True) as response:
            return response.status == 200 and 'image' in response.headers.get('Content-Type', '')
    except Exception:
        return False

async def extract_product_info_from_images(image_files):
    if not image_files:
        return "No images were successfully downloaded."

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-exp-0827", 
            generation_config=GENERATION_CONFIG,
            safety_settings={
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE
            })
        images = [Image.open(BytesIO(base64.b64decode(img))) for img in image_files if img]
        
        if not images:
            return "No valid images found in the provided data."

        prompt = "Analyze the given images of a food product and its packaging. Extract useful information like Product Info, Ingredients, Nutritional Information, Claims. Return the response in markdown format."
        response = model.generate_content([prompt, *images])
        return response.text
    except Exception as e:
        return f"An error occurred during image analysis: {str(e)}"

async def generate_structured_product_data(markdown_content, image_analysis_output):
    try:
        NEW_GENERATION_CONFIG = {
          "temperature": 0.7,
          "top_p": 0.95,
          "top_k": 64,
          "max_output_tokens": 8192,
          "response_schema": content.Schema(
            type = content.Type.OBJECT,
            properties = {
              "product_name": content.Schema(
                type = content.Type.STRING,
              ),
              "ingredients": content.Schema(
                type = content.Type.STRING,
              ),
              "nutritional_information": content.Schema(
                type = content.Type.STRING,
              ),
              "product_details": content.Schema(
                type = content.Type.OBJECT,
                properties = {
                  "brand_name": content.Schema(
                    type = content.Type.STRING,
                  ),
                  "weight": content.Schema(
                    type = content.Type.STRING,
                  ),
                  "category": content.Schema(
                    type = content.Type.OBJECT,
                    properties = {
                      "purpose": content.Schema(
                        type = content.Type.STRING,
                      ),
                      "frequency": content.Schema(
                        type = content.Type.STRING,
                      ),
                    },
                  ),
                },
              ),
              "claims": content.Schema(
                type = content.Type.STRING,
              ),
            },
          ),
          "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-exp-0827", 
            generation_config=NEW_GENERATION_CONFIG,
            safety_settings={
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE
            },
            system_instruction="""
            - Identify claims as promises about nutrition, strength, fruit content etc,you can ignore claims about taste or something like that.\
                We are purely focused on the health related claims of the product.\n/
            - List the nutritional information seperated by commas, no need to represent in tabular format.
            """)
        
        custom_prompt = f"""
        Generate a JSON product description from the following:

        **Product Description (Markdown):**
        ```markdown
        {markdown_content}
        ```

        **Image Analysis Output (Markdown):**
        ```markdown
        {image_analysis_output}
        ```
        """

        response = model.generate_content(custom_prompt)
        
        # Parse the JSON output
        try:
            structured_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            structured_data = {"error": "Failed to parse JSON output"}

        return structured_data
    except Exception as e:
        return {"error": f"An error occurred during structured data generation: {str(e)}"}

async def process_product_url(url):
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)
        markdown_content = result.markdown

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
                    if not link.endswith((".jpg", ".jpeg")) and i+1 < len(lines) and "cdn.grofers.com" not in lines[i+1]:
                        link += lines[i+1].strip()
                    cleaned_link = re.sub(r"https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=85,metadata=none,[^/]+/[^/]+/", "https://cdn.grofers.com/app/", link) \
                        .replace("\\", "") \
                        .replace(".jpg.*", ".jpg") \
                        .replace(".jpeg.*", ".jpeg")
                    image_links.append(cleaned_link)

        async with aiohttp.ClientSession() as session:
            verified_links = [link for link in image_links if await verify_image_url(session, link)]
            image_files = [img for img in await asyncio.gather(*[download_image(session, link, i) for i, link in enumerate(verified_links)]) if img]

        image_analysis_output = await extract_product_info_from_images(image_files)
        structured_data = await generate_structured_product_data(final_markdown_content, image_analysis_output)

        # Print the response
        return structured_data

# Example usage:
# asyncio.run(process_product_url("https://grofers.com/prn/britannia-marie-gold-biscuit/prid/184024")) 