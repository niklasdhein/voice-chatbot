from logger import WarningLogger
import subprocess
from datetime import datetime
import os
import json

wng = WarningLogger()

def open_firefox() -> str:
    "Opens the Firefox browser."
    try:
        subprocess.Popen(['firefox'])
        return "Started successfully"
    except FileNotFoundError:
        return "Couldn't find firefox"

def open_firefox_with_search(search_term: str="") -> str:
    """
    Opens Firefox browser. Uses default search engine to search the given term.
    """
    try:
        subprocess.Popen(['firefox', '--search', search_term])
        return f"Started successfully and searched for {search_term}"
    except FileNotFoundError:
        return "Couldn't find firefox"

def open_url(url: str) -> str:
    """
    Opens a URL in firefox.
    """
    try:
        subprocess.Popen(['firefox', '--new-window', url])
        return f"Opened {url} in a new window"
    except FileNotFoundError:
        return "Couldn't find firefox"

def open_terminal() -> None:
    """
    Opens konsole.
    """
    subprocess.Popen(['konsole'])

def execute_terminal_command(command: str) -> str:
    """
    Executes a command in the terminal and returns the output or error.
    Use this for file management, system checks, or running installed CLI tools.
    The default terminal app used is 'konsole'.
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            text=True, 
            capture_output=True, 
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout else "Command executed successfully"
        return f"Error (Exit-Code {result.returncode}): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Hit timeout of 10sec"
    except Exception as e:
        return f"Error while executing: {e}"

def get_current_date_and_time() -> str:
    """
    Returns current date, time and day of the week.
    """
    now = datetime.now()
    return now.strftime("%A, %d. %B %Y - %H:%M Uhr")

def read_file(filepath: str) -> str:
    """
    Returns the content of a given filepath interpreted as text and returns the string.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Path {filepath} does not exist"
    except PermissionError:
        return f"Missing read-permissions for path {filepath}"
    except OSError as e:
        return f"A file error occured: {e}" 

def overwrite_file(filepath: str, content: str) -> str:
    """
    Overwrites the content of the file specified through filepath. If this file does not exist, a new one will be created.
    Be careful.
    """
    try:
        with open(filepath, "w") as f:
            f.write(content)
        return "File written successfully"
    except FileNotFoundError:
        return f"Path {filepath} does not exist"
    except PermissionError:
        return f"Missing write-permissions for path {filepath}"
    except OSError as e:
        return f"A file error occured: {e}"

def append_to_file(filepath: str, content: str) -> str:
    """
    Appends the given content onto the file specified through filepath. If this file does not exist, a new one will be created.
    """
    try:
        with open(filepath, "a") as f:
            f.write(content)
        return "Appended content to file successfully"
    except FileNotFoundError:
        return f"Path {filepath} does not exist"
    except PermissionError:
        return f"Missing write-permissions for path {filepath}"
    except OSError as e:
        return f"A file error occured: {e}"

def change_directory(dirpath: str) -> str:
    """
    Changes the directory to the given directory path.
    """
    if os.path.exists(dirpath): 
        os.chdir(dirpath)
        return f"Changed directory to {dirpath}"
    else: return f"The path {dirpath} does not exist"


# +-----------------+
# |  SPECIAL TOOLS  |
# +-----------------+

def create_execution_plan(plan_json: str) -> dict:
    """
    This function takes the execution plan used to tackle more complex task as a string in json format.
    Only use correct json syntax. Remember that also keys need to be inside of double-quotes.
    The passed json needs to be of this format: {"summary": <short summary of the plan>, "steps": {<step_name>: <step_description>, ...}}
    Internally it reformats that json to a python dictionary to be able to use it directly in the code to track progress.
    The steps need to be this simple, that they can be accomplished with given tools.
    """
    print(f"Received plan {plan_json}")
    try:
        return json.loads(plan_json)
    except json.JSONDecodeError as e:
        return f"Der folgende JSON-String ist nicht gültig: {plan_json}"

def mark_task_as_completed() -> True:
    """
    If you sucessfully achieved to goal of your task, call this tool to move on to the next one.
    It returns True so that the program can handle the logic for serving the next task.
    """
    return True

# Include all tools that may be used by LLMs here
available_functions = [
    open_firefox,
    open_firefox_with_search,
    open_url,
    open_terminal,
    execute_terminal_command,
    get_current_date_and_time,
    read_file,
    overwrite_file,
    append_to_file,
    change_directory,
    create_execution_plan,
    mark_task_as_completed
]