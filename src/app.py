"""
KU Parking Web App - Sprint 2
Authors: K Li
Created February 8th, 2026
Main driver behind Parking Lot app functionality.
Follow the instructions below to run the app.
Sprint 2: Decision logic moved to AvailabilityService for centralized availability decision making.
Run instructions:
    1. Install Flask: pip install flask
    2. Run: python app.py
    3. Open browser: http://192.168.1.124:8080

To stop the application:
    - In the terminal window where the app is running, press Ctrl + C
    - If the terminal window is closed, use PowerShell: Get-Process python* | Stop-Process -Force
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from services.availabilityservice import AvailabilityService

app = Flask(__name__)

# Initialize AvailabilityService for centralized decision making
availability_service = AvailabilityService()

# Get the absolute path to the app directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, 'data', 'lots.json')

# Load parking lots data
def load_lots():
    """Load parking lots from data/lots.json"""
    print(f"[DEBUG] Loading lots from: {DATA_FILE}")
    print(f"[DEBUG] File exists: {os.path.exists(DATA_FILE)}")
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            lots_data = json.load(f)
            print(f"[DEBUG] Successfully loaded {len(lots_data)} lots from JSON")
            return lots_data
    except FileNotFoundError:
        print(f"[ERROR] File not found: {DATA_FILE}")
        raise
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error: {e}")
        raise


@app.route('/')
def index():
    # Get current time in HH:MM format
    current_time = datetime.now().strftime('%H:%M')
    # Get current day of week (Mon, Tue, Wed, etc.)
    current_day = datetime.now().strftime('%a')  # Returns Mon, Tue, Wed, etc.
    return render_template('index.html', current_time=current_time, current_day=current_day)


# 🔹 Helper function to add minutes to a time string
def add_minutes_to_time(time_hhmm, minutes):
    """Add minutes to a time in HH:MM format"""
    hours, mins = map(int, time_hhmm.split(":"))
    total_minutes = hours * 60 + mins + minutes
    # Handle day wraparound
    total_minutes = total_minutes % (24 * 60)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


# 🔹 Now accepts permit/day/time and returns availability using AvailabilityService
@app.route('/api/lots')
def get_lots():
    try:
        lots = load_lots()

        permit = request.args.get("permit", "NONE")
        day = request.args.get("day", "Mon")
        time = request.args.get("time", "09:00")

        # Compute availability at current time and in 1 hour
        time_in_one_hour = add_minutes_to_time(time, 60)

        # Use AvailabilityService for centralized decision making
        for lot in lots:
            lot["available"] = availability_service.is_lot_available(lot, permit, day, time)
            lot["available_in_one_hour"] = availability_service.is_lot_available(
                lot, permit, day, time_in_one_hour
            )

        print(f"[DEBUG] Returning {len(lots)} lots to client")
        print(f"[DEBUG] Permit: {permit}, Day: {day}, Time: {time}, Time+1h: {time_in_one_hour}")
        return jsonify(lots)
    
    except Exception as e:
        print(f"[ERROR] Failed to get lots: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    '''
    USE BOTTOM TWO LINES FOR PUBLIC DEPLOYMENT.
    Fly.io demands port 8080 by default (no need to configure another).
    Doesn't want 127.0.0.1
    '''
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    '''
    FOR LOCAL TESTING/DEPLOYMENT: 
    Comment out the two lines above and uncomment
    the line below.
    Access using http://127.0.0.1:5000
    '''
    #app.run(debug=True, host='127.0.0.1', port=5000)
