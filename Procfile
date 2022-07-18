release: python manage.py migrate
web: gunicorn geospatialproject.wsgi --timeout 100000 --log-file -
