FROM python:3.6 as base
RUN apt-get update && apt-get install -y \
    ffmpeg \
&& rm -rf /var/lib/apt/lists/*

FROM base
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
RUN chmod u+x ./entrypoint.sh
RUN mkdir data

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD gunicorn -b 0.0.0.0:5000 -k gevent -t 10000 "app:app"
