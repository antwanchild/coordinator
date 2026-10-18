FROM python:3.14-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    tzdata \
    gosu \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Remove vulnerable copies shipped in the Python base image before installing
# the application dependencies. Installing newer copies alongside the base
# packages can leave old dist-info metadata behind for scanners to detect.
COPY requirements.txt .
RUN python -m pip uninstall -y setuptools urllib3 msgpack || true && \
    python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --no-cache-dir --upgrade \
        "setuptools>=78.1.1" \
        "urllib3>=2.8.0" \
        "msgpack>=1.2.1" && \
    python -m pip check

# Copy app
COPY app.py constants.py logging_utils.py room_utils.py schedule.py renderer.py time_utils.py validation.py ./
COPY entrypoint.sh .
COPY V-COORDINATE--Scheduled.xlsx .
COPY templates/ templates/
COPY static/ static/

RUN chmod +x entrypoint.sh

# Default runtime user inside the image; entrypoint can still switch to a mapped user.
RUN useradd --system --create-home --home-dir /app --shell /usr/sbin/nologin coordinator && \
    chown -R coordinator:coordinator /app

# Version build arg — passed in by GitHub Actions
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
ARG APP_COMMIT_SHA=unknown
ENV APP_COMMIT_SHA=${APP_COMMIT_SHA}

LABEL org.opencontainers.image.version=${APP_VERSION} \
      org.opencontainers.image.revision=${APP_COMMIT_SHA}

# Timezone — override with -e TZ=America/Denver
ENV TZ=UTC

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
