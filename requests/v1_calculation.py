import requests
import json

url = "http://127.0.0.1:8000/api/v1/power_calculator/calculate/"

payload = {
    "backup_time": 4,
    "battery_capacity": 200,
    "system_voltage": 24,
    "solar_panel_watt": 350,
    "items": [
        {
            "id": 8,
            "quantity": 6,
            "power_rating": 10
        },
        {
            "id": 18,
            "quantity": 3,
            "power_rating": 75
        },
        {
            "id": 17,
            "quantity": 1,
            "power_rating": 120
        },
        {
            "id": 15,
            "quantity": 1,
            "power_rating": 150
        },
        {
            "id": 12,
            "quantity": 2,
            "power_rating": 150
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=4))

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print("Response Content:", e.response.text)