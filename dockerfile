# Build Stage
FROM python:3.10-slim as build
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir moviepy pillow==8.3.2 openai-whisper psutil ffmpeg-python youtube-dl validators boto3
RUN git clone --depth=1 https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe
RUN mkdir -p /app/input/workout /app/input/transcript /app/output
RUN apt-get clean

# Runtime Stage
FROM python:3.10-slim
WORKDIR /app
COPY --from=build /app /app
COPY split_video.py /app/split_video.py
ENTRYPOINT ["python", "/app/split_video.py"]
