import os
import subprocess
import re
import time
import numpy as np
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx, crop
from PIL import Image


def convert_mov_to_mp4(input_path):
    if not input_path.lower().endswith(".mov"):
        return input_path

    output_path = input_path.replace(".mov", ".mp4")
    print(f"🎥 Converting {input_path} to {output_path}...")

    command = ["ffmpeg", "-i", input_path, "-vcodec", "libx264", "-acodec", "aac", "-strict", "experimental", output_path]

    try:
        subprocess.run(command, check=True)

        if wait_for_file(output_path):
            os.remove(input_path)
            print(f"✅ Conversion successful: {output_path}")
            return output_path
        else:
            print(f"⚠️ Warning: Conversion finished, but {output_path} not detected in time.")
            return input_path
    except subprocess.CalledProcessError:
        print("❌ Conversion failed.")
        return input_path


def wait_for_file(file_path, timeout=30):
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
    target_width, target_height = 1575, 888
    crop_x = (video.w - target_width) // 2
    return crop(video, x1=crop_x, y1=0, x2=crop_x + target_width, y2=target_height)


def resize_frame(frame, width):
    current_height, current_width = frame.shape[:2]
    height = int(width * current_height / current_width)
    resized_frame = Image.fromarray(frame).resize((width, height), Image.LANCZOS)
    return np.array(resized_frame)


def identify_files(input_dir):
    video_paths = []
    image_path = None

    for file in os.listdir(input_dir):
        path = os.path.join(input_dir, file)
        if os.path.isfile(path):
            if file.lower().endswith(('.mp4', '.mov', '.avi')):
                video_paths.append(path)
            elif file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = path

    durations = []
    for i in range(len(video_paths)):
        if video_paths[i].lower().endswith(".mov"):
            video_paths[i] = convert_mov_to_mp4(video_paths[i])
        try:
            clip = VideoFileClip(video_paths[i])
            durations.append(clip.duration)
        except Exception:
            durations.append(0)

    if not durations:
        raise ValueError("❌ No valid video files found!")

    workout_video = video_paths[np.argmax(durations)]
    transcript_video = video_paths[np.argmin(durations)]

    return workout_video, transcript_video, image_path


def split_and_merge_video(input_video, output_gif, segment_duration=10):
    os.makedirs(os.path.dirname(output_gif), exist_ok=True)

    video = VideoFileClip(input_video)
    video = crop_video_center(video)
    video_duration = video.duration

    print(f"🤸 Processing workout video: {input_video} (Duration: {video_duration:.2f}s)")

    clips = []
    for start_time in range(0, int(video_duration), segment_duration):
        end_time = min(start_time + segment_duration - 0.5, video_duration)
        subclip = video.subclip(start_time, end_time).fx(speedx, 1.3)
        subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w // 2))
        clips.append(subclip)

    if clips:
        half = (len(clips) + 1) // 2
        first_output_gif = output_gif.replace(".gif", "1.gif")
        second_output_gif = output_gif.replace(".gif", "2.gif")

        save_gif(clips[:half], first_output_gif)
        if clips[half:]:
            save_gif(clips[half:], second_output_gif)


def save_gif(clips, output_path):
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


def transcribe_video(input_video):
    print("📝 Starting transcription process...")

    temp_input_dir = "/app/input_transcribe_temp"
    os.makedirs(temp_input_dir, exist_ok=True)

    video_name = os.path.basename(input_video)
    temp_video_path = os.path.join(temp_input_dir, video_name)
    subprocess.run(["cp", input_video, temp_video_path], check=True)

    try:
        subprocess.run(
            ["python", "/app/Video-Transcribe/whisper-og.py", "-i", temp_input_dir, "-od", "/app/output"],
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

        if not wait_for_file(srt_file):
            print(f"⚠️ Failed to confirm .srt file is fully written: {srt_file}")
            return

        with open(srt_file, "r", encoding="utf-8") as f:
            content = f.read()
        cleaned_text = clean_transcription(content)

        with open(safe_txt_file, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        if wait_for_file(safe_txt_file):
            os.rename(safe_txt_file, emoji_txt_file)
            print(f"✅ Transcription saved as {emoji_txt_file}")
        os.remove(srt_file)
        print("✅ Transcription completed and cleaned successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Transcription failed: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
    finally:
        subprocess.run(["rm", "-rf", temp_input_dir])


def clean_transcription(text):
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d{1,2}:\d{2}:\d{2},\d{3} --> \d{1,2}:\d{2}:\d{2},\d{3}', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def process_image(image_path, output_folder):
    image = Image.open(image_path)

    # Get GIF size to crop and resize image to the same dimensions
    gif_path = os.path.join(output_folder, "🤸.gif")
    gif = Image.open(gif_path)
    gif_width, gif_height = gif.size

    # Resize the image
    image = image.resize((gif_width, gif_height), Image.LANCZOS)

    # Compress image without losing quality
    compressed_image_path = os.path.join(output_folder, "📝.png")
    image.save(compressed_image_path, format="PNG", quality=95)

    print(f"✅ Image saved as {compressed_image_path}")


if __name__ == "__main__":
    input_folder = "/app/input"
    output_folder = "/app/output"
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    all_files = os.listdir(input_folder)
    video_files = [f for f in all_files if f.lower().endswith(('.mp4', '.mov', '.avi'))]
    image_files = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not video_files:
        print("📂 No video files found in /app/input. Exiting gracefully...")
        exit(0)

    if not image_files:
        print("📂 No image file found in /app/input. Exiting gracefully...")
        exit(0)

    # Identify workout and transcript videos
    workout_video, transcript_video, image_path = identify_files(input_folder)

    # Proceed with transcription and GIF generation
    transcribe_video(transcript_video)
    split_and_merge_video(workout_video, os.path.join(output_folder, "🤸.gif"))

    # Process the image to match GIF size and save it
    process_image(image_path, output_folder)
