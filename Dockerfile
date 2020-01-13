FROM python:3.5

WORKDIR /dependency

COPY ./crawler/requirements.txt requirements.txt

RUN pip3 install -r requirements.txt
