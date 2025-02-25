FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for both tasks
RUN pip install --no-cache-dir moviepy pillow==8.3.2 openai-whisper psutil ffmpeg-python youtube-dl validators

# Clone the Video-Transcribe repository for transcription task
RUN git clone https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe

# Create input and output directories
RUN mkdir -p /app/input/workout /app/input/transcript /app/output

# Copy the split_video.py (from workout splitting task) into the container
COPY split_video.py /app/split_video.py

# Entry point to run both tasks concurrently
ENTRYPOINT ["bash", "-c", "python /app/split_video.py /app/input/workout /app/output/🤸.gif & python /app/Video-Transcribe/whisper-og.py -i /app/input/transcript -od /app/output & wait"]
