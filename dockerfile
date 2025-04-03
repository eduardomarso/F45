FROM python:3.10-bullseye

WORKDIR /app

# Set a better Debian mirror to avoid network issues
RUN echo "deb http://ftp.debian.org/debian bullseye main" > /etc/apt/sources.list && \
    apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
        ffmpeg git wget curl software-properties-common gnupg2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    moviepy \
    pillow==8.3.2 \
    numpy \
    ffmpeg-python \
    youtube-dl \
    validators \
    openai-whisper \
    psutil

# Clone Video-Transcribe repository
RUN git clone https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe

# Create directories for input/output
RUN mkdir -p /app/input/workout /app/input/transcript /app/output

# Copy the main script
COPY f45.py /app/f45.py

# Set entrypoint
ENTRYPOINT ["python", "/app/f45.py"]
