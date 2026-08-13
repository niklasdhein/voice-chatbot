from logger import WarningLogger
import subprocess
from datetime import datetime

wng = WarningLogger()

def open_firefox(search_term: str="") -> str:
    """
    Opens Firefox browser. Optionally uses default search engine to search the given term.
    """
    try:
        if search_term != "":
            subprocess.Popen(['firefox', '--search', search_term])
            return f"Started successfully and searched for {search_term}"
        else:
            subprocess.Popen(['firefox'])
            return "Started successfully"
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
    Executes a bash command in the terminal and returns the output or error.
    Use this for file management, system checks, or running installed CLI tools.
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

# Include all tools that may be used by LLMs here
available_functions = [
    open_firefox,
    open_url,
    open_terminal,
    execute_terminal_command,
    get_current_date_and_time
]