FROM python:3.14-slim

WORKDIR /code

# Copy dependency file first for better Docker caching
COPY requirements.txt .

# Install dependencies without storing cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only application files
COPY ./app ./app

# Expose application port
EXPOSE 80

# Run FastAPI application
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
