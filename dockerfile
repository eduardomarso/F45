# Use Python 3.10 Slim as Base Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    moviepy \
    pillow==8.3.2 \
    openai-whisper \
    psutil \
    ffmpeg-python \
    youtube-dl \
    validators \
    boto3  # Ensure boto3 is installed

# Create input/output directories
RUN mkdir -p /app/input /app/output

# Copy script to container
COPY split_video.py /app/split_video.py

# Set entrypoint to execute the script
ENTRYPOINT ["python", "/app/split_video.py"]
