#------------------------- IMPORTS

import streamlit as st
from openai import OpenAI
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import requests
import fitz  # PyMuPDF
from io import BytesIO


#-------------------------- Secrets from OPEN AI 
#Do Not push secrets to Github!

api_key = st.secrets["openai"]["api_key"]
default_assistant = st.secrets["openai"]["assistant_id"]
#For quickly running local put your API keys and comment out the above area
#api_key = "OPEN_AI_KEY"
#default_assistant = "Assistant ID"
isKeyed = True
# Boolean flag to determine if assistants should be fetched
fetch_assistants = True

#---------------------------- URL Transcriptions

# Function to get transcript or scraped text from URL
def get_transcript_from_url(url):
    if "youtube.com" in url or "youtu.be" in url:
        return get_youtube_transcript(url)
    else:
        return scrape_website(url)

# Function to get YouTube transcript
def get_youtube_transcript(url):
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return "Invalid YouTube URL"
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        print(f"Error retrieving YouTube transcript: {e}")
        return f"Error retrieving YouTube transcript: {e}"

# Function to extract video ID from YouTube URL
def extract_youtube_video_id(url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.match(pattern, url)
    return match.group(1) if match else None

# Function to scrape website content
def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract all text content from the website
        text = ' '.join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"❌Error scraping website: {e}"
    
#---------------------------------------------------- Text File Extraction PDF/TXT

# Function to read text from PDF file
def read_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"❌Error reading PDF file: {e}"

# Function to read text from TXT file
def read_txt(file):
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        return f"❌Error reading TXT file: {e}"
    
#----------------------------------------------------- Image Uploader

def attach_image_to_thread(attachment, thread_id):
    print(f"🔎Attaching file {attachment}")
    client = OpenAI(api_key=st.session_state.api_key)
    
    upload_response = client.files.create(
        purpose='vision',
        file=attachment
    )
    # Attach file to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[
            {
                "type": "text",
                "text": "Picture Uploaded"
            },
            {
                "type": "image_file",
                "image_file": {
                    "file_id": upload_response.id,
                    "detail": "high"
                }
            }
        ]
    )
    
#---------------------------------------------------- Open AI Thread and cleaning

# Clean Thread
def clean_create_thread(thread_id=None):
    client = OpenAI(api_key=st.session_state.api_key)
    st.session_state.messages = []
    if thread_id is None:
        try:
            # Create a new thread
            new_thread = client.beta.threads.create()
            print(f"New thread created with ID: {new_thread.id}")
            return new_thread.id
        except Exception as e:
            print(f"Error creating new thread: {e}")
            return None
    else:
        try:
            # Delete the specified thread
            client.beta.threads.delete(thread_id=thread_id)
            print(f"Thread {thread_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting thread: {e}")
            return None
        try:
            # Create a new thread
            new_thread = client.beta.threads.create()
            print(f"New thread created with ID: {new_thread.id}")
            return new_thread.id
        except Exception as e:
            print(f"Error creating new thread: {e}")
            return None
        
        
#----------------------------------------------------- StreamLit UI

# Starting Wide!

# Session States
st.session_state.setdefault('thread_id', None)
st.session_state.setdefault('assistant_id', default_assistant)
st.session_state.setdefault('api_key', api_key)

st.session_state.setdefault('systemPrompt', "You are a friendly and helpful assistant.")
st.session_state.setdefault('preprompt', "")
st.set_page_config(page_title="🕵️Assistant Agent🕵️", page_icon=":speech_balloon:",layout="wide")




# Sidebar settings
st.sidebar.header('🕵️ Assistant Agent 🕵️')
st.sidebar.image("https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHV6dmJjMmFic2lma3ZoaHJnaHY4d2VvMXJ0c3NpcTA3dGc5N2VoNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/kgAzAJl4eUZzO/giphy.webp")

if isKeyed:
    st.session_state.api_key = api_key
    st.session_state.assistant_id = default_assistant
else:
    st.session_state.api_key = st.sidebar.text_input('OpenAI API Key')
    st.session_state.assistant_id = st.sidebar.text_input('Assistant ID')


#--------------------------------------------------------------- Assistant List

def list_assistants():
    # Retrieve the list of assistants
    client = OpenAI(api_key=st.session_state.api_key)
    assistants = client.beta.assistants.list()
    
    # Initialize the options dictionary with the Default Assistant first
    options = {}

    for assistant in assistants.data:
        if assistant.name == "Default Assistant":
            options["Default Assistant"] = assistant.id
            break

    # Add the rest of the assistants to the options dictionary
    for assistant in assistants.data:
        if assistant.name != "Default Assistant":
            options[assistant.name] = assistant.id

    return options



# Fetch the assistants if the flag is set
if 'options' not in st.session_state and fetch_assistants:
    st.session_state.options = list_assistants()
    st.rerun()
else:
    st.session_state.assistant_id = st.session_state.options.get(default_assistant, None)

