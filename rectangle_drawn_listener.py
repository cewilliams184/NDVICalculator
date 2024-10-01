#listen for an event (rectangle being drawn) and return results (rectangle coordinates) when called
#Chantel Williams
#October 2024

import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process-rectangle', method=['POST'])
def process_rectangle():
    try:
        #Get the JSON data from the request
        data = request.get_json()

        # Trigger the python Script (NDVI_Calculations) using the received coordinates
        # Pass this data to your Python script with environment variables
        result = subprocess.run(['python3', r'C:\Users\cewil\Documents\GitHub\NDVICalculator\NDVI_Calculations.py', data], capture_output=True, text=True)
        return jsonify({'output': result.stdout, 'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)