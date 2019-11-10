FROM ubuntu:18.04

RUN apt update && apt install sudo python3-pip git -y

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN set -ex && mkdir /app

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY src src