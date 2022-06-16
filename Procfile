release: python manage.py migrate
web: gunicorn geospatialproject.wsgi --timeout 10000 --log-file -
