#FROM harshpreets63/random:simple
FROM python:3.9.2

WORKDIR /usr/src/app

COPY . .

RUN pip3 install -r requirements.txt

CMD gunicorn app:app & python3 -m bot
