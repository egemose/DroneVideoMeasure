FROM python:3.13-slim

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get --no-install-recommends install -y ffmpeg npm && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./package.json /package.json
RUN npm install && npm cache clean --force

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN pip install --no-cache-dir -e .[dev]

RUN chmod u+x ./entrypoint.sh
RUN mkdir /app_data

EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "-b 0.0.0.0:5000", "-k gevent", "-t 10000", "'dvm:app'"]
