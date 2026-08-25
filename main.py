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
from pathlib import Path

# +--------+
# |  VARS  |
# +--------+

r = sr.Recognizer()
r.pause_threshold = 1.5
r.non_speaking_duration = 1.5

mic = sr.Microphone()

pygame.mixer.init()

dbg = logger.DebugLogger()
wng = logger.WarningLogger()

AI_NAME = "AVA"
MODEL_NAME = "gemma4:latest"     # Available lfm2, qwen2.5:7b, gemma4:latest
ROOT_PATH = "/home/niklas/Dokumente/python/speech-recognizer/"

whisper = WhisperModel("small", device="cpu", compute_type="int8")    # cuda für gpu

messages = []


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
    plan: dict = t.create_execution_plan(**call.function.arguments)   # Creates a execution plan formatted as a dictionary
    dbg.log(f"Plan: '{plan}'")

    base_system_prompt = {
    "role": "system",
    "content": (
        f"Du bist ein autonomer KI-Agent. Dein Ziel: Abarbeiten eines Plans.\n"
        f"Plan-Zusammenfassung: {plan['summary']}\n\n"
        "REGELN:\n"
        "- Führe Tools aus, um die Aufgaben zu lösen.\n"
        "- Wenn du eine Teilaufgabe komplett gelöst hast, RUFE ZWINGEND das Tool 'mark_task_as_completed' auf.\n"
        "- Schreibe keine Zusammenfassungen für den Nutzer, arbeite stumm deine Tools ab."
        )
    }

    # Track finished tasks as lightweight context for subsequent steps
    completed_tasks = []

    for key in plan["steps"]:
        print(f"\nWorking on task '{key}'..")
        
        # Fresh msgs list for EACH task step
        msgs = [base_system_prompt]

        # Provide lightweight summary of already finished steps
        if completed_tasks:
            msgs.append({
                "role": "system",
                "content": f"Bisher bereits erledigte Schritte in diesem Plan:\n- " + "\n- ".join(completed_tasks)
            })

        # Add current task instruction
        msgs.append({
            "role": "user",
            "content": f"Starte jetzt mit Aufgabe: {key}\nBeschreibung: {plan['steps'][key]}"
        })
        
        # Work on the current step with a maximum amount of iterations / trys
        max_iterations_for_step = 10
        solved = False
        for i in range(max_iterations_for_step):
            if solved: break
            
            # Get model response for the current iteration
            print(f"* Step '{key}' try {i+1}")
            resp = ask_assistant(msgs)
            msgs.append(resp.message)
            
            # Go through all tool calls
            if resp.message.tool_calls:
                for call in resp.message.tool_calls:
                    # Check if LLM wants to move on to next step of the plan
                    if call.function.name == "mark_task_as_completed":
                        print("Task solved.")
                        completed_tasks.append(f"{key}: {plan['steps'][key]}")
                        solved = True

                    dbg.log(f"Executing Tool: {call.function.name}")
                    ret: str = execute_tool_call(call)

                    # Append tool response with tool role
                    msgs.append({
                        "role": "tool",
                        "name": call.function.name,
                        "content": str(ret)
                    })

                msgs.append({
                    "role": "user",
                    "content": "Alle Tools ausgeführt, wenn du mit dem Ergebnis zufrieden bist, rufe 'mark_task_as_completed' auf."
                })
            else:
                msgs.append({
                    "role": "user",
                    "content": "Du hast kein Tool aufgerufen. Erledige deine Aufgabe durch Toolaufrufe. Wenn du fertig bist markiere diese als erledigt."
                })
    
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
        return execute_plan_call(call)

    # Match the called tool to an actual tool to call
    for f in t.available_functions:
        if f.__name__ != function_name: continue
        
        print(f"Executing '{call.function.name}' with args '{call.function.arguments}'..")

        # Execute tool with error handling
        try:
            ret = f(**arguments)
            print(f"Tool returned '{ret}'")
            return str(ret)
        except TypeError as e:
            # Catches missing parameters like missing 'search_text' and informs the agent
            wng.log(f"Fehler bei Ausführung des Tools '{function_name}': Ungültige Argumente ({e}). Bitte mit allen benötigten Argumenten erneut probieren.")
            return f"Fehler bei Ausführung des Tools '{function_name}': Ungültige Argumente ({e}). Bitte mit allen benötigten Argumenten erneut probieren."
        except Exception as e:
            wng.log(f"Fehler bei Ausführung des Tools '{function_name}': {e}")
            return f"Fehler bei Ausführung des Tools '{function_name}': {e}"
    
    return f"Tool {function_name} nicht gefunden"

def ask_assistant(m: list(dict)) -> ChatResponse:
    return chat(
        model=MODEL_NAME, 
        messages=m, 
        tools=t.available_functions,
        options={
            "num_ctx": 8192  # Gives the LLM more space for code
        }
    )


# +-------------+
# |  MAIN LOOP  |
# +-------------+ 

if __name__ == "__main__":
    dbg.log("Reading soul..")
    
    # Read Soul
    soul_path = Path(ROOT_PATH) / "agent" / "soul.txt"
    if soul_path.exists():
        messages.append({"role": "system", "content": soul_path.read_text(encoding="utf-8")})

    dbg.log("Calibrating microphone..")
    adjust_recognizer(r, mic, 0.5)

    standby = True
    while True:
        # Print warning message for when in standby
        if standby: wng.log("In standby.")

        # 1. Record audio and transcribe
        audio: AudioData = get_audio_input()
        transcription: str = transcribe_audio(audio)
        print(f"User: {transcription}")
        
        # Check for keywords / trigger-words
        # Exit the program
        if "ausführung beenden" in transcription.lower():
            dbg.log("Exiting..")
            break

        # Toggle standby
        elif "standby" in transcription.lower() or "stand-by" in transcription.lower() or "stand by" in transcription.lower(): 
            dbg.log("Resuming from standby.." if standby else "Switching to standby..")
            standby  = not standby
            continue

        # Skip if in standby or no speech was detected
        if not transcription.strip() or standby:
            continue

        # 2. User message
        messages.append({"role": "user", "content": transcription})

        # Trim context, keep system prompt and last 10 messages
        if len(messages) > 12:
            messages = [messages[0]] + messages[-10:]

        # 3. Request first respond from model
        try:
            resp: ChatResponse = ask_assistant(messages)
        except Exception as e:
            dbg.log(f"Ollama Error: {e}")
            speak_response("Entschuldigung, ich hatte ein Problem beim Verarbeiten.")
            continue
        
        # 4. Tool loop, as long as the LLM wants to call tools execute them
        while resp.message.tool_calls:
            # LLM response has to be appended in messages
            messages.append(resp.message.content)

            for call in resp.message.tool_calls:
                ret: str = execute_tool_call(call)

                # Append tool response with tool role
                messages.append({
                    "role": "tool",
                    "name": call.function.name,
                    "content": str(ret)
                })

            # Request next step from LLM (another tool or response)
            resp = ask_assistant(messages)

        # 5. Save final answer and print
        resp_msg: str = resp.message.content or ""
        
        messages.append({
            "role": "assistant",
            "content": resp_msg
        })

        print(f"{AI_NAME}: {resp_msg}")
        
        if resp_msg.strip():
            speak_response(resp_msg)