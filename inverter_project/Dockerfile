# Use an official Python runtime as a parent image
FROM python:3.11.9

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && pip install --no-cache-dir -r requirements.txt

# Set environment variables (modern syntax)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port 8000 (default Django development server port)
EXPOSE 8000

# Run migrations and start the server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]