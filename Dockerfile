FROM python:3.11-alpine as runtime
ARG IMAGE_NAME=flibusta_bot

WORKDIR /opt/flibusta/

#poetry
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==1.8.5 && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi --only main
ENV PATH="/opt/flibusta/.venv/bin:$PATH"

#move code
COPY ./src /opt/flibusta/src
WORKDIR /opt/flibusta/src
ENTRYPOINT ["python"]
CMD ["bot.py"]