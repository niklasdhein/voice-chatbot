# AVA - Autonomous Voice Assistant

Ein lokaler, sprachgesteuerter KI-Assistent für den Desktop mit integrierter Agenten- und Tool-Calling-Architektur.

AVA kombiniert lokale Spracherkennung (**Faster-Whisper**), lokale Sprachmodelle via **Ollama** und natürliche Sprachausgabe (**Edge-TTS**). Über ein integriertes Tool-Set kann der Assistent Aufgaben auf dem System autonom planen und ausführen (z. B. Terminal-Befehle, Dateioperationen, Browsersteuerung).

---

## Architektur-Übersicht

```
[ Mikrofon ]
     │
     ▼
[ Faster-Whisper ]  ── (Speech-to-Text, lokal)
     │
     ▼
[ Ollama (LLM) ]    ── (Reasoning, Plan-Erstellung & Tool-Auswahl)
     │   ▲
     │   └── [ Tools: Shell, Browser, File I/O, Task Planning ]
     ▼
[ Edge-TTS ]        ── (Text-to-Speech)
     │
     ▼
[ Pygame Mixer ]    ── (Audio-Ausgabe)
```

---

## Features

- **Lokale Spracherkennung**: Transkription via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (schnell, präzise und offline).
- **Lokale LLM-Integration**: Unterstützung für Modelle via [Ollama](https://ollama.com/) (z. B. Gemma, Qwen).
- **Autonome Agenten-Fähigkeiten**:
  - Zerlegen komplexer Aufgaben in mehrstufige Ausführungspläne (`create_execution_plan`).
  - Terminal-Befehle ausführen (`execute_terminal_command`).
  - Dateien lesen, schreiben und zeilenbasiert manipulieren (`read_file_with_line_numbers`, `replace_lines`, `insert_at_line`).
  - Webbrowser öffnen und suchen (`open_browser`).
- **Natürliche Sprachausgabe**: Hochwertige deutsche Sprachausgabe via `edge-tts`.
- **Standby-Modus**: Ein- und Ausschalten per Sprachbefehl (`"standby"`).

---

## Voraussetzungen

- **Python 3.10+**
- **[Ollama](https://ollama.com/)** (installiert und gestartet)
  ```bash
  ollama pull gemma4:latest
  # Alternativ: qwen2.5:7b, etc.
  ```
- **System-Abhängigkeiten** (z. B. für Audio / PyAudio):
  - Ubuntu/Debian: `sudo apt install python3-pyaudio portaudio19-dev ffmpeg`
  - Arch Linux: `sudo pacman -S portaudio ffmpeg`

---

## Installation & Schnellstart

1. **Repository klonen**:
   ```bash
   git clone https://github.com/niklasdhein/voice-chatbot.git
   cd voice-chatbot
   ```

2. **Virtuelle Umgebung erstellen & Abhängigkeiten installieren**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Assistenten starten**:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   *Oder direkt über Python:*
   ```bash
   python3 main.py
   ```

---

## Projektstruktur

```
voice-chatbot/
├── agent/
│   └── soul.txt          # System-Prompt & Identitätsdefinition des Assistenten
├── agent_test.py         # Test-Harness für interaktive Agent-Aufgaben im Terminal
├── autostart.sh          # Starter-Skript für Autostart/Terminal
├── logger.py             # Benutzerdefinierte Debug- & Warning-Logger
├── main.py               # Haupteinstiegspunkt (Speech Loop, Agent & Audio-I/O)
├── requirements.txt      # Python-Abhängigkeiten
├── run.sh                # Portables Startskript
└── tools.py              # Tool-Definitionen für das LLM (Dateisystem, Shell, Browser)
```

---

## Sprachsteuerung & Befehle

- **Standby aktivieren / deaktivieren**: Sagen Sie *"Standby"* (pausiert die Verarbeitung oder reaktiviert AVA).
- **Beenden**: Sagen Sie *"Ausführung beenden"*.

---

## Sicherheitshinweis

> [!CAUTION]
> Das Tool `execute_terminal_command` erlaubt dem LLM die direkte Ausführung von Shell-Befehlen. Dieses Projekt wurde für persönliche Test- und Prototyping-Zwecke auf lokalen Maschinen entwickelt. Für den produktiven Einsatz wird eine Sandbox-Umgebung (z. B. Docker/Container) empfohlen.
