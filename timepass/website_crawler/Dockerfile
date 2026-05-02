FROM python:3.9-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only to save space/time)
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Output folder for results
RUN mkdir -p output

# Environment variable for port
ENV PORT=5000

# Run with Gunicorn for production
# Need to add gunicorn to requirements or install it
RUN pip install gunicorn

CMD gunicorn --bind 0.0.0.0:$PORT app:app --timeout 120
