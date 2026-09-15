FROM python:3.14

WORKDIR /code

# this contains all the dependencies required for the application
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

# Runtime configuration such as API_KEY is injected by Docker Compose or
# Kubernetes rather than baked into the container image.
CMD ["fastapi", "run", "app/main.py", "--port", "8080"]
