import os
import boto3
from moviepy.editor import VideoFileClip, clips_array
from moviepy.video.fx.all import speedx
import tempfile
import numpy as np
from PIL import Image

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """Lambda function to process video from S3, split into GIFs, and save back to S3."""
    # Extract information about the uploaded file from the S3 event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    video_key = event['Records'][0]['s3']['object']['key']

    # Create temporary directories for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        input_video_path = os.path.join(tmpdir, 'input_video.mp4')

        # Download the video file from S3 to the Lambda temp directory
        s3_client.download_file(bucket_name, video_key, input_video_path)

        # Process the video (split into GIFs and upload them back to S3)
        output_gif_key = process_video(input_video_path, bucket_name)
    
    return {
        'statusCode': 200,
        'body': f"GIFs successfully created and uploaded: {output_gif_key}"
    }

def process_video(input_video_path, bucket_name, segment_duration=10):
    """Process video to split into GIFs and upload them back to S3."""
    video = VideoFileClip(input_video_path)
    video_duration = video.duration

    print(f"Processing video: {input_video_path} (Duration: {video_duration:.2f}s)")

    clips = []
    clip_index = 1

    # Split video into clips and resize
    for start_time in range(0, int(video_duration), segment_duration):
        end_time = min(start_time + segment_duration - 0.5, video_duration)
        subclip = video.subclip(start_time, end_time)
        subclip = subclip.fx(speedx, 1.5)  # Speed up x1.5

        # Resize while maintaining aspect ratio
        subclip = subclip.fl_image(lambda frame: resize_frame(frame, video.w))

        clips.append(subclip)
        clip_index += 1

    # Combine clips into one GIF file
    if clips:
        total_clips = len(clips)
        num_parts = 2  # Split into 2 parts (adjust if needed)
        part_size = (total_clips + num_parts - 1) // num_parts  # Round up to ensure equal distribution

        gif_keys = []
        for part in range(num_parts):
            start_idx = part * part_size
            end_idx = min((part + 1) * part_size, total_clips)
            part_clips = clips[start_idx:end_idx]

            if part_clips:
                part_output_gif = f"part_{part + 1}.gif"
                stacked_clip = clips_array([[clip] for clip in part_clips])

                # Optimize GIF size by resizing and reducing colors
                stacked_clip = stacked_clip.resize(height=480)  # Resize height to 480px
                stacked_clip_path = os.path.join(tmpdir, part_output_gif)

                stacked_clip.write_gif(
                    stacked_clip_path,
                    fps=12,
                    program="ffmpeg",
                    fuzz=3,
                    loop=0,
                    colors=128
                )

                # Upload the resulting GIF to S3
                s3_output_gif_key = f"output_gifs/{part_output_gif}"
                s3_client.upload_file(stacked_clip_path, bucket_name, s3_output_gif_key)

                gif_keys.append(s3_output_gif_key)
                print(f"Part {part + 1} GIF uploaded: {s3_output_gif_key}")

        return gif_keys

def resize_frame(frame, width):
    """Resizes a frame while maintaining horizontal aspect ratio."""
    current_height, current_width = frame.shape[:2]

    if current_width > current_height:
        height = int(width * current_height / current_width)
    else:
        height = int(width * current_width / current_height)

    resized_frame = Image.fromarray(frame).resize((width, height), Image.LANCZOS)
    return np.array(resized_frame)
