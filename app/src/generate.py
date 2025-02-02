import json

from app.src.config import (
    GENERATION_CONFIG,
    BytesIO,
    HarmBlockThreshold,
    HarmCategory,
    Image,
    base64,
    content,
    genai,
)

async def analyze_product_info(text):
    
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

        prompt = f"""
        You will be given data about a product and a user's dietary preferences and other information.
        Your job is to carefully analyze the product data and user data and provide an output on whether the given product is good or bad for the user. 
        Provide the output in the form of a list of points. Also, support your decision with reasons why it is good/bad.

        Instructions:
        Keep the analysis clear and concise
        The user will see your analysis, so address user as you
        Make it personalized
        
        Output format (JSON):
        {{
          "analysis": ["...", "...", "...", ....]
        }}

        Data to Analyze:
        {text}
        """
        response = model.generate_content(prompt)
         # Parse the JSON output
        try:
            structured_analysis = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            structured_analysis = {"error": "Failed to parse JSON output"}

        return structured_analysis
    except Exception as e:
        return f"An error occurred during product analysis: {str(e)}"

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

        prompt = """
        Analyze the given images of a food product and its packaging. 
        Extract useful information like Product Info, Ingredients, Nutritional Information, Claims.
        When extracting nutritional information also mention the scale of the measuring like per serving or per 100g, it is very useful
        in maintaing the same scale for all the products.
        Return the response in markdown format.
        """
        response = model.generate_content([*images, prompt])
        return response.text
    except Exception as e:
        return f"An error occurred during image analysis: {str(e)}"

async def generate_structured_product_data(markdown_content, image_analysis_output):
    try:
        NEW_GENERATION_CONFIG = {
          "temperature": 0.9,
          "top_p": 0.95,
          "top_k": 64,
          "max_output_tokens": 1000,
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
            - Categorize the purpose and frequency of the product correctly.
            - Identifying the weight of the product is very important, keep it accurate.
            - Convert the nutrient information into a list of individual nutrient details, each separated by a comma.\
             Ensure that each nutrient name is followed by its value, and any percentage daily value (DV) is mentioned in parentheses wherever applicable
            - When calculating the nutrient information, give all the information relative to the entire product(not per serving or per 100g or anything like that\
              which will increase the transparency about the product)
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