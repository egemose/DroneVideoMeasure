FROM python:3.8 as base
RUN apt-get update 
RUN apt-get install -y curl 
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - 
RUN apt-get install -y ffmpeg 
RUN apt-get install -y nodejs
RUN rm -rf /var/lib/apt/lists/*

FROM base
WORKDIR /app
COPY ./package.json /package.json
RUN npm install
COPY ./pyproject.toml /app/pyproject.toml
COPY . /app
RUN pip install -e .
RUN chmod u+x ./entrypoint.sh
RUN mkdir /app_data

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD gunicorn -b 0.0.0.0:5000 -k gevent -t 10000 "app:app"
