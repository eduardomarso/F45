import boto3
import os
import shutil
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# AWS S3 Config
S3_BUCKET = "3dy"
INPUT_FOLDER = "/app/input"  # Updated to match Docker structure
OUTPUT_FOLDER = "/app/output"
S3_CLIENT = boto3.client("s3")

def clean_output_folder():
    """Delete all files in the output folder before processing."""
    if os.path.exists(OUTPUT_FOLDER):
        shutil.rmtree(OUTPUT_FOLDER)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("✅ Cleared output folder.")

def download_from_s3():
    """Download the first video file from S3 bucket to input folder."""
    
    # Ensure input folder is empty
    if os.path.exists(INPUT_FOLDER):
        shutil.rmtree(INPUT_FOLDER)
    os.makedirs(INPUT_FOLDER, exist_ok=True)

    objects = S3_CLIENT.list_objects_v2(Bucket=S3_BUCKET, Prefix="F45/input/")

    if "Contents" in objects:
        for obj in objects["Contents"]:
            filename = os.path.basename(obj["Key"])  # Extract filename properly
            if filename.lower().endswith(('.mp4', '.mov', '.avi')):  # Filter valid video files
                local_path = os.path.join(INPUT_FOLDER, filename)
                S3_CLIENT.download_file(S3_BUCKET, obj["Key"], local_path)
                print(f"✅ Downloaded {filename} from S3")
                return local_path  # Process only the first video

    print("❌ No video files found in S3 input folder.")
    return None

def upload_to_s3():
    """Upload output files to S3."""
    for file in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, file)
        S3_CLIENT.upload_file(file_path, S3_BUCKET, f"F45/output/{file}")
        print(f"✅ Uploaded {file} to S3 output folder.")

def split_and_merge_video(input_folder, output_gif, segment_duration=10, max_gif_size_mb=10):
    """Splits a workout video into 2 GIFs, ensuring each GIF stays under 10MB."""

    os.makedirs(os.path.dirname(output_gif), exist_ok=True)
    
    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    if not video_files:
        print("❌ No video files found in the input folder.")
        return

    input_video = os.path.join(input_folder, video_files[0])
    video = VideoFileClip(input_video)
    video_duration = video.duration

    print(f"🎥 Processing video: {input_video} (Duration: {video_duration:.2f}s)")

    clips = []
    
    with ThreadPoolExecutor() as executor:
        for start_time in range(0, int(video_duration), segment_duration):
            end_time = min(start_time + segment_duration - 0.5, video_duration)
            subclip = video.subclip(start_time, end_time)
            subclip = subclip.fx(speedx, 1.4)  # Slight speedup to reduce size

            # Resize dynamically based on target size
            subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w // 2))
            clips.append(subclip)

    if clips:
        total_clips = len(clips)
        half = (total_clips + 1) // 2  # First GIF gets extra clip if odd

        # First GIF
        first_output_gif = output_gif.replace(".gif", "1.gif")
        save_gif(clips[:half], first_output_gif, max_gif_size_mb)

        # Second GIF
        second_output_gif = output_gif.replace(".gif", "2.gif")
        if clips[half:]:
            save_gif(clips[half:], second_output_gif, max_gif_size_mb)

def save_gif(clips, output_path, max_size_mb):
    """Saves a GIF under the given size limit (MB)."""
    colors_list = [128, 64, 32]
    width_factors = [1.0, 0.8, 0.6, 0.5]
    base_fps = 15  

    for width_factor in width_factors:
        for colors in colors_list:
            resized_clips = [clip.fl_image(lambda frame: resize_frame(frame, int(clip.w * width_factor))) for clip in clips]
            stacked_clip = clips_array([[clip] for clip in resized_clips])
            stacked_clip.write_gif(output_path, fps=base_fps, program="ffmpeg", fuzz=10, loop=0, colors=colors)

            if os.path.exists(output_path) and os.path.getsize(output_path) <= max_size_mb * 1024 * 1024:
                print(f"✅ GIF saved under {max_size_mb}MB: {output_path}")
                return  

    print(f"⚠️ Warning: Could not keep {output_path} under {max_size_mb}MB.")

def resize_frame(frame, width):
    """Resizes a frame while maintaining aspect ratio."""
    resized_frame = Image.fromarray(frame).resize((width, width), Image.LANCZOS)
    return np.array(resized_frame)

if __name__ == "__main__":
    clean_output_folder()
    video_path = download_from_s3()
    if video_path:
        split_and_merge_video(INPUT_FOLDER, os.path.join(OUTPUT_FOLDER, "🤸.gif"))
        upload_to_s3()
