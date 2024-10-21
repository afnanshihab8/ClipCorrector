import os
import requests
import moviepy.editor as mp
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment
from google.cloud import speech, texttospeech, storage
import streamlit as st
import numpy as np
import time
import openai

# Set the path to ffmpeg
AudioSegment.converter = r"C:\ffmpeg-2024-10-17-git-e1d1ba4cbc-full_build\bin\ffmpeg.exe"

# Function to set Google credentials
def set_google_credentials(credentials):
    """Set Google Cloud credentials for the session."""
    with open("google_credentials.json", "w") as cred_file:
        cred_file.write(credentials)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials.json"

# Uploading to Google Cloud Storage
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the Google Cloud Storage bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    return gcs_uri

# Extracting audio from video
def extract_audio_from_video(video_path):
    video = mp.VideoFileClip(video_path)
    audio_path = "extracted_audio.wav"
    video.audio.write_audiofile(audio_path)

    # Converting to mono using pydub
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1)
    mono_audio_path = "mono_audio.wav"
    audio.export(mono_audio_path, format="wav")

    return mono_audio_path

# Transcribing long audio using Google Cloud
def transcribe_long_audio(gcs_uri):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="en-US",
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=90)

    # Collecting the transcription results
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "
    return transcript.strip()

# Correcting the transcription with OpenAI
def correct_transcription_with_openai(transcription):
    """Corrects the transcription using OpenAI's GPT model."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Correct this transcription to make it more sensible:\n\n{transcription}"}
            ]
        )
        corrected_transcription = response.choices[0].message['content'].strip()
        return corrected_transcription
    except Exception as e:
        st.error(f"Error correcting transcription: {str(e)}")
        return transcription  # Error

# Generating audio from corrected text using Google Text-to-Speech
def generate_audio_from_text(corrected_text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=corrected_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    output_audio_path = "output_audio.wav"
    with open(output_audio_path, "wb") as out:
        out.write(response.audio_content)
    return output_audio_path

# Replacing audio in video
def replace_audio_in_video(video_path, new_audio_path, output_video_path):
    video = VideoFileClip(video_path)
    new_audio = AudioFileClip(new_audio_path)
    video = video.set_audio(new_audio)
    video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

# Connecting to Azure OpenAI and get a response
def connect_to_azure_openai(azure_openai_key, azure_openai_endpoint):
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_key
    }

    data = {
        "messages": [{"role": "user", "content": "Hello, Azure OpenAI!"}],
        "max_tokens": 50
    }

    response = requests.post(azure_openai_endpoint, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        raise Exception(f"Azure OpenAI Error: {response.status_code} - {response.text}")

# Streamlit App
def main():
    st.title("Video Audio Correcting using OpenAI and Google API")

    # User inputs for Google credentials
    google_credentials = st.text_area("Paste your Google Cloud credentials JSON here:", height=200)

    # Set Google credentials if provided
    if st.button("Set Google Credentials"):
        if google_credentials:
            set_google_credentials(google_credentials)
            st.success("Google Cloud credentials set successfully.")
        else:
            st.warning("Please provide your Google Cloud credentials.")

    # Azure OpenAI connection details
    azure_openai_key = st.text_input("Azure OpenAI API Key", type="password")  # Input for the API key
    azure_openai_endpoint = st.text_input("Azure OpenAI Endpoint URL")  # Input for the endpoint URL

    # Button to initiate the connection and request
    if st.button("Connect to Azure OpenAI"):
        if azure_openai_key and azure_openai_endpoint:
            try:
                azure_response = connect_to_azure_openai(azure_openai_key, azure_openai_endpoint)
                st.success(f"Azure OpenAI Response: {azure_response}")
            except Exception as e:
                st.error(f"Failed to connect to Azure OpenAI: {str(e)}")

    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mkv", "avi"])
    if uploaded_file:
        video_path = "uploaded_video.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())
        st.video(video_path)

        # Progress bar
        progress_bar = st.progress(0)

        audio_file_path = extract_audio_from_video(video_path)
        progress_bar.progress(20)  # Update progress to 20%

        bucket_name = "azurevidapp"
        gcs_uri = upload_to_gcs(bucket_name, audio_file_path, "uploaded_audio.wav")
        progress_bar.progress(40)  # Update progress to 40%
        st.write("Audio uploaded to Google Cloud Storage.")

        transcription = transcribe_long_audio(gcs_uri)
        progress_bar.progress(60)  # Update progress to 60%
        if transcription:
            st.write(f"Transcription: {transcription}")

            corrected_transcription = correct_transcription_with_openai(transcription)
            progress_bar.progress(80)  # Update progress to 80%
            if corrected_transcription:
                st.write(f"Corrected Transcription: {corrected_transcription}")

                audio_output = generate_audio_from_text(corrected_transcription)
                progress_bar.progress(90)  # Update progress to 90%
                st.audio(audio_output, format="audio/wav")

                st.write("Processing video...")
                time.sleep(1)  # Simulate processing time for demonstration

                output_video_path = "output_video.mp4"
                replace_audio_in_video(video_path, audio_output, output_video_path)
                progress_bar.progress(100)  # Complete progress
                st.video(output_video_path)

                st.write("Play/Pause the video to verify the sync.")

if __name__ == "__main__":
    main()
