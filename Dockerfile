FROM jjanzic/docker-python3-opencv
MAINTAINER Henrik Dyrberg Egemose <hesc@mmmi.sdu.dk>

RUN apt-get update && apt-get install -y \
    ffmpeg \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN mkdir data

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "-k", "gevent", "-t", "10000", "app:app"]
