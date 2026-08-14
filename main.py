# Speech Recognition stuff
import io
from faster_whisper import WhisperModel
import speech_recognition as sr

# Ollama stuff
import ollama
from ollama import chat
from ollama import ChatResponse

# Logger stuff
import logger

# Used for text to speech and playing audio
import asyncio
import edge_tts
import pygame

# Tools the LLM may use
import tools as t

import os


# +--------+
# |  VARS  |
# +--------+

r = sr.Recognizer()
r.pause_threshold = 1.5
r.non_speaking_duration = 0.8

mic = sr.Microphone()

pygame.mixer.init()

dbg = logger.DebugLogger()
wng = logger.WarningLogger()

AI_NAME = "AVA"
MODEL_NAME = "gemma4:latest"     # Available lfm2, qwen2.5:7b, gemma4:latest
ROOT_PATH = "/home/niklas/Dokumente/python/speech-recognizer/"

whisper = WhisperModel("small", device="cpu", compute_type="int8")    # cuda für gpu

messages = [
    {
        "role": "system",
        "content": f"Du bist {AI_NAME}, ein nützlicher Assistent."
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

def transcribe_audio(audio: sr.AudioData) -> str:
    """
    Transcribes the given audio data to text using Google's speech recognition. If problems occur, empty string is returned.
    """
    dbg.log("Transcribing..")

    wav_bytes = audio.get_wav_data()    # AudioData to wav format
    wav_stream = io.BytesIO(wav_bytes)  # Convert to Byte stream
    
    segments, info = whisper.transcribe(wav_stream, language="de")

    text = "".join([segment.text for segment in segments]).strip()
    return text if text != "copyright wdr 2020" else ""

def speak_response(response: str) -> None:
    """
    Converts the given text response to speech and plays it.
    """
    async def _generate():
        communicate = edge_tts.Communicate(response, "de-DE-KatjaNeural", rate="+50%")
        await communicate.save(f"{ROOT_PATH}tmp/output.mp3")
    
    dbg.log("Generating speech..")

    asyncio.run(_generate())    # Generates output mp3 file

    pygame.mixer.music.load(f"{ROOT_PATH}tmp/output.mp3")
    dbg.log("Speaking..")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():    # Wait for the audio to finish playing
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()             # Unload the audio file to free up resources
    os.remove(f"{ROOT_PATH}tmp/output.mp3") # Prevent many files existing in different places, when working directories get changed, etc

def adjust_recognizer(recognizer: sr.Recognizer, microphone: sr.Microphone, duration: float=0.5) -> None:
    """
    Takes the recognizer used for speech recognition and adjusts it for a given duration to the ambient noise.
    """
    dbg.log("Adjusting for ambient noise..")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=duration)

def execute_plan_call(call) -> str:
    # Creates the plan as dictionary
    plan = t.create_execution_plan(**call.function.arguments)

    # Prepare a new temporary list of messages specifically for the plan execution
    msgs = [{
        "role": "system",
        "content": f"Du bist ein KI Agent, der einen Plan abarbeitet. Hier die Zusammenfassung des gesamten Plans: {plan["summary"]}"
    }]

    # Go through each step
    for key in plan["steps"]:
        print(f"Working on task '{key}'..")
        msgs.append({
            "role": "system",
            "content": f"Du arbeitest an folgendem Schritt des Plans: {key}. Hier eine genaue Beschreibung deiner Aufgabe: {plan["steps"][key]}. Nutze deine Tools, um die Aufgabe zu lösen."
        })
        
        # Work on that task until completed
        for i in range(10):
            print(f"Try {i+1} running..")
            resp = ask_assistant(msgs)  # Get a response from the agent

            # If a tool call is requested, what hopefully had been, execute the tool
            if resp.message.tool_calls:
                call = resp.message.tool_calls[0]

                if call.function.name == "mark_task_as_completed":
                    msgs.append({
                        "role": "system",
                        "content": f"Du hast die Aufgabe '{key}' als erledigt gekennzeichnet. Die nächste Aufgabe wird dir bereitgestellt."
                    })
                    print("Task solved.")
                    break

                print(f"Executing '{call.function.name}' with args '{call.function.arguments}'..")
                ret = execute_tool_call(call)
                msgs.append({
                    "role": "system",
                    "content": f"Du hast '{call.function.name}' mit Args '{call.function.arguments}' aufgerufen und das Tool hat folgendes returnt: {ret} - Wenn Du deine aktuelle Aufgabe erledigt hast, markiere sie als erledigt"
                })
    
    # Return information on how the plan execution went
    return "Alle Schritte des Plans ausgeführt"


def execute_tool_call(call) -> str:
    """
    Executes the tool for the given tool call. The function passes the return of the tool as a string.
    If no tool was found for the given call 'Tool <function_name> not found' will be returned.
    """
    function_name = call.function.name
    arguments =     call.function.arguments

    # Handle plan usage in a seperate function
    if function_name == "create_execution_plan":
        execute_plan_call(call)
        return "Plan ausgeführt"

    # Match the called tool to an actual tool to call
    for f in t.available_functions:
        if f.__name__ != function_name: continue
        
        # Execute the function for that tool
        ret = f(**arguments)

        # Pass through the tool return as string
        return str(ret)
    
    return f"Tool {function_name} nicht gefunden"

def ask_assistant(m: list(dict)) -> ChatResponse:
    return chat(model=MODEL_NAME, messages=m, tools=t.available_functions)

# +-------------+
# |  MAIN LOOP  |
# +-------------+ 

if __name__ == "__main__":
    # Read soul.txt and append the content to messages
    dbg.log("Reading soul..")
    with open(f"{ROOT_PATH}agent/soul.txt", "r") as f:
        messages.append({"role": "system", "content": f.read()})

    # Adjust for ambient noise to calibrate the microphone
    dbg.log("Calibrating microphone..")
    adjust_recognizer(r, mic, 0.5)

    while True:
        # Get audio input from the user
        audio: AudioData = get_audio_input()

        # Get transcription, if not understood "" is returned
        transcription: str = transcribe_audio(audio)
        dbg.log(f"User: {transcription}")

        # Continue if the transcription was empty
        if transcription == "": continue

        # Check for exit
        if "ausführung beenden" in transcription.lower():
            dbg.log("Exiting..")
            break

        # Append what the user said in the right format to messages
        messages.append({"role": "user", "content": f"{transcription} - Wenn notwendig, erstelle einen Ausführungsplan, um komplexe Aufgaben Stück für Stück zu lösen"})

        # Get a response from the model
        resp: ChatResponse =    ask_assistant(messages)
        resp_msg: str =         resp.message.content
        
        # Execute tool call if requested, also let the LLM react to the tool outcome
        if resp.message.tool_calls:
            call = resp.message.tool_calls[0]
            ret = execute_tool_call(call)
            messages.append({
                "role": "system",
                "content": f"Du hast '{call.function.name}' mit Args '{call.function.arguments}' aufgerufen und das Tool hat folgendes returnt: {ret} - Werte aus"
            })
            resp = ask_assistant(messages)
            resp_msg = resp.message.content

        # Print the LLM response
        print(f"{AI_NAME}: {resp_msg}")
        
        # Play the text-to-speech
        if resp_msg.strip() != "": speak_response(resp_msg)