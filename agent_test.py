from pathlib import Path
from ollama import chat
from ollama import ChatResponse
from logger import DebugLogger
import tools
import json

MODEL_NAME = "gemma4:latest"
BASE_DIR = Path(__file__).resolve().parent

debug = DebugLogger()
messages = []
soul_path: Path = BASE_DIR / "agent" / "soul.txt"
if soul_path.exists(): messages.append({"role": "system", "content": soul_path.read_text()})

def handle_task(task: str) -> str:    
    """
    This tool allows the LLM to perform tasks given by the user.
    The passed 'task' MUST ALWAYS be in .json format following this specific structure:
    {"summary": "<short summary of the task>", "steps": ["<step 1>", "<step 2>", ..]}
    'steps' is a list of strings, that desribe the given task in smaller steps to process each step by step.
    """
    
    # Tools the LLM may use for working on tasks
    TOOLS = [
        tools.execute_terminal_command,
        tools.read_file_with_line_numbers,
        tools.write_file,
        tools.insert_at_line,
        tools.change_directory,
        tools.mark_step_as_complete
    ]

    try:
        task_dictionary: dict = json.loads(task)
    except Exception as e:
        return f"Fehler: {e}"
    summary =   task_dictionary["summary"]
    steps =     task_dictionary["steps"]
    print(f"Summary: {summary}")
    for i in range(len(steps)):
        print(f"\t{i+1}. {steps[i]}")

    completed_steps = []
    step_messages = [{
        "role": "system",
        "content": f"Du bist ein Assistant und arbeitest eine Reihe an Aufgaben ab. Folgende Aufgaben hast du bereits erledigt: {', '.join(completed_steps) if completed_steps else 'keine'}."
    }]

    for step in steps:
        print(f"Working on step '{step}'..")
        iteration_counter = 0
        step_complete = False
        step_messages.append({"role": "user", "content": f"Bearbeite nun folgende Aufgabe: {step}."})
        while not step_complete:
            print(f"Iteration {iteration_counter}..")
            step_response: str = chat(model=MODEL_NAME, messages=step_messages, tools=TOOLS)
            print(f"\033[96m{step_response.message.thinking}\033[0m") if step_response.message.thinking else print("\033[96m(Was not thinking)\033[0m")
            if step_response.message.tool_calls:
                call = step_response.message.tool_calls[0]
                try:
                    print(f"\t* Calling '{call.function.name}' with args {call.function.arguments}..")
                    tool_return: str = getattr(tools, call.function.name)(**call.function.arguments)
                    print(f"\t* Returned '{tool_return}'")
                    step_messages.append({"role": "tool", "tool_name": call.function.name, "content": str(tool_return)})
                    if call.function.name == "mark_step_as_complete":
                        step_complete = True
                        completed_steps.append(step)
                        break
                    step_messages.append({"role": "user", "content": f"Das Tool '{call.function.name}' wurde mit den Argumenten {call.function.arguments} aufgerufen und hat '{tool_return}' returned. Wenn du mit dem Ergebnis zufrieden bist, markiere den Schritt als beendet."})
                except Exception as e:
                    print(f"Error: {e}")
                    exit(1)
            else:
                step_messages.append({"role": "user", "content": "Du hast kein Tool aufgerufen. Bitte rufe ein Tool auf, um den Schritt zu bearbeiten."})
            iteration_counter += 1
    
    return "Die Aufgabe wurde ohne Fehler bearbeitet."

def get_letter_count(m: list[dict]) -> int:
    return len(str(m))

# Prompt - Response loop
while True:
    # Get users input
    user_input = input("> ")
    if "/quit" in user_input.strip().lower(): break
    messages.append({"role": "user", "content": user_input})

    # Model response
    response: ChatResponse = chat(model=MODEL_NAME, messages=messages, tools=[handle_task])
    messages.append(response.message)
    print(f"\033[96m{response.message.thinking}\033[0m") if response.message.thinking else print("\033[96m(Was not thinking)\033[0m")
    if response.message.tool_calls and response.message.tool_calls[0].function.name == "handle_task":
        messages.append({"role": "tool", "tool_name": "handle_task", "content": handle_task(**response.message.tool_calls[0].function.arguments)})
        response: ChatResponse = chat(model=MODEL_NAME, messages=messages)
        messages.append(response.message)
    print(f"AI: {response.message.content}")
    
    print(f"\tmessages consists of {get_letter_count(messages)} letters.")