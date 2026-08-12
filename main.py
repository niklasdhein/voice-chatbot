# Speech Recognition stuff
import speech_recognition as sr

# Ollama stuff
import ollama
from ollama import chat
from ollama import ChatResponse

# Logger stuff
import logger

# Used for text to speech and playing audio
from gtts import gTTS
import pygame


# +--------+
# |  VARS  |
# +--------+

r = sr.Recognizer()
r.pause_threshold = 1.5

mic = sr.Microphone()

pygame.mixer.init()

dbg = logger.DebugLogger()
wng = logger.WarningLogger()

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Answer short and precise. Little humor allowed. Do NOT use smileys or emojis."
    }
]


# +-------------+
# |  FUNCTIONS  |
# +-------------+

def get_audio_input() -> AudioData:
    """
    Listens for audio input from the user and returns the audio data.
    """
    with mic as source:
        dbg.log("Listening..")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)
    return audio

def transcribe_audio(audio: AudioData) -> str:
    """
    Transcribes the given audio data to text using Google's speech recognition. If problems occur, empty string is returned.
    """
    try:
        transcription = r.recognize_google(audio, language="de-DE")
        return transcription
    except sr.UnknownValueError:
        wng.log("Could not understand what the user said")
        return ""
    except sr.RequestError as e:
        wng.log(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

def speak_response(response: str) -> None:
    """
    Converts the given text response to speech and plays it.
    """
    tts = gTTS(text=response, lang="de", slow=False)
    tts.save("output.mp3")
    pygame.mixer.music.load("output.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():    # Wait for the audio to finish playing
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()     # Unload the audio file to free up resources


# +-------------+
# |  MAIN LOOP  |
# +-------------+ 

if __name__ == "__main__":
    while True:
        # Get audio input from the user
        audio: AudioData = get_audio_input()

        # Try to transcribe what the user said
        dbg.log("Transcribing..")
        transcription: str = transcribe_audio(audio)
        print(f"User: {transcription}")

        if transcription != "":
            # Construct user message and append it to the messages list
            user_message = {
                "role": "user",
                "content": transcription
            }
            messages.append(user_message)

            # Get the model response
            response = chat(model='lfm2', messages=messages)

            # Print response to the console
            print(f"LLM: {response.message.content}")

            # Play the generated speech
            speak_response(response.message.content)

        # Check for exit condition
        if input("Any key to continue, 'q' to quit: ").strip().lower() == "q":
            dbg.log("Exiting..")
            break