FROM python:3.14-slim

WORKDIR /code

# Copy dependency file first for improved Docker caching
COPY requirements.txt .

# Install dependencies without storing cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./app ./app

# Environment variable
# TODO: Replace hardcoded API key with secure environment variable management
ENV API_KEY=secret_key

# Expose application port
EXPOSE 80

# Run FastAPI application
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
