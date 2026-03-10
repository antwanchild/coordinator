FROM python:3.11-slim

WORKDIR /app

# Install system deps for Pillow
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .
COPY V-COORDINATE--Scheduled.xlsx .
COPY templates/ templates/

# Version build arg — passed in by GitHub Actions
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

EXPOSE 5000

CMD ["python", "app.py"]
