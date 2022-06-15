release: python manage.py migrate
web: gunicorn geospatialproject.wsgi --timeout 200 --log-file -
