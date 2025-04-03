import os
import subprocess
import re
import time
import numpy as np
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
from PIL import Image

def convert_mov_to_mp4(input_path):
    """Converts a .mov file to .mp4 using ffmpeg if needed and waits for the conversion."""
    if not input_path.lower().endswith(".mov"):
        return input_path  # No conversion needed

    output_path = input_path.replace(".mov", ".mp4")
    print(f"🎥 Converting {input_path} to {output_path}...")

    command = [
        "ffmpeg", "-i", input_path, "-vcodec", "libx264",
        "-acodec", "aac", "-strict", "experimental", output_path
    ]

    try:
        subprocess.run(command, check=True)
        os.remove(input_path)  # Remove the original .mov file after conversion
        print(f"✅ Conversion successful: {output_path}")

        # Wait for the converted file to be fully written before returning
        if wait_for_file(output_path):
            return output_path
        else:
            print(f"⚠️ Converted file {output_path} not found after conversion.")
            return input_path  # Fallback to original file if something goes wrong
    except subprocess.CalledProcessError as e:
        print(f"❌ Conversion failed: {e}")
        return input_path  # Use the original file if conversion fails

def wait_for_file(file_path, timeout=30):
    """Waits until a file exists and is fully written."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read()  # Ensure it's not locked
                return True
            except:
                pass
        time.sleep(1)
    return False

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

def split_and_merge_video(input_folder, output_gif, segment_duration=10, max_gif_size_mb=10):
    """Splits a workout video into exactly 2 GIFs, each covering half the total clips."""
    os.makedirs(os.path.dirname(output_gif), exist_ok=True)

    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    if not video_files:
        print("⚠️ No video files found in the input folder.")
        return

    input_video = os.path.join(input_folder, video_files[0])

    # Convert .mov files to .mp4 before processing
    if input_video.lower().endswith(".mov"):
        input_video = convert_mov_to_mp4(input_video)

    if not input_video.lower().endswith(".mp4"):
        print("❌ No valid .mp4 video available for processing.")
        return

    video = VideoFileClip(input_video)
    video_duration = video.duration
    print(f"📹 Processing video: {input_video} (Duration: {video_duration:.2f}s)")

    clips = [video.subclip(start, min(start + segment_duration, video_duration))
             .fx(speedx, 1.2)
             .fl_image(lambda frame: resize_frame(frame, video.w // 2))
             for start in range(0, int(video_duration), segment_duration)]

    num_clips = len(clips)

    if num_clips < 2:
        print("⚠️ Error: The video must generate at least 2 clips to split evenly.")
        return

    # Split clips into exactly two equal parts
    half = num_clips // 2
    first_clips = clips[:half]
    second_clips = clips[half:]

    output_gif1 = output_gif.replace(".gif", "1.gif")
    output_gif2 = output_gif.replace(".gif", "2.gif")

    print(f"🎬 Generating first GIF: {output_gif1}...")
    save_gif(first_clips, output_gif1, max_gif_size_mb)

    print(f"🎬 Generating second GIF: {output_gif2}...")
    save_gif(second_clips, output_gif2, max_gif_size_mb)

    print(f"✅ GIFs created successfully: {output_gif1}, {output_gif2}")

def save_gif(clips, output_path, max_size_mb):
    """Saves a stacked GIF while ensuring it remains under the size limit."""
    if not clips:
        print(f"⚠️ No clips provided for {output_path}")
        return

    print(f"🔨 Saving GIF: {output_path}...")

    base_fps = 15
    width_factor = 1.0  # Default width scaling
    colors = 128  # Default color depth

    resized_clips = [clip.fl_image(lambda frame: resize_frame(frame, int(clip.w * width_factor))) for clip in clips]
    stacked_clip = clips_array([[clip] for clip in resized_clips])

    print(f"🖼 Creating GIF frames for {output_path}...")
    stacked_clip.write_gif(output_path, fps=base_fps, program="ffmpeg", fuzz=10, loop=0, colors=colors, opt="OptimizePlus")

    # Ensure the GIF is under max size
    if os.path.exists(output_path) and os.path.getsize(output_path) <= max_size_mb * 1024 * 1024:
        print(f"✅ GIF saved under {max_size_mb}MB: {output_path} ({os.path.getsize(output_path) / 1024 / 1024:.2f}MB)")
    else:
        print(f"⚠️ Warning: GIF {output_path} may exceed {max_size_mb}MB limit.")

def resize_frame(frame, width):
    """Resizes a frame while maintaining aspect ratio."""
    h, w = frame.shape[:2]
    height = int(width * h / w) if w > h else int(width * w / h)
    return np.array(Image.fromarray(frame).resize((width, height), Image.LANCZOS))

if __name__ == "__main__":
    transcribe_videos()
    split_and_merge_video("/app/input/workout", "/app/output/🤸.gif")
