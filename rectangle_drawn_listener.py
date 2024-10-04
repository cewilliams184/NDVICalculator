#listen for an event (rectangle being drawn) and return results (rectangle coordinates) when called
#Chantel Williams
#October 2024


import json
from subprocess import Popen, PIPE
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) #allows requests from any origin


@app.route('/process-rectangle', methods=['POST'])

def process_rectangle():
    try:
        #Get the JSON data from the request
        data = request.get_json()
        if not data:
            raise ValueError("No JSON payload provided")
        coordinates = data.get("coordinates")

        # Trigger the python Script (NDVI_Calculations) using the received coordinates
        # Pass this data to your Python script with environment variables
        result = Popen(["python", "-u", "NDVI_Calculations.py"], stdout=PIPE, stderr=PIPE)
        output = []
        for line in iter(result.stdout.readline, ''):
            value = line.rstrip() #+ <br>
            if value != b'':
                output.append(value)
                print(value)
            else:
                break

        return jsonify({'output': str(output), 'status': 'success'}), 200
        # return jsonify({'message': 'Rectangle processed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5174)
