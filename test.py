from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from app.src.process import process_product_url, process_product_image

app = FastAPI()

class ProductInput(BaseModel):
    url: Optional[str] = None
    image: Optional[UploadFile] = None

@app.post("/process_product")
async def process_product(product: ProductInput):
    """
    Process a product URL or image and extract structured data.

    The product URL or image is passed as part of the request body.
    """
    try:
        if product.url:
            structured_data = await process_product_url(product.url)
        elif product.image:
            # Read the image file and process it
            image_content = await product.image.read()
            structured_data = await process_product_image(image_content)
        else:
            raise HTTPException(status_code=400, detail="Either URL or image must be provided")

        return structured_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")