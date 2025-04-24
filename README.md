# 5G Network Emulator with SDN and Docker by Messi⚽
This step-by-step guide will walk you through building a simplified 5G messi network emulator using Docker and SDN
## Part 1: Environment Setup
### 1. Install Prerequisites
#### #Install Docker and Docker Compose <br/>
If you have Installed the `containerd` or `runc` previously, uninstall them to avoid conflicts with the versions bundled with Docker Engine. <br/>

Run the following command to uninstall all conflicting packages:
```
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
```

1. Setup Docker's `apt` repository.
```
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```
2. Install the Docker Packages. <br/>
To install the latest version, run:
```
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
3. Verify that the installation is successfully by running the `hello-world` image:
```
sudo docker run hello-world
```
This command downloads a test image and runs it in a container. When the container runs, it prints a confirmation message and exits.

You have now successfullly installed and started Docker Engine.
> Tip
>
> Receiving errors when trying to run without root?
>
> The `docker` user group exists but contains no users, which is why you’re required to use `sudo` to run Docker commands. Continue to [Linux postinstall](https://docs.docker.com/engine/install/linux-postinstall) to allow non-privileged users to run Docker commands and for other optional configuration steps.
>
### 2. Create Project Structure
#### #Create Directory
This is the project root directory where your application develop<br/>

Run the following commands.
```
mkdir 5g-emulator
cd 5g-emulator
```

Create main directories
```
mkdir -p docker/core-network/{amf,smf,upf,nrf,pcf,ausf,udm}
mkdir -p docker/ran
mkdir -p docker/ue
mkdir -p app/{css,js,assets}
```

## Part 2: Network Component Development
### 1. Create 5G Core Network Components
- AMF (Access and Mobility Management Function)
  - Dockerfile (docker/core-network/amf/Dockerfile)\
    Create Docker File
    ```
    touch Dockerfile
    ```
    Edit Docker File
    ```
    nano Dockerfile
    ```
    Dockerfile Configuration
    ```
    FROM ubuntu:20.04
  
    RUN apt-get update && apt-get install -y \
        iproute2 \
        iputils-ping \
        net-tools \
        iptables \
        tcpdump \
        python3 \
        python3-pip \
        && pip3 install flask
  
    WORKDIR /app
  
    COPY amf.py /app/
  
    EXPOSE 38412/sctp 80/tcp
  
    CMD ["python3", "amf.py"]
    ```
  - Python Script (docker/core-network/amf/amf.py)
    Create Python File
    ```
    touch amf.py
    ```
    Edit Python File
    ```
    nano amf.py
    ```
    Python File Configuration
    ```
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
    ```
- SMF (Session Management Function)
  - Dockerfile (docker/core-network/smf/Dockerfile)\
    Create Docker File
    ```
    touch Dockerfile
    ```
    Edit Docker File
    ```
    nano Dockerfile
    ```
    Dockerfile Configuration
    ```
    FROM ubuntu:20.04
    
    RUN apt-get update && apt-get install -y \
        iproute2 \
        iputils-ping \
        net-tools \
        iptables \
        tcpdump \
        python3 \
        python3-pip \
        && pip3 install flask requests
    
    WORKDIR /app
    
    COPY smf.py /app/
    
    EXPOSE 80/tcp
    
    CMD ["python3", "smf.py"]
    ```
  - Python Script (docker/core-network/smf/smf.py)
    Create Python File
    ```
    touch smf.py
    ```
    Edit Python File
    ```
    nano smf.py
    ```
    Python File Configuration
    ```
    from flask import Flask, jsonify, request
    import os
    import json
    import time
    import threading
    import socket
    import requests
    
    app = Flask(__name__)
    
    # Configuration
    nrf_address = os.environ.get('NRF_ADDRESS', 'nrf')
    upf_address = os.environ.get('UPF_ADDRESS', 'upf')
    
    # Store session contexts
    session_contexts = {}
    registered = False
    
    # Register with NRF on startup
    def register_with_nrf():
        global registered
        while not registered:
            try:
                response = requests.post(f'http://{nrf_address}/nf/register', json={
                    'nf_type': 'smf',
                    'nf_id': socket.gethostname(),
                    'status': 'active',
                    'services': ['session-management'],
                    'api_prefix': f'http://{socket.gethostname()}'
                })
                if response.status_code == 200:
                    print(f"Successfully registered with NRF: {response.json()}")
                    registered = True
                else:
                    print(f"Failed to register with NRF: {response.text}")
                    time.sleep(5)  # Retry after 5 seconds
            except Exception as e:
                print(f"Error registering with NRF: {str(e)}")
                time.sleep(5)  # Retry after 5 seconds
    
    @app.route('/status', methods=['GET'])
    def get_status():
        return jsonify({
            'status': 'running',
            'component': 'SMF',
            'registered_with_nrf': registered,
            'active_sessions': len(session_contexts)
        })
    
    @app.route('/session/create', methods=['POST'])
    def create_session():
        data = request.json
        supi = data.get('supi')
        dnn = data.get('dnn', 'internet')
    
        if not supi:
            return jsonify({'error': 'supi is required'}), 400
    
        # Create session ID
        session_id = f'{supi}-{int(time.time())}'
    
        # Store session context
        session_contexts[session_id] = {
            'supi': supi,
            'dnn': dnn,
            'created_at': time.time(),
            'status': 'created'
        }
    
        # Request IP address allocation from UPF
        try:
            response = requests.post(f'http://{upf_address}/ip/allocate', json={
                'session_id': session_id,
                'supi': supi
            })
    
            if response.status_code == 200:
                ip_data = response.json()
                session_contexts[session_id]['ip_address'] = ip_data.get('ip_address')
                session_contexts[session_id]['status'] = 'active'
    
                return jsonify({
                    'session_id': session_id,
                    'ip_address': ip_data.get('ip_address'),
                    'status': 'active'
                })
            else:
                session_contexts[session_id]['status'] = 'failed'
                return jsonify({'error': f"UPF IP allocation failed: {response.text}"}), 500
    
        except Exception as e:
            session_contexts[session_id]['status'] = 'failed'
            return jsonify({'error': f"UPF communication error: {str(e)}"}), 500
    
    @app.route('/session/<session_id>', methods=['GET'])
    def get_session(session_id):
        if session_id not in session_contexts:
            return jsonify({'error': 'Session not found'}), 404
    
        return jsonify(session_contexts[session_id])
    
    @app.route('/session/<session_id>/release', methods=['POST'])
    def release_session(session_id):
        if session_id not in session_contexts:
            return jsonify({'error': 'Session not found'}), 404
    
        # Request IP address release from UPF
        try:
            response = requests.post(f'http://{upf_address}/ip/release', json={
                'session_id': session_id
            })
    
            # Mark session as released regardless of UPF response
            session_contexts[session_id]['status'] = 'released'
            session_contexts[session_id]['released_at'] = time.time()
    
            return jsonify({
                'session_id': session_id,
                'status': 'released'
            })
        except Exception as e:
            return jsonify({'error': f"UPF communication error: {str(e)}"}), 500
    
    if __name__ == '__main__':
        # Register with NRF on startup
        threading.Thread(target=register_with_nrf, daemon=True).start()
    
        # Start API server
        app.run(host='0.0.0.0', port=80)    
    ```
- UPF (User Plane Function)
  - Dockerfile (docker/core-network/upf/Dockerfile)\
    Create Docker File
    ```
    touch Dockerfile
    ```
    Edit Docker File
    ```
    nano Dockerfile
    ```
    Dockerfile Configuration
    ```
    FROM ubuntu:20.04
    
    RUN apt-get update && apt-get install -y \
        iproute2 \
        iputils-ping \
        net-tools \
        iptables \
        tcpdump \
        python3 \
        python3-pip \
        && pip3 install flask requests
    
    WORKDIR /app
    
    COPY upf.py /app/
    
    EXPOSE 80/tcp
    
    CMD ["python3", "upf.py"]
    ```
  - Python Script (docker/core-network/upf/upf.py)
    Create Python File
    ```
    touch upf.py
    ```
    Edit Python File
    ```
    nano upf.py
    ```
    Python File Configuration
    ```
    from flask import Flask, jsonify, request
    import os
    import json
    import time
    import threading
    import socket
    import requests
    import random
    
    app = Flask(__name__)
    
    # Configuration
    nrf_address = os.environ.get('NRF_ADDRESS', 'nrf')
    
    # IP address management
    ip_pool = {f"10.45.0.{i}": None for i in range(2, 254)}  # IP pool excluding .0, .1, .255
    allocated_ips = {}
    registered = False
    
    # Traffic statistics
    traffic_stats = {
        'packets_uplink': 0,
        'packets_downlink': 0,
        'bytes_uplink': 0,
        'bytes_downlink': 0
    }
    
    # Register with NRF on startup
    def register_with_nrf():
        global registered
        while not registered:
            try:
                response = requests.post(f'http://{nrf_address}/nf/register', json={
                    'nf_type': 'upf',
                    'nf_id': socket.gethostname(),
                    'status': 'active',
                    'services': ['user-plane'],
                    'api_prefix': f'http://{socket.gethostname()}'
                })
                if response.status_code == 200:
                    print(f"Successfully registered with NRF: {response.json()}")
                    registered = True
                else:
                    print(f"Failed to register with NRF: {response.text}")
                    time.sleep(5)  # Retry after 5 seconds
            except Exception as e:
                print(f"Error registering with NRF: {str(e)}")
                time.sleep(5)  # Retry after 5 seconds
    
    def find_available_ip():
        available_ips = [ip for ip, session_id in ip_pool.items() if session_id is None]
        if not available_ips:
            return None
        return random.choice(available_ips)
    
    @app.route('/status', methods=['GET'])
    def get_status():
        return jsonify({
            'status': 'running',
            'component': 'UPF',
            'registered_with_nrf': registered,
            'allocated_ips': len(allocated_ips),
            'available_ips': len([ip for ip, session_id in ip_pool.items() if session_id is None]),
            'traffic_stats': traffic_stats
        })
    
    @app.route('/ip/allocate', methods=['POST'])
    def allocate_ip():
        data = request.json
        session_id = data.get('session_id')
        supi = data.get('supi')
    
        if not session_id or not supi:
            return jsonify({'error': 'session_id and supi are required'}), 400
    
        if session_id in allocated_ips:
            return jsonify({
                'ip_address': allocated_ips[session_id],
                'status': 'already_allocated'
            })
    
        # Allocate IP from pool
        ip_address = find_available_ip()
        if not ip_address:
            return jsonify({'error': 'No IP addresses available in pool'}), 503
    
        # Update records
        ip_pool[ip_address] = session_id
        allocated_ips[session_id] = ip_address
    
        return jsonify({
            'ip_address': ip_address,
            'session_id': session_id,
            'supi': supi,
            'allocated_at': time.time()
        })
    
    @app.route('/ip/release', methods=['POST'])
    def release_ip():
        data = request.json
        session_id = data.get('session_id')
    
        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400
    
        if session_id not in allocated_ips:
            return jsonify({'error': 'Session ID not found in allocated IPs'}), 404
    
        # Release IP back to pool
        ip_address = allocated_ips[session_id]
        ip_pool[ip_address] = None
        del allocated_ips[session_id]
    
        return jsonify({
            'ip_address': ip_address,
            'session_id': session_id,
            'status': 'released',
            'released_at': time.time()
        })
    
    @app.route('/traffic/simulate', methods=['POST'])
    def simulate_traffic():
        data = request.json
        session_id = data.get('session_id')
        direction = data.get('direction', 'uplink')  # uplink or downlink
        bytes_count = data.get('bytes', 1024)
    
        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400
    
        if session_id not in allocated_ips:
            return jsonify({'error': 'Session ID not found in allocated IPs'}), 404
    
        # Update traffic statistics
        if direction == 'uplink':
            traffic_stats['packets_uplink'] += 1
            traffic_stats['bytes_uplink'] += bytes_count
        else:
            traffic_stats['packets_downlink'] += 1
            traffic_stats['bytes_downlink'] += bytes_count
    
        return jsonify({
            'session_id': session_id,
            'direction': direction,
            'bytes': bytes_count,
            'ip_address': allocated_ips[session_id],
            'processed_at': time.time(),
            'traffic_stats': traffic_stats
        })
    
    @app.route('/traffic/stats', methods=['GET'])
    def get_traffic_stats():
        return jsonify(traffic_stats)
    
    if __name__ == '__main__':
        # Register with NRF on startup
        threading.Thread(target=register_with_nrf, daemon=True).start()
    
        # Start API server
        app.run(host='0.0.0.0', port=80)
    ```
- NRF (Network Repository Function)
  - Dockerfile (docker/core-network/nrf/Dockerfile)\
    Create Docker File
    ```
    touch Dockerfile
    ```
    Edit Docker File
    ```
    nano Dockerfile
    ```
    Dockerfile Configuration
    ```
    FROM ubuntu:20.04
    
    RUN apt-get update && apt-get install -y \
        iproute2 \
        iputils-ping \
        net-tools \
        iptables \
        tcpdump \
        python3 \
        python3-pip \
        && pip3 install flask requests
    
    WORKDIR /app
    
    COPY nrf.py /app/
    
    EXPOSE 80/tcp
    
    CMD ["python3", "nrf.py"]
    ```
  - Python Script (docker/core-network/nrf/nrf.py)
    Create Python File
    ```
    touch nrf.py
    ```
    Edit Python File
    ```
    nano nrf.py
    ```
    Python File Configuration
    ```
    from flask import Flask, jsonify, request
    import os
    import json
    import time
    import threading
    import socket
    
    app = Flask(__name__)
    
    # Store registered NFs
    network_functions = {}
    heartbeat_timestamps = {}
    
    # NF health check thread
    def check_nf_health():
        while True:
            current_time = time.time()
            for nf_id, timestamp in list(heartbeat_timestamps.items()):
                # If no heartbeat for more than 30 seconds, mark as inactive
                if current_time - timestamp > 30:
                    if nf_id in network_functions:
                        network_functions[nf_id]['status'] = 'inactive'
                        print(f"NF {nf_id} marked as inactive due to missed heartbeats")
    
            # Sleep for 10 seconds before next check
            time.sleep(10)
    
    @app.route('/status', methods=['GET'])
    def get_status():
        active_nfs = sum(1 for nf in network_functions.values() if nf['status'] == 'active')
    
        return jsonify({
            'status': 'running',
            'component': 'NRF',
            'registered_nfs': len(network_functions),
            'active_nfs': active_nfs,
            'nf_types': list(set(nf['nf_type'] for nf in network_functions.values()))
        })
    
    @app.route('/nf/register', methods=['POST'])
    def register_nf():
        data = request.json
        nf_type = data.get('nf_type')
        nf_id = data.get('nf_id')
    
        if not nf_type or not nf_id:
            return jsonify({'error': 'nf_type and nf_id are required'}), 400
    
        # Register the network function
        network_functions[nf_id] = {
            'nf_type': nf_type,
            'nf_id': nf_id,
            'status': data.get('status', 'active'),
            'services': data.get('services', []),
            'api_prefix': data.get('api_prefix', ''),
            'registered_at': time.time()
        }
    
        # Update heartbeat timestamp
        heartbeat_timestamps[nf_id] = time.time()
    
        return jsonify({
            'nf_id': nf_id,
            'status': 'registered',
            'timestamp': time.time()
        })
    
    @app.route('/nf/update', methods=['PUT'])
    def update_nf():
        data = request.json
        nf_id = data.get('nf_id')
    
        if not nf_id:
            return jsonify({'error': 'nf_id is required'}), 400
    
        if nf_id not in network_functions:
            return jsonify({'error': 'Network function not found'}), 404
    
        # Update the network function
        for key, value in data.items():
            if key != 'nf_id' and key != 'registered_at':
                network_functions[nf_id][key] = value
    
        # Update heartbeat timestamp
        heartbeat_timestamps[nf_id] = time.time()
    
        return jsonify({
            'nf_id': nf_id,
            'status': 'updated',
            'timestamp': time.time()
        })
    
    @app.route('/nf/heartbeat', methods=['POST'])
    def nf_heartbeat():
        data = request.json
        nf_id = data.get('nf_id')
    
        if not nf_id:
            return jsonify({'error': 'nf_id is required'}), 400
    
        if nf_id not in network_functions:
            return jsonify({'error': 'Network function not found'}), 404
    
        # Update heartbeat timestamp
        heartbeat_timestamps[nf_id] = time.time()
    
        # If NF was inactive, mark as active again
        if network_functions[nf_id]['status'] == 'inactive':
            network_functions[nf_id]['status'] = 'active'
    
        return jsonify({
            'nf_id': nf_id,
            'status': 'heartbeat_acknowledged',
            'timestamp': time.time()
        })
    
    @app.route('/nf/deregister', methods=['POST'])
    def deregister_nf():
        data = request.json
        nf_id = data.get('nf_id')
    
        if not nf_id:
            return jsonify({'error': 'nf_id is required'}), 400
    
        if nf_id not in network_functions:
            return jsonify({'error': 'Network function not found'}), 404
    
        # Remove the network function
        del network_functions[nf_id]
    
        # Remove heartbeat timestamp
        if nf_id in heartbeat_timestamps:
            del heartbeat_timestamps[nf_id]
    
        return jsonify({
            'nf_id': nf_id,
            'status': 'deregistered',
            'timestamp': time.time()
        })
    
    @app.route('/nf/discover', methods=['GET'])
    def discover_nf():
        nf_type = request.args.get('nf_type')
    
        if not nf_type:
            return jsonify({'error': 'nf_type query parameter is required'}), 400
    
        # Find all active NFs of the requested type
        matching_nfs = [
            nf for nf in network_functions.values()
            if nf['nf_type'] == nf_type and nf['status'] == 'active'
        ]
    
        if not matching_nfs:
            return jsonify({'error': f'No active network functions of type {nf_type} found'}), 404
    
        return jsonify({
            'nf_type': nf_type,
            'network_functions': matching_nfs,
            'timestamp': time.time()
        })
    
    @app.route('/nf/list', methods=['GET'])
    def list_nfs():
        # Optional filter by type
        nf_type = request.args.get('nf_type')
    
        if nf_type:
            filtered_nfs = {
                nf_id: nf for nf_id, nf in network_functions.items()
                if nf['nf_type'] == nf_type
            }
            return jsonify(filtered_nfs)
    
        return jsonify(network_functions)
    
    if __name__ == '__main__':
        # Start health check thread
        health_thread = threading.Thread(target=check_nf_health, daemon=True)
        health_thread.start()
    
        # Start API server
        app.run(host='0.0.0.0', port=80)   
    ```
### 2. Create Radio Access Network (RAN) Component
