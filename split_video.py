from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
import os
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

def split_and_merge_video(input_folder, output_gif, segment_duration=10):
    """Splits video into GIFs and merges them vertically into one or two stacked GIFs."""
    
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
    clip_index = 1  

    with ThreadPoolExecutor() as executor:
        for start_time in range(0, int(video_duration), segment_duration):
            end_time = min(start_time + segment_duration - 0.5, video_duration)
            subclip = video.subclip(start_time, end_time)
            subclip = subclip.fx(speedx, 1.5)  # Speed up x2

            # Resize while keeping a horizontal orientation
            subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w // 2))  # Reduce resolution by half

            clips.append(subclip)
            clip_index += 1  

    if clips:
        # Split the clips into two parts
        total_clips = len(clips)
        half = (total_clips + 1) // 2  # Ensures the first GIF gets the extra clip if odd

        # Create the first GIF with the first half of the clips
        first_clips = clips[:half]
        first_output_gif = output_gif.replace(".gif", "1.gif")
        stacked_clip = clips_array([[clip] for clip in first_clips])
        stacked_clip.write_gif(
            first_output_gif,
            fps=15,  # Maintain smooth playback
            program="ffmpeg",
            fuzz=3,
            loop=0,
            colors=128,  # Reduce the number of colors to 128
            opt="OptimizePlus",  # Optimize the GIF
        )
        print(f"First stacked GIF saved: {first_output_gif}")

        # Create the second GIF with the remaining clips
        if total_clips > half:
            second_clips = clips[half:]
            second_output_gif = output_gif.replace(".gif", "2.gif")
            stacked_clip = clips_array([[clip] for clip in second_clips])
            stacked_clip.write_gif(
                second_output_gif,
                fps=15,  # Maintain smooth playback
                program="ffmpeg",
                fuzz=3,
                loop=0,
                colors=128,  # Reduce the number of colors to 128
                opt="OptimizePlus",  # Optimize the GIF
            )
            print(f"Second stacked GIF saved: {second_output_gif}")

def resize_frame(frame, width):
    """Resizes a frame while maintaining horizontal aspect ratio."""
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
