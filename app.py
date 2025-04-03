import os
from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime


app = Flask(__name__)

API_URL = "https://agmarknet.ceda.ashoka.edu.in/api/priceqtyapi"

# Commodity Mapping for Correct Display
commodity_map = {
    "3": "Rice",
    "1": "Wheat",
    "4": "Maize",
    "5": "Jowar",
    "30": "Ragi",
    "97": "Pulses",
    "6": "Bengal Gram",
    "7": "Red Gram",
    "8": "Black Gram",
    "9": "Green Gram",
    "114": "Horse Gram"
}

# District Mapping
district_map = {
    "556": "Bagalkot",
    "572": "Bangalore",
    "583": "Bangalore Rural",
    "565": "Bellary",
    "558": "Bidar",
    "557": "Bijapur",
    "578": "Chamarajanagar",
    "582": "Chikkaballapura",
    "570": "Chikmagalur",
    "566": "Chitradurga",
    "575": "Dakshina Kannada",
    "567": "Davanagere",
    "562": "Dharwad",
    "561": "Gadag",
    "579": "Gulbarga",
    "574": "Hassan",
    "564": "Haveri",
    "576": "Kodagu",
    "581": "Kolar",
    "560": "Koppal",
    "573": "Mandya",
    "577": "Mysore",
    "584": "Ramanagara",
    "559": "Raichur",
    "568": "Shimoga",
    "571": "Tumkur",
    "569": "Udupi",
    "563": "Uttara Kannada",
    "580": "Yadgir"
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/fetch_data", methods=["POST"])
def fetch_prices():
    data = request.json

    payload = {
        "state_id": "29",  # Karnataka
        "commodity_id": data["commodity_id"],
        "district_id": data["district_id"],
        "calculation_type": data["calculation_type"],
        "start_date": data["start_date"],
        "end_date": data["end_date"]
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        print(f"API Response for {commodity_map.get(data['commodity_id'])} in {district_map.get(data['district_id'])}")
        
        if "priceData" in result and isinstance(result["priceData"], list):
            price_data = result["priceData"]

            # Process and enrich data
            for entry in price_data:
                # Standardize date format
                entry["date"] = entry.get("month", entry.get("date", "N/A"))
                
                # Add commodity name
                entry["commodity_name"] = commodity_map.get(data["commodity_id"], "Unknown")
                
                # Add district name
                entry["district_name"] = district_map.get(data["district_id"], "Unknown")
                
                # Handle potential missing values
                for price_key in ["avg_min_price", "avg_max_price", "avg_modal_price"]:
                    if price_key not in entry or entry[price_key] is None:
                        entry[price_key] = "0.00"

            # Sort data by date (newest first for daily, chronologically for monthly)
            if data["calculation_type"] == "daily":
                # For daily data, sort by date descending and limit to 20 entries
                try:
                    price_data = sorted(
                        price_data, 
                        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d") if "-" in x["date"] else datetime.now(),
                        reverse=True
                    )[:20]
                except (ValueError, TypeError):
                    # If date parsing fails, use basic sorting
                    price_data = sorted(price_data, key=lambda x: x["date"], reverse=True)[:20]
            else:
                # For monthly data, try to sort chronologically
                try:
                    price_data = sorted(
                        price_data,
                        key=lambda x: datetime.strptime(x["date"], "%b %Y") if " " in x["date"] else datetime.now()
                    )
                except (ValueError, TypeError):
                    # If parsing fails, use the data as is
                    pass

            return jsonify(price_data)
        else:
            return jsonify({"error": "No price data found for the selected criteria."})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"})
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid response from API server."})
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"})

# Add this new endpoint to your Flask app
@app.route("/get_weather", methods=["POST"])
def get_weather():
    data = request.json
    lat = data.get("lat")
    lon = data.get("lon")
    
    # Weather API configuration - keep API key on server side for security
    weather_api_key = "4e3dc91be1a4e75ccf8851a5b8532b00"  # Replace with your valid API key
    
    # Using OpenWeatherMap API
    weather_api_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={weather_api_key}"
    
    try:
        response = requests.get(weather_api_url)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        weather_data = response.json()
        
        print(f"Weather API response for coordinates {lat}, {lon}:", weather_data)
        return jsonify(weather_data)
        
    except requests.exceptions.RequestException as e:
        print(f"Weather API request failed: {str(e)}")
        return jsonify({"error": f"Could not fetch weather data: {str(e)}"})
    except Exception as e:
        print(f"Unexpected error in weather API: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

