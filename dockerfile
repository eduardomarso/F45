FROM python:3.10-slim

WORKDIR /app
# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*
# Install Python dependencies
RUN pip install --no-cache-dir \
    moviepy \
    youtube_dl \
    pillow==8.3.2 \
    openai-whisper \
    psutil \
    ffmpeg-python \
    boto3

RUN git clone https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe
RUN mkdir -p /app/input /app/output
COPY f45.py /app/f45.py
ENTRYPOINT ["python", "/app/f45.py"]
