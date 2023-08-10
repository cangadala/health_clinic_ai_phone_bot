# Use the official image as a parent image
FROM python:3.11.4

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libasound-dev \
    libsndfile1-dev \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install uvicorn fastapi vocode redis twilio

# Create a non-root user and switch to it
RUN useradd -m myuser
USER myuser

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define the command to run on container start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
