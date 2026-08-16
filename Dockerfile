FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chmod +x /app/build.sh

EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --no-input && python manage.py migrate --no-input && python manage.py loaddata fixtures/initial_data.json || true && gunicorn shopsphere_project.wsgi:application --bind 0.0.0.0:8000"]
