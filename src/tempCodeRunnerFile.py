
from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
# Support both: run from repo root (e.g. deploy) or from src/ (local: cd src && python app.py)
try:
    from src.services.LotController import LotController
except ModuleNotFoundError:
    from services.LotController import LotController

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

        #Let the Backend do the work.
        lots = lot_control.get_lots(permit, day, time)
        
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

        '''
        DESCRIPTION OPTIONAL
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

        # Default logic when user omits Description / Start / End (implement here or in lot_control):
        # - No start/end (both None) → restriction expires after 24 hours (Req 19).
        # - Start/end span > 48 hours → treat as 24-hour restriction from report time (Req 20).
        # - Empty description → use e.g. default text like "Special restriction reported" or leave empty.
       
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
