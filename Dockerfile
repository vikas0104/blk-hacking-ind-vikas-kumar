# docker build -t blk-hacking-ind-vikas-kumar .

# Base OS: Debian 12 (Bookworm) slim — Linux distribution with minimal footprint
FROM python:3.9-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5477

CMD ["gunicorn", "--bind", "0.0.0.0:5477", "--workers", "2", "--threads", "2", "wsgi:app"]
