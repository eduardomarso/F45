from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
import os
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

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

            # Resize dynamically based on target size
            subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w // 2))

            clips.append(subclip)

    if clips:
        total_clips = len(clips)
        half = (total_clips + 1) // 2  # Ensures the first GIF gets the extra clip if odd

        # First GIF
        first_clips = clips[:half]
        first_output_gif = output_gif.replace(".gif", "1.gif")
        save_gif(first_clips, first_output_gif, max_gif_size_mb)

        # Second GIF
        second_clips = clips[half:]
        if second_clips:
            second_output_gif = output_gif.replace(".gif", "2.gif")
            save_gif(second_clips, second_output_gif, max_gif_size_mb)

def save_gif(clips, output_path, max_size_mb):
    """Saves a stacked GIF while ensuring it remains under the given size limit (in MB)."""
    if not clips:
        return

    colors_list = [128, 64, 32]  # Reduce color depth for smaller size
    width_factors = [1.0, 0.8, 0.6, 0.5]  # Reduce resolution dynamically
    base_fps = 15  # Fixed FPS for consistency

    for width_factor in width_factors:
        for colors in colors_list:
            resized_clips = [clip.fl_image(lambda frame: resize_frame(frame, int(clip.w * width_factor))) for clip in clips]

            stacked_clip = clips_array([[clip] for clip in resized_clips])
            stacked_clip.write_gif(
                output_path,
                fps=base_fps,  # Constant smoothness
                program="ffmpeg",
                fuzz=10,  # More aggressive compression
                loop=0,
                colors=colors,
                opt="OptimizePlus",
            )

            # Check file size
            if os.path.exists(output_path) and os.path.getsize(output_path) <= max_size_mb * 1024 * 1024:
                print(f"✅ GIF saved under {max_size_mb}MB: {output_path} (Size: {os.path.getsize(output_path) / 1024 / 1024:.2f}MB)")
                return  # Stop searching when a valid size is achieved

    print(f"⚠️ Warning: Could not keep {output_path} under {max_size_mb}MB even with max compression.")

def resize_frame(frame, width):
    """Resizes a frame while maintaining aspect ratio."""
    current_height, current_width = frame.shape[:2]

    if current_width > current_height:
        height = int(width * current_height / current_width)
    else:
        height = int(width * current_width / current_height)

    resized_frame = Image.fromarray(frame).resize((width, height), Image.LANCZOS)
    return np.array(resized_frame)

if __name__ == "__main__":
    input_folder = "/input"
    output_gif = "/output/🤸.gif"
    split_and_merge_video(input_folder, output_gif)
