from google.cloud import texttospeech

def list_available_voices():
    """Lists available voices."""
    client = texttospeech.TextToSpeechClient()
    voices = client.list_voices()

    for voice in voices.voices:
        print(f"Name: {voice.name}, Language: {voice.language_codes}, SSML Gender: {voice.ssml_gender}")

# Call this function to list available voices
list_available_voices()
