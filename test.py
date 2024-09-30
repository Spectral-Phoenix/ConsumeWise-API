import requests

# Define the URL of your FastAPI application
url = "https://consumewise-253339989916.us-central1.run.app/process_product"

# Define the payload with the URL
payload = {
    "url":"https://blinkit.com/prn/coca-cola-soft-drink-750-ml-pack-of-2/prid/396483"
}

# Send the POST request
response = requests.post(url, json=payload)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.json())