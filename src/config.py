import asyncio
import base64
import json
import os
import re
from io import BytesIO

import aiohttp
import google.generativeai as genai
from crawl4ai import AsyncWebCrawler
from google.ai.generativelanguage_v1beta.types import content
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from PIL import Image

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