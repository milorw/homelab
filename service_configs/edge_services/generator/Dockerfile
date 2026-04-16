FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY generator.py .
COPY ip.yaml .

CMD ["python", "/app/generator.py"]
