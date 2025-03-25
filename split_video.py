import os
import boto3
import shutil
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import subprocess

# AWS S3 Config
S3_BUCKET = "3du"
S3_INPUT_PREFIX = "F45/input/"
S3_OUTPUT_PREFIX = "F45/output/"
INPUT_FOLDER = "/app/input"
OUTPUT_FOLDER = "/app/output"
S3_CLIENT = boto3.client("s3")

def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

def clean_local_folder(folder_path):
    """Delete all files in the specified local folder."""
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

def download_from_s3():
    """Download video files from S3."""
    create_folder_if_not_exists(INPUT_FOLDER)
    clean_local_folder(INPUT_FOLDER)
    objects = S3_CLIENT.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_INPUT_PREFIX)
    
    video_paths = []
    if "Contents" in objects:
        for obj in objects["Contents"]:
            filename = os.path.basename(obj["Key"])
            local_path = os.path.join(INPUT_FOLDER, filename)
            S3_CLIENT.download_file(S3_BUCKET, obj["Key"], local_path)
            video_paths.append(local_path)

    return video_paths

def split_and_merge_video(video_path, output_gif, segment_duration=10, max_gif_size_mb=10):
    """Splits a workout video into 2 GIFs."""
    video = VideoFileClip(video_path)
    clips = []
    
    for start_time in range(0, int(video.duration), segment_duration):
        end_time = min(start_time + segment_duration, video.duration)
        subclip = video.subclip(start_time, end_time).fx(speedx, 1.4)
        subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w // 2))
        clips.append(subclip)

    if clips:
        half = len(clips) // 2
        save_gif(clips[:half], output_gif.replace(".gif", "1.gif"), max_gif_size_mb)
        save_gif(clips[half:], output_gif.replace(".gif", "2.gif"), max_gif_size_mb)

def save_gif(clips, output_path, max_size_mb):
    """Saves a GIF while keeping it under a size limit."""
    colors_list = [128, 64, 32]
    width_factors = [1.0, 0.8, 0.6]
    
    for width_factor in width_factors:
        for colors in colors_list:
            resized_clips = [clip.fl_image(lambda frame: resize_frame(frame, int(clip.w * width_factor))) for clip in clips]
            stacked_clip = clips_array([[clip] for clip in resized_clips])
            stacked_clip.write_gif(output_path, fps=15, program="ffmpeg", fuzz=10, colors=colors)

            if os.path.exists(output_path) and os.path.getsize(output_path) <= max_size_mb * 1024 * 1024:
                return

def resize_frame(frame, width):
    """Resize while maintaining aspect ratio."""
    resized_frame = Image.fromarray(frame).resize((width, width), Image.LANCZOS)
    return np.array(resized_frame)

def transcribe_video(video_path, output_txt):
    """Run Whisper transcription."""
    command = f"python3 /app/Video-Transcribe/whisper-og.py -i {video_path} -od {output_txt}"
    subprocess.run(command, shell=True)

def upload_to_s3():
    """Upload output files to S3."""
    for file in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, file)
        S3_CLIENT.upload_file(file_path, S3_BUCKET, f"{S3_OUTPUT_PREFIX}{file}")

if __name__ == "__main__":
    create_folder_if_not_exists(OUTPUT_FOLDER)
    clean_local_folder(OUTPUT_FOLDER)
    
    video_paths = download_from_s3()

    if video_paths:
        with ThreadPoolExecutor() as executor:
            for video in video_paths:
                if "workout" in video.lower():
                    executor.submit(split_and_merge_video, video, os.path.join(OUTPUT_FOLDER, "🤸.gif"))
                elif "📝" in video.lower():
                    executor.submit(transcribe_video, video, OUTPUT_FOLDER)

        upload_to_s3()
