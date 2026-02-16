"""
KU Parking Web App - Sprint 1
Authors: K Li
Created February 8th, 2026
Main driver behind Parking Lot app functionality.
Follow the instructions below to run the app.
In the next sprint, decision logic will be moved here, and there will be public accessibility for the app
Run instructions:
    1. Install Flask: pip install flask
    2. Run: python app.py
    3. Open browser: http://127.0.0.1:5000/

To stop the application:
    - In the terminal window where the app is running, press Ctrl + C
    - If the terminal window is closed, use PowerShell: Get-Process python* | Stop-Process -Force
"""

from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

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


# 🔹 Availability logic MOVED from map.js to backend
def is_lot_available(lot, permit, day, time_hhmm):
    lot_type = lot["type"].upper()

    hours, minutes = map(int, time_hhmm.split(":"))
    time_in_minutes = hours * 60 + minutes

    # Yellow lot logic
    if lot_type == "YELLOW":

        if permit == "YELLOW":
            return True

        if permit == "NONE":
            is_weekday = day in ["Mon", "Tue", "Wed", "Thu", "Fri"]

            # Block 8:00–16:59 on weekdays
            if is_weekday and 480 <= time_in_minutes < 1020:
                return False

            return True

        return False

    # Red lot logic
    if lot_type == "RED":
        return permit == "RED"

    # Blue lot logic
    if lot_type == "BLUE":
        return permit == "BLUE"

    # Green lot logic
    if lot_type == "GREEN":
        return permit == "GREEN"

    return False


@app.route('/')
def index():
    return render_template('index.html')


# 🔹 Now accepts permit/day/time and returns availability
@app.route('/api/lots')
def get_lots():
    try:
        lots = load_lots()

        permit = request.args.get("permit", "NONE")
        day = request.args.get("day", "Mon")
        time = request.args.get("time", "09:00")

        for lot in lots:
            lot["available"] = is_lot_available(lot, permit, day, time)

        print(f"[DEBUG] Returning {len(lots)} lots to client")
        return jsonify(lots)
    
    except Exception as e:
        print(f"[ERROR] Failed to get lots: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
