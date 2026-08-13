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

# Tools the LLM may use
import tools as t


# +--------+
# |  VARS  |
# +--------+

r = sr.Recognizer()
r.pause_threshold = 1.5

mic = sr.Microphone()

pygame.mixer.init()

dbg = logger.DebugLogger()
wng = logger.WarningLogger()

AI_NAME = "AVA"
MODEL_NAME = "lfm2"     # Available lfm2, qwen2.5:7b

messages = [
    {
        "role": "system",
        "content": f"Du bist {AI_NAME}, ein nützlicher Assistent. Antworte kurz und präzise. Minimaler Humor erlaubt. Benutze KEINE Smileys oder Emojis."
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
        audio = r.listen(source)

    return audio

def transcribe_audio(audio: AudioData) -> str:
    """
    Transcribes the given audio data to text using Google's speech recognition. If problems occur, empty string is returned.
    """
    dbg.log("Transcribing..")
    try:
        transcription = r.recognize_google(audio, language="de-DE")
        return transcription.lower().strip()
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

def adjust_recognizer(recognizer: sr.Recognizer, microphone: sr.Microphone, duration: float=0.5) -> None:
    """
    Takes the recognizer used for speech recognition and adjusts it for a given duration to the ambient noise.
    """
    dbg.log("Adjusting for ambient noise..")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=duration)


# +-------------+
# |  MAIN LOOP  |
# +-------------+ 

if __name__ == "__main__":
    # Adjust for ambient noise to calibrate the microphone
    adjust_recognizer(r, mic, 0.5)

    while True:
        # Get audio input from the user
        audio: AudioData = get_audio_input()

        # Try to transcribe what the user said
        transcription: str = transcribe_audio(audio)
        print(f"User: {transcription}")

        # Check for exit
        if transcription == "beenden" or transcription == "aus":
            dbg.log("Exiting..")
            break

        if transcription != "":
            # Construct user message and append it to the messages list
            messages.append({"role": "user", "content": transcription})

            # Get the model response
            response = chat(model=MODEL_NAME, messages=messages, tools=t.available_functions)

            # Perform tool call
            if response.message.tool_calls:
                call = response.message.tool_calls[0]
                function_name = call.function.name
                arguments = call.function.arguments
                for i in range(len(t.available_functions)):
                    if t.available_functions[i].__name__ == function_name:
                        result = t.available_functions[i](**arguments)
                        messages.append({"role": "system", "content": f"Aufgerufenes Tool: {function_name}, Argumente: {arguments}, Return: {str(result)}. Werte das Ergebnis aus."})
                        dbg.log(f"{MODEL_NAME} called tool {function_name} with args {arguments}, got result: {str(result)}")

                        # Feed back the result to the LLM to evaluate
                        response = chat(model=MODEL_NAME, messages=messages)
                        break

            # Print response to the console
            print(f"{AI_NAME}: {response.message.content}")

            # Play the generated speech
            response_content = response.message.content
            if response_content.strip() != "":
                speak_response(response_content)