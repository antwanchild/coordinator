FROM python:3.14-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    tzdata \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .
COPY entrypoint.sh .
COPY V-COORDINATE--Scheduled.xlsx .
COPY templates/ templates/

RUN chmod +x entrypoint.sh

# Version build arg — passed in by GitHub Actions
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

# Timezone — override with -e TZ=America/Denver
ENV TZ=UTC

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
