# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose the application port
EXPOSE 80

# Use a production-ready WSGI server like Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:80", "app:app"]