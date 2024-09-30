from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.process import process_product_image, process_product_url

app = FastAPI()

class ProductURLs(BaseModel):
    urls: List[str]

@app.post("/process_products")
async def process_products(
    products: Optional[ProductURLs] = None,
    images: Optional[List[UploadFile]] = File(None)
):
    results = []
    try:
        if images:
            if len(images) > 5:
                raise HTTPException(status_code=400, detail="You can upload up to 5 images only.")

            image_contents = [await image.read() for image in images]

            structured_data = await process_product_image(image_contents)
            results.append(structured_data)

        elif products and products.urls:
            for url in products.urls:
                structured_data = await process_product_url(url)
                results.append(structured_data)

        else:
            raise HTTPException(status_code=400, detail="No URLs or images provided.")

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
