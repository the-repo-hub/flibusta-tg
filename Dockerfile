FROM python:3.11-slim as builder

#poetry
RUN pip install --no-cache-dir poetry==1.8.5
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /opt/flibusta/
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-ansi
ENV PATH="/opt/flibusta/.venv/bin:$PATH"

#move code
COPY ./src /opt/flibusta/src
WORKDIR /opt/flibusta/src
CMD ["python", "bot.py"]