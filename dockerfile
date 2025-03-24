# Build Stage
FROM python:3.10-slim as build

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    moviepy \
    pillow==8.3.2 \
    openai-whisper \
    psutil \
    ffmpeg-python \
    youtube-dl \
    validators \
    boto3  # Ensure boto3 is included

# Clone the Video-Transcribe repository
RUN git clone --depth=1 https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe

# Create input and output directories
RUN mkdir -p /app/input/workout /app/input/transcript /app/output

# Runtime Stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy built application from previous stage
COPY --from=build /app /app

# 🚀 Install dependencies again in runtime stage to ensure boto3 exists
RUN pip install --no-cache-dir \
    moviepy \
    pillow==8.3.2 \
    openai-whisper \
    psutil \
    ffmpeg-python \
    youtube-dl \
    validators \
    boto3  # Install boto3 again in the final image

# Copy script to container
COPY split_video.py /app/split_video.py

# Set entrypoint to execute the script
ENTRYPOINT ["python", "/app/split_video.py"]
