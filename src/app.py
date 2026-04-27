"""
KU Parking Web App
Authors: K Li, Joshua Welicky, Mark Kitchin, Evans Chigweshe
Created February 8th, 2026
Main driver behind Parking Lot app functionality.
Follow the instructions below to run the app.
Sprint 2: Decision logic moved to AvailabilityService for centralized availability decision making.
Sprint 2: Strip down server app to leverage the new Python backend. This listens for requests, passes parameters to the LotController, and sends the results.
Sprint 3: Add functionality to receive special reports (Mark). Tweak to suit the requirements(Josh).
sprint 4: added permit_description route to handle the  nativation to the Permit Description page(Evans).
sprint 5: added censoring to special restriction reports. 4/11 (Josh)
sprint 6: Tweak to special restrictions and addition of dispute handler (Josh and Mark)
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
from psycopg2.pool import ThreadedConnectionPool
# Support both: run from repo root (e.g. deploy) or from src/ (local: cd src && python app.py)
try:
    from src.services.LotController import LotController
    from src.services.censor import Censor
except ModuleNotFoundError:
    from services.LotController import LotController
    from services.censor import Censor

app = Flask(__name__)


# Connect to the database
CONN_STR = "postgresql://neondb_owner:npg_Te8KnPXpq9Yr@ep-lingering-lab-aevc8697-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

db_pool = ThreadedConnectionPool(
    minconn = 1,
    maxconn=10,
    dsn=CONN_STR
)

# Initialize AvailabilityService for centralized decision making
lot_control = LotController(db_pool)

# Initialize profanity-censoring module.
censor  = Censor()

# Get the absolute path to the app directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, 'data', 'lots.json')


@app.route('/')
def index():
    now_chi = datetime.now(ZoneInfo("America/Chicago"))
    current_time = now_chi.strftime('%H:%M')
    current_day = now_chi.strftime('%a')  # Returns Mon, Tue, Wed, etc.
    current_date = now_chi.strftime('%Y-%m-%d')
    return render_template('index.html', current_time=current_time, current_day=current_day, current_date=current_date)

# Route to display the parking permit description page
@app.route('/permit_description')
def permit_description():
    return render_template('permit_description.html')


# 🔹 Now accepts permit/day/time and returns availability using AvailabilityService
@app.route('/api/lots')
def get_lots():
    try:
        #lots = load_lots()
        permit = request.args.get("permit", "NONE")
        day = request.args.get("day", "Mon")
        time = request.args.get("time", "09:00")
        date_raw = request.args.get("date", "").strip()
        view_date = None
        if date_raw:
            try:
                datetime.strptime(date_raw, "%Y-%m-%d")
                view_date = date_raw
            except ValueError:
                view_date = None

        #Let the Backend do the work.
        lots = lot_control.get_lots(permit, day, time, view_date=view_date)
        
        #JSONIFY works best if the Lot instances are actually dictionaries.
        return jsonify([lot.json_dictionary() for lot in lots])

    except Exception as e:
        print(f"[ERROR] Failed to get lots: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Accepts HTTP POST messages reporting a special restriction. Passes information to LotController
@app.route('/api/lots/<lot_id>/report', methods=['POST'])
def report_special_restriction(lot_id):
    try:
        data = request.get_json(force=True)
        description = data.get('description', '').strip()

        #censor the description immediately.
        description = censor.censor(description)

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

        # Default logic when user omits Description / Start / End (implement here or in lot_control):
        # - No start/end (both None) → restriction expires after 24 hours (Req 19).
        # - Start/end span > 48 hours → treat as 24-hour restriction from report time (Req 20).
        # - Empty description → use e.g. default text like "Special restriction reported" or leave empty.
       
        report = lot_control.report_special_restriction(lot_id, description, start_datetime, end_datetime)
        print(f"[INFO] special restriction reported for {lot_id}: {report}")

        return jsonify({'status': 'ok'}), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"[ERROR] Failed to report restriction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    



@app.route('/api/restrictions')
def get_special_restrictions():
    try:
        id = request.args.get("lot_id", "NONE")
        time = request.args.get("time", "09:00")
        date_raw = request.args.get("date", "").strip()
        view_date = None
        if date_raw:
            try:
                datetime.strptime(date_raw, "%Y-%m-%d")
                view_date = date_raw
            except ValueError:
                view_date = None

        specs = lot_control.lookup_restrictions(id, time, view_date)
        return jsonify(specs)
    except Exception as e:
        print(f"[ERROR] Failed to get restrictions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/dispute', methods=['POST'])
def dispute_restriction():
    try:
        data = request.get_json()
        if not data or 'report_id' not in data:
            return jsonify({'error': 'Missing report_id'}), 400
        
        report_id = data['report_id']
        if not isinstance(report_id, int) or report_id <= 0:
            return jsonify({'error': 'Invalid report_id'}), 400
        
        deleted = lot_control.dispute(report_id)
        
        if deleted:
            return jsonify({'status': 'deleted', 'message': 'Restriction removed due to multiple disputes'}), 200
        else:
            return jsonify({'status': 'incremented', 'message': 'Dispute count increased'}), 200
            
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 404
    except Exception as e:
        print(f"[ERROR] Failed to process dispute: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500


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
    Access using http://127.0.0.1:5000]
    '''
    #app.run(debug=True, host='127.0.0.1', port=5000)
