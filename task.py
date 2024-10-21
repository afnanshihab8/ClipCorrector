import streamlit as st
import openai
import requests
import json

def main():
    st.title("Azure OpenAI GPT-4o Connectivity Test") 

    # Azure OpenAI connection details
    azure_openai_key = ("22ec84421ec24230a3638d1b51e3a7dc`") # Replace with your actual key
    azure_openai_endpoint = """https://internshala.openai.azure.com/openai/deployments/gpt-4o/
chat/completions?api-version=2024-08-01-preview""" # Replace with your actual endpoint URL

    # Create a file uploader widget for video files
    uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "avi", "mov"])

    # Check if a file has been uploaded
    if uploaded_file is not None:
        st.write("Uploaded file:", uploaded_file.name)

        # Process the uploaded video file here (e.g., extract audio, transcribe)
        # For demonstration purposes, we'll display a message
        st.write("Processing the uploaded video...")

        # Here you can implement the logic to extract audio from the video

    # Button to initiate the connection and request
    if st.button("Connect and Get Response"):
        # Check if both the key and endpoint are provided
        if azure_openai_key and azure_openai_endpoint:
            try:
                # Setting up headers for the API request
                headers = {
                    "Content-Type": "application/json",  # Specify that we are sending JSON data
                    "api-key": azure_openai_key  # The API key for authentication
                }

                # Data to be sent to Azure OpenAI
                # This is where you can customize the message prompt and token limit.
                data = {
                    "messages": [{"role": "user", "content": "Hello, Azure OpenAI!"}],  # Sample message prompt
                    "max_tokens": 50  # Limit the response length
                }

                # Making the POST request to the Azure OpenAI endpoint
                response = requests.post(azure_openai_endpoint, headers=headers, json=data)

                # Check if the request was successful
                if response.status_code == 200:
                    result = response.json()  # Parse the JSON response
                    st.success(result["choices"][0]["message"]["content"].strip())  # Display the AI response
                else:
                    # Handle errors if the request was not successful
                    st.error(f"Failed to connect or retrieve response: {response.status_code} - {response.text}")
            except Exception as e:
                # Handle any exceptions that occur during the request
                st.error(f"Failed to connect or retrieve response: {str(e)}")
        else:
            # Warn the user if key or endpoint is missing
            st.warning("Please enter all the required details.")

if __name__ == "__main__":
    main()
