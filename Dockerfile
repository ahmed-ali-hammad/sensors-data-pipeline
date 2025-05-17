FROM python:3.13

RUN apt update \
    && apt install -y pgcli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

RUN pip install --upgrade pip && pip install pipenv
ENV PIPENV_CUSTOM_VENV_NAME="sensors-data-pipeline"
COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv install --dev