FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# copy ONLY backend contents
COPY . /app/

# install from pyproject.toml
RUN pip install --upgrade pip setuptools wheel && pip install .

EXPOSE 10000
