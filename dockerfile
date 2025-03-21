# Build Stage
FROM python:3.10-slim as build

# Set the working directory for the build stage
WORKDIR /app

# Install dependencies required for building (ffmpeg, git, and other tools)
RUN apt-get update && apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a single step to reduce layers
RUN pip install --no-cache-dir moviepy pillow==8.3.2 openai-whisper psutil ffmpeg-python youtube-dl validators

# Clone the Video-Transcribe repository (shallow clone to reduce size)
RUN git clone --depth=1 https://github.com/a2nath/Video-Transcribe.git /app/Video-Transcribe

# Create input and output directories for later use
RUN mkdir -p /app/input/workout /app/input/transcript /app/output

# Clean up apt cache to further reduce image size
RUN apt-get clean

# Runtime Stage
FROM python:3.10-slim

# Set the working directory for the runtime stage
WORKDIR /app

# Copy only necessary files from the build stage to the runtime image
COPY --from=build /app /app

# Copy the split_video.py file (from workout splitting task) into the runtime container
COPY split_video.py /app/split_video.py

# Entry point to run both tasks concurrently
ENTRYPOINT ["bash", "-c", "python /app/split_video.py /app/input/workout /app/output/🤸.gif & python /app/Video-Transcribe/whisper-og.py -i /app/input/transcript -od /app/output & wait"]
