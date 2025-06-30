# Use official lightweight Python image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY bot_api_forward.py .
COPY settings.json .

# Entrypoint
CMD ["python", "-u", "bot_api_forward.py"]
