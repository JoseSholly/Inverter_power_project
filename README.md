# Inverter Power Project API

This project provides a Django REST Framework API for calculating inverter, battery, and solar panel requirements based on a list of appliances and desired usage. It offers a stateless calculation endpoint with two versions (`v1` and `v2`), making it a flexible tool for quick estimations.

## Table of Contents
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Sample Requests](#sample-requests)
- [Differences Between v1 and v2](#differences-between-v1-and-v2)

## Features
- **Stateless Calculation**: Perform real-time inverter, battery, and solar panel sizing calculations without persisting calculation instances to the database.
- **Appliance Management (Optional)**: Maintain a database of predefined appliances that can be referenced by ID in calculation requests.
- **Detailed Outputs**: Provides comprehensive results including total load, inverter rating, total battery capacity, number of batteries, total solar panel capacity, number of solar panels, and controller current.
- **Individual Appliance Backup Times (v2)**: Allows specifying different backup times for each appliance, enabling more accurate estimations.
- **Modular Calculation Logic**: Calculation logic is encapsulated in a utility class for better organization and reusability.

## Technologies Used
- **Python**: Programming Language
- **Django**: Web Framework
- **Django REST Framework (DRF)**: For building the API
- **cURL**: For testing API endpoints (example provided)

## Setup Instructions
Follow these steps to get the project up and running on your local machine.

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### 1. Clone the Repository
```bash
git clone https://github.com/JoseSholly/Inverter_power_project.git
cd Inverter_power_project
```

### 2. Create and Activate a Virtual Environment
It's recommended to use a virtual environment to manage project dependencies.
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Database Setup
Apply database migrations to create the necessary tables. If you are using the Appliance model for lookup, you'll need to run migrations.
```bash
python manage.py migrate
```

### 5. Populate Appliance Data
To quickly add sample appliance data to your database, you can use the custom management command:
```bash
python manage.py populate_appliances
```
This command will create a set of default Appliance records, which are necessary for testing the calculation endpoint with appliance IDs.

### 6. Run the Development Server
```bash
python manage.py runserver
```
The API will now be running on `http://127.0.0.1:8000/`.

## API Endpoints
The API provides the following endpoints:

### 1. List Appliances (GET)
- **URL**: `/api/v2/appliances/`
- **Method**: GET
- **Description**: Retrieves a list of all predefined appliance records from the database.
- **Example Response**:
```json
[
    {
        "id": 1,
        "name": "Laptop"
    },
    {
        "id": 2,
        "name": "TV"
    }
]
```

### 2. Perform Calculation (POST)
- **URLs**:
  - v1: `/api/v1/power_calculator/calculate/` 
  - v2: `/api/v2/power_calculator/calculate/`
- **Method**: POST
- **Description**: Takes system parameters and a list of appliance details (referenced by ID) to calculate inverter, battery, and solar panel requirements. Results are returned directly and not stored in the database.

#### v1 Request Body Fields
- `system_voltage` (float, required): System voltage in Volts (V).
- `battery_capacity` (float, required): Individual battery capacity in Ampere-hours (Ah).
- `solar_panel_watt` (float, required): Individual solar panel rating in Watts-peak (Wp).
- `backup_time` (float, required): Uniform backup time for all appliances in hours.
- `items` (array, required): List of appliances:
  - `id` (integer, required): Appliance ID.
  - `quantity` (integer, required): Number of units.
  - `power_rating` (float, required): Power consumption in Watts (W).

#### v2 Request Body Fields
- `system_voltage` (float, required): System voltage in Volts (V).
- `battery_capacity` (float, required): Individual battery capacity in Ampere-hours (Ah).
- `solar_panel_watt` (float, required): Individual solar panel rating in Watts-peak (Wp).
- `items` (array, required): List of appliances:
  - `id` (integer, required): Appliance ID.
  - `quantity` (integer, required): Number of units.
  - `power_rating` (float, required): Power consumption in Watts (W).
  - `backup_time` (float, required): Backup time for this appliance in hours.

## Sample Requests
Sample request scripts are located in the `requests/` folder within the project directory.

### v1 Sample Request
Run the `v1_calculation.py` script:
```bash
python requests/v1_calculation.py
```

#### v1 Example Request Payload
```json
{
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
```

#### v1 Example Response
```json
{
    "total_load": 855,
    "inverter_rating": 1.06875,
    "total_battery_capacity": 178.12,
    "numbers_of_batteries": 2,
    "total_solar_panel_capacity_needed": 712.5,
    "numbers_of_solar_panel": 3,
    "total_current": 43.75,
    "backup_time": 4,
    "battery_capacity": 200,
    "system_voltage": 24,
    "solar_panel_watt": 350,
    "items": [
        {
            "id": 8,
            "name": "LED Light",
            "quantity": 6,
            "power_rating": 10
        },
        {
            "id": 18,
            "name": "Radio",
            "quantity": 3,
            "power_rating": 75
        },
        {
            "id": 17,
            "name": "Home Theater",
            "quantity": 1,
            "power_rating": 120
        },
        {
            "id": 15,
            "name": "Washing Machine",
            "quantity": 1,
            "power_rating": 150
        },
        {
            "id": 12,
            "name": "Refrigerator",
            "quantity": 2,
            "power_rating": 150
        }
    ]
}
```

### v2 Sample Request
Run the `v2_calculation.py` script:
```bash
python requests/v2_calculation.py
```

#### v2 Example Request Payload
```json
{
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
```

#### v2 Example Response
```json
{
    "system_voltage": 24.0,
    "battery_capacity": 200.0,
    "solar_panel_watt": 350.0,
    "total_load": 251.0,
    "inverter_rating": 0.31,
    "total_battery_capacity": 51.96,
    "numbers_of_batteries": 1,
    "total_solar_panel_capacity_needed": 259.79,
    "numbers_of_solar_panel": 1,
    "controller_current": 13.53,
    "items": [
        {
            "id": 1,
            "name": "Wifi Router",
            "quantity": 1,
            "power_rating": 75.0,
            "backup_time": 5.0
        },
        {
            "id": 2,
            "name": "Phone Charger",
            "quantity": 1,
            "power_rating": 120.0,
            "backup_time": 4.0
        },
        {
            "id": 3,
            "name": "Fridge",
            "quantity": 8,
            "power_rating": 7.0,
            "backup_time": 7.0
        }
    ]
}
```

## Differences Between v1 and v2
- **Backup Time**:
  - **v1**: Uses a single `backup_time` for all appliances, applied uniformly.
  - **v2**: Allows individual `backup_time` for each appliance in the `items` array, enabling more precise calculations.
- **Response Fields**:
  - **v1**: Includes `total_current`.
  - **v2**: Includes `controller_current` for solar charge controller sizing.
- **Use Case**:
  - **v1**: Best for scenarios where all appliances have the same backup time requirement.
  - **v2**: Ideal for complex setups with varying backup time needs per appliance.