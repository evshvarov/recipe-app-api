
# Useful commands

## docker
docker-compose build

docker-compose build --no-cache --progress=plain

## linting for python

docker-compose run --rm app sh -c "flake8"

## testing for python

docker-compose run --rm app sh -c "python manage.py test"

## django commands

docker-compose run --rm app sh -c "django-admin startproject app ."

docker-compose run --rm app sh -c "python manage.py startapp core"

docker-compose run --rm app sh -c "python manage.py makemigrations"

docker-compose run --rm app sh -c "python manage.py migrate"

docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"

docker volume rm recipe-app-api_dev-db-data

docker-compose run --rm app sh -c "python manage.py createsuperuser"

docker-compose run --rm app sh -c "python manage.py startapp user"


curl -X 'GET' \
  'http://127.0.0.1:8000/api/user/me/' \
  -H 'accept: application/json' \
  -H 'Authorization: Token 4dcd498d105293cbbe74dfcb8ccc044c4d468461'
