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

COPY ue.py /app/

EXPOSE 80/tcp

CMD ["python3", "ue.py"]
