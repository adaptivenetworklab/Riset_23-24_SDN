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
