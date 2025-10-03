# Step 1: Use the official Playwright base image from Microsoft.
# This image already has Python, browsers, and all system dependencies installed!
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy your requirements file and install your Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Step 4: Copy the rest of your application code into the container
COPY . .

# Step 5: Define the command to run your app using Gunicorn
# This tells Gunicorn to run the 'app' object from your 'run.py' file.
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "300", "run:app"]