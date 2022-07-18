release: python manage.py migrate
web: gunicorn geospatialproject.wsgi --timeout 20000 --log-file -
