release: python manage.py migrate
web: gunicorn geospatialproject.wsgi --timeout 1000 --log-file -
