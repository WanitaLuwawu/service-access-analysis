# server.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import main as analysis
import os

app = Flask(__name__)
CORS(app)


@app.route('/analyse', methods=['POST'])
def analyse():
    data = request.json
    region = data['region']
    buffer = data['buffer']
    outputs = data.get('outputs', ['png', 'html'])

    try:
        result = analysis.run(region, buffer, outputs)
        return jsonify({'status': 'ok', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/view/<path:filename>')
def view_file(filename):
    return send_file(os.path.abspath(filename), as_attachment=False)


if __name__ == '__main__':
    app.run(port=5000)