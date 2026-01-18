FROM python:3.14-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY bot/ bot/
COPY db/ db/
COPY fill_form_razer_async.py .
COPY submit_photo_async.py .
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN playwright install --with-deps
