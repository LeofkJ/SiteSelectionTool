release: python manage.py migrate
web: gunicorn geospatialproject.wsgi --timeout 15 --log-file -
