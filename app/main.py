from fastapi import FastAPI, HTTPException, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from app.src.process import process_product_url, process_product_image, analyze_data
from urllib.parse import urlparse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"], 
    allow_headers=["*"], 
)

class ProductInput(BaseModel):
    url: Optional[HttpUrl] = None
    images: Optional[List[UploadFile]] = None

@app.post("/process_product")
async def process_product(product: ProductInput):
    try:
        if product.url:
            url_str = str(product.url)
            parsed_url = urlparse(url_str)
            if parsed_url.netloc != "www.bigbasket.com":
                raise HTTPException(status_code=400, detail="Only URLs from 'bigbasket.com' are allowed for now!")
            
            structured_data = await process_product_url(url_str)
        elif product.images:
            if len(product.images) > 5:
                raise HTTPException(status_code=400, detail="Maximum of 5 images allowed")
            
            structured_data = []
            for image in product.images:
                image_content = await image.read()
                image_data = await process_product_image(image_content)
                structured_data.append(image_data)
        else:
            raise HTTPException(status_code=400, detail="Either URL or images must be provided")

        return structured_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/analysis")
async def analysis(data: str = Body(..., media_type="text/plain")):
    try:
        # Await the result of the analyze_data function
        analysis_result = await analyze_data(data) 
        return analysis_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")