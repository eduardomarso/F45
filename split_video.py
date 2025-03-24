import boto3
import os
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# AWS S3 Config
S3_BUCKET = "3dy"  # Change to your S3 bucket name
INPUT_FOLDER = "/app/F45/input"
OUTPUT_FOLDER = "/app/F45/output"
S3_CLIENT = boto3.client("s3")

def download_from_s3():
    """Download the first video file from S3 bucket to input folder"""
    objects = S3_CLIENT.list_objects_v2(Bucket=S3_BUCKET, Prefix="input/")
    
    if "Contents" in objects:
        for obj in objects["Contents"]:
            filename = obj["Key"].split("/")[-1]
            local_path = os.path.join(INPUT_FOLDER, filename)
            S3_CLIENT.download_file(S3_BUCKET, obj["Key"], local_path)
            print(f"✅ Downloaded {filename} from S3")
            return local_path  # Process only the first video
    
    print("❌ No video files found in S3 input folder.")
    return None

def upload_to_s3():
    """Upload output files to S3"""
    for file in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, file)
        S3_CLIENT.upload_file(file_path, S3_BUCKET, f"output/{file}")
        print(f"✅ Uploaded {file} to S3 output folder")

def split_and_merge_video(input_folder, output_gif, segment_duration=10, max_gif_size_mb=10):
    """Splits a workout video into 2 GIFs, ensuring each GIF stays under 10MB."""
    
    os.makedirs(os.path.dirname(output_gif), exist_ok=True)

    # Get the video file from the input folder
    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    if not video_files:
        print("No video files found in the input folder.")
        return

    input_video = os.path.join(input_folder, video_files[0])
    video = VideoFileClip(input_video)
    video_duration = video.duration

    print(f"Processing video: {input_video} (Duration: {video_duration:.2f}s)")

    clips = []
    
    with ThreadPoolExecutor() as executor:
        for start_time in range(0, int(video_duration), segment_duration):
            end_time = min(start_time + segment_duration - 0.5, video_duration)
            subclip = video.subclip(start_time, end_time)
            subclip = subclip.fx(speedx, 1.4)  # Slight speedup to reduce size

            # Resize dy
