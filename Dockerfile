FROM python:3

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV DISPLAY=:99

# Install apt dependencies
RUN apt update

# Install requirements
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /app
ENTRYPOINT python main.py -c dd_cost_exporter_config.yaml
