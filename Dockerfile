# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional for building some packages)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pymysql

# Copy the rest of the app
COPY . .

# ✅ Add wait-for-it script
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Expose Flask port
EXPOSE 5000

# ✅ Wait for MySQL before starting Flask
CMD ["/wait-for-it.sh", "db:3306", "--", "python", "app.py"]