
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
