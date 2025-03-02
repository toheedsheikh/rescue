import requests

# Specify the public ngrok URL and the API endpoint
url = "https://3e3d-34-106-3-100.ngrok-free.app/predict"  # Replace <NGROK_PUBLIC_URL> with your actual ngrok URL

# Specify the path to the image file you want to test
image_path = "./download.jfif"

# Send a POST request with the image file
with open(image_path, "rb") as image_file:
    files = {"file": image_file}
    response = requests.post(url, files=files)

# Check if the request was successful and print the response
if response.status_code == 200:
    print("Prediction:", response.json().get("predicted_label"))
else:
    print("Error:", response.json().get("error"))