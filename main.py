from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from process import process_product_url

app = FastAPI()

class ProductURL(BaseModel):
    url: str

@app.post("/process_product")
async def process_product(product: ProductURL):
    """
    Process a product URL and extract structured data.

    The product URL is passed as part of the request body.
    """
    try:
        print(product.url)
        structured_data = await process_product_url(product.url)
        return structured_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")