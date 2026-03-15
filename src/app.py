"""
KU Parking Web App - Sprint 2
Authors: K Li, Joshua Welicky
Created February 8th, 2026
Main driver behind Parking Lot app functionality.
Follow the instructions below to run the app.
Sprint 2: Decision logic moved to AvailabilityService for centralized availability decision making.
Sprint 2: Strip down server app to leverage the new Python backend. This listens for requests, passes parameters to the LotController, and sends the results.
Run instructions (Local):
    0. CHECK THE IN-LINE COMMENTS(import statement AND the if __name__ == 'main' segment)
    1. Install Flask: pip install flask
    2. Run: python app.py
    3. Open browser: http://192.168.1.124:8080
Deploy instructions:
    1. Install fly.io: powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"   (for windows)
    2. Run fly.deploy (and pray)

To stop the application:
    - In the terminal window where the app is running, press Ctrl + C
    - If the terminal window is closed, use PowerShell: Get-Process python* | Stop-Process -Force
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
#USE FOR LOCAL TESTING
#from services.LotController import LotController
'''
READ ME READ ME DON'T SCROLL PAST OR YOU'LL BREAK SOMETHING!!!!!!!!!!!!!!!
'''
#USE FOR DEPLOYMENT
from src.services.LotController import LotController

app = Flask(__name__)

# Initialize AvailabilityService for centralized decision making
lot_control = LotController()

# Get the absolute path to the app directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, 'data', 'lots.json')


@app.route('/')
def index():
    # Get current time in HH:MM format
    current_time = datetime.now(ZoneInfo("America/Chicago")).strftime('%H:%M')
    # Get current day of week (Mon, Tue, Wed, etc.)
    current_day = datetime.now().strftime('%a')  # Returns Mon, Tue, Wed, etc.
    return render_template('index.html', current_time=current_time, current_day=current_day)


# 🔹 Now accepts permit/day/time and returns availability using AvailabilityService
@app.route('/api/lots')
def get_lots():
    try:
        #lots = load_lots()
        permit = request.args.get("permit", "NONE")
        day = request.args.get("day", "Mon")
        time = request.args.get("time", "09:00")

        #Let the Backend do the work.
        lots = lot_control.get_lots(permit, day, time)
        
        #JSONIFY works best if the Lot instances are actually dictionaries.
        return jsonify([lot.json_dictionary() for lot in lots])

    except Exception as e:
        print(f"[ERROR] Failed to get lots: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/lots/<lot_id>/report', methods=['POST'])
def report_special_restriction(lot_id):
    try:
        data = request.get_json(force=True)
        description = data.get('description', '').strip()

        '''
        if not description:
            return jsonify({'error': 'description is required'}), 400
        '''

        start_str = data.get('start')
        end_str = data.get('end')

        start_datetime = None
        end_datetime = None

        if start_str:
            try:
                start_datetime = datetime.fromisoformat(start_str)
            except ValueError:
                return jsonify({'error': 'start must be ISO format datetime'}), 400

        if end_str:
            try:
                end_datetime = datetime.fromisoformat(end_str)
            except ValueError:
                return jsonify({'error': 'end must be ISO format datetime'}), 400

        report = lot_control.report_special_restriction(lot_id, description, start_datetime, end_datetime)
        print(f"[INFO] special restriction reported for {lot_id}: {report.special_restriction}")

        return jsonify({'status': 'ok'}), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"[ERROR] Failed to report restriction: {e}")
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
