#!/bin/sh
set -e

echo ">> Migratsiyalar..."
python manage.py migrate --noinput

echo ">> Tarjimalar kompilyatsiyasi..."
python manage.py compilemessages --ignore=.venv

echo ">> Static fayllar..."
python manage.py collectstatic --noinput

echo ">> Boshlang'ich ma'lumotlar (admin, user, turlar)..."
python manage.py seed

echo ">> Server ishga tushdi: http://localhost:8000/api/docs/"
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
