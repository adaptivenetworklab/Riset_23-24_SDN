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
