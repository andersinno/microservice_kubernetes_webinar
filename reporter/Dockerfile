# ===================================================
FROM andersinnovations/python:3.9-slim AS build-base
# ===================================================

EXPOSE 8000/tcp

# ===================================
FROM build-base AS poetry
# ===================================

ARG POETRY_CHECKSUM=e973b3badb95a916bfe250c22eeb7253130fd87312afa326eb02b8bdcea8f4a7
ARG POETRY_TARGET=/tmp/get-poetry.py

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/1.1.3/get-poetry.py -o "$POETRY_TARGET"
RUN sha256sum "$POETRY_TARGET"
RUN echo "$POETRY_CHECKSUM *$POETRY_TARGET" | sha256sum -c -
RUN python /tmp/get-poetry.py
RUN ln -s $HOME/.poetry/bin/poetry /usr/bin/poetry

COPY poetry.lock /app/poetry.lock
COPY pyproject.toml /app/pyproject.toml

RUN poetry export -f requirements.txt -o requirements.txt
RUN poetry export -f requirements.txt --dev -o requirements-dev.txt

# ===================================
FROM build-base AS base
# ===================================

COPY --from=poetry --chown=appuser:appuser /app/requirements.txt /app/requirements.txt
COPY --from=poetry --chown=appuser:appuser /app/requirements-dev.txt /app/requirements-dev.txt

# ==============================
FROM base AS development
# ==============================

# Install dev (and production) dependencies
RUN apt-install.sh build-essential libssl-dev \
 && pip install --no-cache-dir -r requirements-dev.txt \
 && apt-cleanup.sh build-essential

# Copy code to image
COPY --chown=appuser:appuser . /app

# Set up start command
ENV DEV_SERVER=1

# Set app user
USER appuser

# Start the application
ENTRYPOINT ["./docker-entrypoint.sh"]

# ==============================
FROM base AS production
# ==============================

# Install production dependencies
RUN apt-install.sh build-essential libssl-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-cleanup.sh build-essential

# Copy code to image
COPY --chown=appuser:appuser . /app

# Set app user
USER appuser

# Set up start command
ENTRYPOINT ["./docker-entrypoint.sh"]
