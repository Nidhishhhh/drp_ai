import requests

url = "http://127.0.0.1:8000/api/v1/search"
files = {"file": ("red_jacket_person.png", open("red_jacket_person.png", "rb"), "image/png")}

response = requests.post(url, files=files)
print(response.json())