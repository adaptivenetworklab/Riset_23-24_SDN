FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && pip3 install ryu

WORKDIR /app

COPY controller.py /app/

EXPOSE 6633 8080

CMD ["ryu-manager", "controller.py"]
