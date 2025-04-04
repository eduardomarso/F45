import os
import subprocess
import re
import time
import numpy as np
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx, crop
from PIL import Image


def convert_mov_to_mp4(input_path):
    """Converts a .mov file to .mp4 using ffmpeg if needed and waits for the conversion."""
    if not input_path.lower().endswith(".mov"):
        return input_path

    output_path = input_path.replace(".mov", ".mp4")
    print(f"🎥 Converting {input_path} to {output_path}...")

    command = ["ffmpeg", "-i", input_path, "-vcodec", "libx264", "-acodec", "aac", "-strict", "experimental", output_path]

    try:
        subprocess.run(command, check=True)

        # Wait for file to be fully written
        if wait_for_file(output_path):
            os.remove(input_path)  # ✅ Delete only after confirming MP4 exists
            print(f"✅ Conversion successful: {output_path}")
            return output_path
        else:
            print(f"⚠️ Warning: Conversion finished, but {output_path} not detected in time.")
            return input_path
    except subprocess.CalledProcessError:
        print("❌ Conversion failed.")
        return input_path
def wait_for_file(file_path, timeout=30):
    """Waits until a file exists and is fully written."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read()
                return True
            except:
                pass
        time.sleep(1)
    return False
def crop_video_center(video):
    """Crops the video to 1575x888, centering it horizontally."""
    target_width, target_height = 1575, 888
    crop_x = (video.w - target_width) // 2
    return crop(video, x1=crop_x, y1=0, x2=crop_x + target_width, y2=target_height)


def split_and_merge_video(input_folder, output_gif, segment_duration=10, max_gif_size_mb=10):
    """Splits a workout video into 2 GIFs, ensuring each GIF stays under 10MB."""

    os.makedirs(os.path.dirname(output_gif), exist_ok=True)

    # Get the video file from the input folder
    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    if not video_files:
        print("No video files found in the input folder.")
        return

    input_video = os.path.join(input_folder, video_files[0])

    # Check if it's a .mov file, convert it to .mp4 if needed
    if input_video.lower().endswith(".mov"):
        input_video = convert_mov_to_mp4(input_video)

    # Load and crop the full video
    video = VideoFileClip(input_video)
    video = crop_video_center(video)  # Crop before splitting
    video_duration = video.duration

    print(f"Processing video: {input_video} (Duration: {video_duration:.2f}s)")

    clips = []

    # Split the video into segments
    for start_time in range(0, int(video_duration), segment_duration):
        end_time = min(start_time + segment_duration - 0.5, video_duration)
        subclip = video.subclip(start_time, end_time)
        subclip = subclip.fx(speedx, 1.3)  # Slight speedup to reduce size

        # Resize dynamically based on target size
        subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w // 2))

        clips.append(subclip)

    if clips:
        total_clips = len(clips)
        half = (total_clips + 1) // 2  # Ensures the first GIF gets the extra clip if odd

        # First GIF
        first_clips = clips[:half]
        first_output_gif = output_gif.replace(".gif", "1.gif")
        save_gif(first_clips, first_output_gif)

        # Second GIF
        second_clips = clips[half:]
        if second_clips:
            second_output_gif = output_gif.replace(".gif", "2.gif")
            save_gif(second_clips, second_output_gif)
def save_gif(clips, output_path):
    """Saves a vertically stacked GIF with fixed low-res, color-limited, and compressed settings."""
    if not clips:
        return

    resized_clips = [clip.fl_image(lambda frame: resize_frame(frame, int(clip.w * 0.5))) for clip in clips]
    stacked_clip = clips_array([[clip] for clip in resized_clips])

    stacked_clip.write_gif(
        output_path,
        fps=15,
        program="ffmpeg",
        fuzz=10,
        loop=0,
        colors=32,
        opt="OptimizePlus"
    )

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"✅ GIF saved: {output_path} (Size: {size_mb:.2f}MB)")
        if size_mb > 10:
            print("⚠️ Warning: Final GIF size is over 10MB!")
def resize_frame(frame, width):
    """Resizes a frame while maintaining aspect ratio."""
    current_height, current_width = frame.shape[:2]

    if current_width > current_height:
        height = int(width * current_height / current_width)
    else:
        height = int(width * current_width / current_height)

    resized_frame = Image.fromarray(frame).resize((width, height), Image.LANCZOS)
    return np.array(resized_frame)


def transcribe_videos():
    """Transcribes video and renames .srt to 📝.txt"""
    print("📝 Starting transcription process...")

    try:
        subprocess.run(
            ["python", "/app/Video-Transcribe/whisper-og.py", "-i", "/app/input/transcript", "-od", "/app/output"],
            check=True
        )

        output_folder = "/app/output"
        transcript_files = [f for f in os.listdir(output_folder) if f.endswith(".srt")]

        if not transcript_files:
            print("⚠️ No transcript file found!")
            return

        srt_file = os.path.join(output_folder, transcript_files[0])
        safe_txt_file = os.path.join(output_folder, "transcript.txt")
        emoji_txt_file = os.path.join(output_folder, "📝.txt")

        # Wait for the file to be fully written
        if not wait_for_file(srt_file):
            print(f"⚠️ Failed to confirm .srt file is fully written: {srt_file}")
            return

        # Read & clean the transcript
        with open(srt_file, "r", encoding="utf-8") as f:
            content = f.read()

        cleaned_text = clean_transcription(content)

        # Save as "transcript.txt" first
        with open(safe_txt_file, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        # Ensure it's fully written before renaming
        if wait_for_file(safe_txt_file):
            try:
                os.rename(safe_txt_file, emoji_txt_file)
                print(f"✅ Transcription saved as {emoji_txt_file}")
            except Exception as rename_error:
                print(f"⚠️ Renaming to '📝.txt' failed, using 'transcript.txt' instead: {rename_error}")
        else:
            print(f"⚠️ Failed to find {safe_txt_file} in time.")

        # Remove the original .srt file
        os.remove(srt_file)

        print("✅ Transcription completed and cleaned successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Transcription failed: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
def clean_transcription(text):
    """Removes SRT timestamps and line numbers while preserving sentence structure and formatting into a paragraph."""
    # Remove line numbers (lines that contain only numbers)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove timestamps (HH:MM:SS,mmm --> HH:MM:SS,mmm)
    text = re.sub(r'\d{1,2}:\d{2}:\d{2},\d{3} --> \d{1,2}:\d{2}:\d{2},\d{3}', '', text)

    # Remove excessive newlines and extra spaces between sentences
    text = re.sub(r'\n+', ' ', text)  # Replace all newlines with a space
    text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces
    text = text.strip()

    return text


if __name__ == "__main__":
    transcribe_videos()
    split_and_merge_video("/app/input/workout", "/app/output/🤸.gif")
