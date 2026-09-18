FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY download_jailbreakbench.py .
COPY static ./static
RUN mkdir -p /app/data

EXPOSE 8102

CMD ["sh", "-c", "if [ ! -f /app/data/jailbreakbench_official.json ]; then python /app/download_jailbreakbench.py; fi && uvicorn app:app --host 0.0.0.0 --port 8102"]
