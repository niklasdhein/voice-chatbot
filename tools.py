from logger import WarningLogger
import subprocess
from datetime import datetime

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
    with open(filepath, "r") as f:
        content = f.read()
    return content

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
    append_to_file
]