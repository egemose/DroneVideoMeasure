FROM jjanzic/docker-python3-opencv
MAINTAINER Henrik Dyrberg Egemose <hesc@mmmi.sdu.dk>

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
&& rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
RUN mkdir data

EXPOSE 5000

CMD gunicorn -b 0.0.0.0:5000 -k gevent -t 10000 "app:app"
