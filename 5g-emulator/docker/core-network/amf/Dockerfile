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
