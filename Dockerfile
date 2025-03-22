# Dockerfile
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install OS-level dependencies (optional, for psycopg2)
RUN apt-get update && apt-get install -y build-essential libpq-dev && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Set default command (can be overridden)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
