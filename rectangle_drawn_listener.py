#listen for an event (rectangle being drawn) and return results (rectangle coordinates) when called
#Chantel Williams
#October 2024


# import json
from subprocess import Popen, PIPE, TimeoutExpired
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) #allows requests from any origin


@app.route('/process-rectangle', methods=['POST'])
# def catch_all(path):
#     return render_template("index.html")

def process_rectangle():
    try:
        #Get the JSON data from the request
        data = request.get_json()
        if not data:
            raise ValueError("No JSON payload provided")
        coordinates = data.get("coordinates")

        # Trigger the python Script (NDVI_Calculations) using the received coordinates
        # Pass this data to your Python script with environment variables
        result = Popen(["python", "-u", "NDVI_Calculations.py", coordinates], stdout=PIPE, stderr=PIPE)
        #Option 1: read each line of result
        # for line in iter(result.stdout.readline, ''):
        #     value = line.rstrip() #+ <br>
        #     output.append(value)
        #     print(value)
        #     # if value == b'':
        #     #     output.append(value)
        #     #     print(value)
        #     # else:
        #     #     print(value)
        #     #     # break
        #Option 2: use communicate()
        try:
            outs, errs = result.communicate()
            # outs, errs = result.communicate(timeout=500)
            #note: time should be longer to account for download times.
            #TODO: add a waiting bar and time counter to webpage and explaining what's happinging, downloading, process, etc, send results to an email?
            #format outs
            output = outs.decode("utf-8").split('\r')[0]


        except TimeoutExpired:
            result.kill()
            outs, errs = result.communicate()
            output = outs, errs



    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500
    return jsonify({f'output': str(output), 'status': 'success'}), 200
    # return jsonify({'message': 'Rectangle processed successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5174)
