FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    moviepy \
    pillow==8.3.2 \
    openai-whisper \
    psutil \
    ffmpeg-python \
    boto3 

# Clone the transcription repo
RUN git clone https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe

# Create input/output directories
RUN mkdir -p /app/input /app/output

# Copy Python script
COPY split_video.py /app/split_video.py

# EntryPoint to run processing
ENTRYPOINT ["python", "/app/split_video.py"]
