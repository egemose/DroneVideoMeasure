FROM jjanzic/docker-python3-opencv

WORKDIR /app
COPY . /app

RUN apt-get update && \
    apt-get install -y ffmpeg

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--log-level=debug", "-k gevent", "app:app"]
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "--log-level=debug", "app:app"]
