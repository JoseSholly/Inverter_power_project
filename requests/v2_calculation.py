import requests
import json

url = "http://127.0.0.1:8000/api/v2/power_calculator/calculate/"

payload = {
    "system_voltage": 24.0,
    "battery_capacity": 200.0,
    "solar_panel_watt": 350.0,
    "items": [
      {
        "id": 1,
        "quantity": 1,
        "power_rating": 75.0,
        "backup_time": 5.0
      },
      {
        "id": 2,
        "quantity": 1,
        "power_rating": 120.0,
        "backup_time": 4.0
      },
      {
        "id": 3,
        "quantity": 8,
        "power_rating": 7.0,
        "backup_time": 7.0
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