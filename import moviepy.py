import moviepy.editor as mp
import os

def extract_audio_from_video(uploaded_file):
    # Save uploaded video file temporarily
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Load the video file
    video = mp.VideoFileClip(uploaded_file.name)

    # Extract audio from the video
    audio_file = "extracted_audio.mp3"
    video.audio.write_audiofile(audio_file)
    
    # Return the path to the extracted audio
    return audio_file
