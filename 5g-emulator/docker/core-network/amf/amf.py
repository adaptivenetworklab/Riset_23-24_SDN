from flask import Flask, jsonify, request
import os
import json
import time
import threading
import socket

app = Flask(__name__)

# Store connected UEs and gNBs
connected_gnbs = {}
registered_ues = {}

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'component': 'AMF',
        'connected_gnbs': len(connected_gnbs),
        'registered_ues': len(registered_ues)
    })

@app.route('/gnb/register', methods=['POST'])
def register_gnb():
    data = request.json
    gnb_id = data.get('gnb_id')
    if not gnb_id:
        return jsonify({'error': 'gnb_id is required'}), 400

    connected_gnbs[gnb_id] = {
        'ip': data.get('ip', '0.0.0.0'),
        'connected_at': time.time(),
        'status': 'connected'
    }
    return jsonify({'status': 'connected', 'gnb_id': gnb_id})

@app.route('/ue/register', methods=['POST'])
def register_ue():
    data = request.json
    imsi = data.get('imsi')
    gnb_id = data.get('gnb_id')

    if not imsi or not gnb_id:
        return jsonify({'error': 'imsi and gnb_id are required'}), 400

    if gnb_id not in connected_gnbs:
        return jsonify({'error': 'Unknown gNB'}), 404

    registered_ues[imsi] = {
        'gnb_id': gnb_id,
        'registered_at': time.time(),
        'status': 'registered'
    }
    return jsonify({'status': 'registered', 'imsi': imsi})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
