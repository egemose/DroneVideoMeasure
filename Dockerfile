FROM python:3.8 as base
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - 
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs
RUN rm -rf /var/lib/apt/lists/*

FROM base
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY ./package.json /package.json
RUN npm install
COPY . /app
RUN chmod u+x ./entrypoint.sh
RUN mkdir data

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD gunicorn -b 0.0.0.0:5000 -k gevent -t 10000 "app:app"
