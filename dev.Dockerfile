# Use the official Python image.
FROM python:3.9-slim

# Set the working directory
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

# Copy the requirements files into the container
COPY requirements.txt requirements-dev.txt requirements-test.txt ./

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt -r requirements-test.txt

# Install Jupyter Lab
RUN pip install jupyterlab

# Expose the Jupyter Lab port
EXPOSE 8888

# Run Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--no-browser"]