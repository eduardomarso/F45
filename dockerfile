FROM python:3.8-slim

# Install dependencies
RUN pip install --upgrade pip
RUN pip install moviepy pillow==8.3.2  # Ensure Pillow version that doesn't have deprecated 'ANTIALIAS'

# Copy the script into the container
COPY split_video.py /app/split_video.py

# Set working directory
WORKDIR /app

# Run the script
CMD ["python", "split_video.py"]