if fetch_assistants:
    # Create a sidebar with a dropdown menu
    selected_assistant = st.sidebar.selectbox("Assistants", list(st.session_state.options.keys()))
    st.session_state.assistant_id = st.session_state.options[selected_assistant]

#--------------------------------------------------------------- System Prompt and Thread buttons

use_system_prompt = st.sidebar.checkbox("Use System Prompt")

with st.sidebar.expander("System Settings"):
    st.session_state.systemPrompt = st.text_area(
        "System Prompt",
        "You are a friendly and helpful assistant.",
        height=5  # Reduced height value
    )
    st.session_state.preprompt = st.text_input("Preprompt")



with st.sidebar.expander("File Upload"):
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "txt"])
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

# Buttons
if st.sidebar.button("Clear/New Thread", use_container_width=True):
    if st.session_state.assistant_id == "":
        st.error("No assistant for thread")
    else:
        st.session_state.thread_id = clean_create_thread()
        
#------------------------------------------------------------------------ Stream end and File Upload Cleaning
        
def on_stream_done(user_input,agent_output):
    #a stub for accessing input and output
    print("AI Stream Done")
    
#This does not them Visually but ensures it only happens once
def reset_file_uploaders():
    print("Files Cleared")
    st.session_state.uploaded_file = None
    st.session_state.uploaded_image = None  


def main_chat(uploaded_file, uploaded_image):
    # Only show the chat interface if the chat has been started
    if st.session_state.assistant_id != "" and st.session_state.api_key != "":
        # Initialize the model and messages list if not already in session state
        client = OpenAI(api_key=st.session_state.api_key)
        if "messages" not in st.session_state:
            st.session_state.messages = []
        # Display existing messages in the chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        # Chat input for the user
        if prompt := st.chat_input("What is up?"):
            if prompt.lower() == "/clear" or prompt.lower() == "/clean":
                st.session_state.thread_id = clean_create_thread()
                return
            if st.session_state.thread_id is None:
                st.session_state.thread_id = clean_create_thread()
                st.empty()

            # Prepend preprompt to the user's input
            prompt = f"{st.session_state.preprompt} {prompt}".strip()
            # Detect URLs in the prompt and replace with transcripts or scraped text for processing
            urls = re.findall(r'(https?://\S+)', prompt)
            processed_prompt = prompt
            for url in urls:
                transcript = get_transcript_from_url(url)
                processed_prompt = processed_prompt.replace(url, transcript)

            # Add file content if a file was uploaded
            if uploaded_file is not None:
                if uploaded_file.type == "application/pdf":
                    file_text = read_pdf(uploaded_file)
                elif uploaded_file.type == "text/plain":
                    file_text = read_txt(uploaded_file)
                else:
                    file_text = "Unsupported file type."
                # Add the file text to the processed prompt
                processed_prompt += "\n" + file_text
                # Add the file name to the user message
                prompt += f"\nFile: {uploaded_file.name}"

            # Add image content if an image was uploaded
            if uploaded_image is not None:
                st.session_state.messages.append({"role": "user", "content": "Image uploaded"})
                # with st.chat_message("user"):
                #     st.image(uploaded_image)
                attach_image_to_thread(uploaded_image, st.session_state.thread_id)
                
            # Add user message to the state and display it (keep original URL and file name)
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                if(uploaded_image) is not None:
                    prompt = prompt + " Image uploaded: " + uploaded_image.name
                st.markdown(prompt)
            print(processed_prompt)
            # Add the processed message to the existing thread
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=processed_prompt
            )
            # Clear uploaded files if the flag is set
            reset_file_uploaders()
            # Streaming run    
            streamingText = ""
            if use_system_prompt:
                with st.chat_message("assistant"):
                    with client.beta.threads.runs.stream(
                      thread_id=st.session_state.thread_id,
                      assistant_id=st.session_state.assistant_id,
                    ) as stream:
                        response = st.write_stream(stream.text_deltas)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    on_stream_done(prompt,response)
            else:
                 with st.chat_message("assistant"):
                    with client.beta.threads.runs.stream(
                      thread_id=st.session_state.thread_id,
                      assistant_id=st.session_state.assistant_id,
                    ) as stream:
                        response = st.write_stream(stream.text_deltas)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    on_stream_done(prompt,response)
    else:
        # Prompt to start the chat
        st.header('Enter API Key and Assistant ID', divider='rainbow')
        st.image("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGlqcGxmaHE2ajM3YnBrMGV0dDdwbTF6NXd5aWM2MXJzMWZubWpqayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/273P92MBOqLiU/giphy.gif")


main_chat(uploaded_file, uploaded_image)



# Display current data
st.sidebar.markdown(f"ThreadID: ```{st.session_state.thread_id}```")
st.sidebar.markdown(f"Assistant: ```{st.session_state.assistant_id}```")
st.sidebar.link_button("Set your Assistant here", "https://platform.openai.com/assistants")

