"""
KU Parking Web App - Sprint 1
Run instructions:
    1. Install Flask: pip install flask
    2. Run: python app.py
    3. Open browser: http://127.0.0.1:5000/

To stop the application:
    - In the terminal window where the app is running, press Ctrl + C
    - If the terminal window is closed, use PowerShell: Get-Process python* | Stop-Process -Force
"""

from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Load parking lots data
def load_lots():
    """Load parking lots from data/lots.json"""
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'lots.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/lots')
def get_lots():
    """API endpoint to return all parking lots"""
    lots = load_lots()
    return jsonify(lots)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
