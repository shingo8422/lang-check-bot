FROM python:3.11-slim

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN poetry config virtualenvs.create false && poetry install

COPY . .

CMD ["python", "main.py"]

EXPOSE 80
