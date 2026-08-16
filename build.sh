#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Applying database migrations..."
python manage.py migrate --no-input

echo "Loading initial product fixture if database is fresh..."
python manage.py loaddata fixtures/initial_data.json || true
python manage.py seed_data || true

echo "Build process completed successfully!"
