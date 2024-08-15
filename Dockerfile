FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Set the working directory inside the container
WORKDIR /app

# Install build-essential and other necessary system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*


# Define the build argument
ARG INSTALL_DEV=false

# Copy the requirements file into the container
COPY requirements.txt /app/requirements.txt
COPY requirements-dev.txt /app/requirements-dev.txt
COPY requirements-test.txt /app/requirements-test.txt

# Install the dependencies based on the build argument
RUN pip install --no-cache-dir --upgrade pip \
    && if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt -r requirements-test.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy the rest of the application code into the container
COPY . /app

# Expose the port FastAPI is going to run on
EXPOSE 8080

# Define the command to run the API
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]
