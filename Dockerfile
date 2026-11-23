FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}
ENV RELEASE_MESSAGE="Release Pipeline ${APP_VERSION}"

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.app:app"]
