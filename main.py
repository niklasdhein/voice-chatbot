import speech_recognition as sr
import logger

# Vars
r = sr.Recognizer()
r.pause_threshold = 1.5

dbg = logger.DebugLogger()
wng = logger.WarningLogger()

mic = sr.Microphone(device_index=0)

if __name__ == "__main__":
    while True:
        # Listening for user to talk
        with mic as source:
            dbg.log("Listening..")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source)

        # Try to transcribe what the user said
        dbg.log("Transcribing..")
        try:
            transcription = r.recognize_google(audio, language="de-DE")
            print(f"> {transcription}")
        except UnknownValueError:
            wng.log("Could not understand what the user said")

        # Check for exit condition
        if input("Any key to continue, 'q' to quit: ").strip().lower() == "q":
            dbg.log("Exiting..")
            break