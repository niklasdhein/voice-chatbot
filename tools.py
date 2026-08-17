from logger import WarningLogger
import subprocess
from datetime import datetime
import os
import json
from pathlib import Path

wng = WarningLogger()


# +-------------------------+
# |  APPLICATION LAUNCHERS  |
# +-------------------------+

def open_browser(target: str = "") -> str:
    """
    Opens Firefox browser. Accepts a search term, a full URL, or an empty string for default startup.
    Use absolute path when passing files as URL.
    """
    try:
        if not target:
            subprocess.Popen(['firefox'])
            return "Firefox started successfully."
        
        if target.startswith(("http://", "https://", "file://")):
            subprocess.Popen(['firefox', '--new-window', target])
            return f"Opened URL '{target}' in a new Firefox window."
        
        subprocess.Popen(['firefox', '--search', target])
        return f"Started Firefox and searched for '{target}'."
    except FileNotFoundError:
        return "Error: Firefox executable not found."

def open_terminal() -> str:
    """
    Opens the default terminal application (konsole).
    """
    try:
        subprocess.Popen(['konsole'])
        return "Opened terminal (konsole) successfully."
    except FileNotFoundError:
        return "Error: Konsole executable not found."


# +---------------------+
# |  COMMAND EXECUTION  |
# +---------------------+

def execute_terminal_command(command: str, cwd: str = None) -> str:
    """
    Executes a command in the shell and returns output or error.
    Optional 'cwd' sets the working directory for the command execution.
    """
    try:
        # Fallback to current working directory if not explicitly provided
        working_dir = cwd if cwd and os.path.exists(cwd) else os.getcwd()
        
        result = subprocess.run(
            command, 
            shell=True, 
            text=True, 
            capture_output=True, 
            timeout=10,
            cwd=working_dir
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return output if output else "Command executed successfully with no output."
        return f"Error (Exit Code {result.returncode}): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 10 seconds."
    except Exception as e:
        return f"Execution error: {e}"


# +------------------+
# |  DATA GATHERING  |
# +------------------+

def get_current_date_and_time() -> str:
    """
    Returns current date, time, and day of the week in a structured format.
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S (%A)")


# +--------------------+
# |  FILE INTERACTION  |
# +--------------------+

def replace_lines(filepath: str, start_line: int, end_line: int, new_content: str) -> str:
    """
    Replaces lines from start_line to end_line (inclusive, 1-indexed) in a file with new_content.
    To delete lines, pass an empty string for new_content.
    It is advised to use smaller texts to stay inside the context window.
    """
    path = Path(filepath)
    if not path.exists():
        return f"Error: File '{filepath}' does not exist."

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Validation of line numbers
        if start_line < 1 or end_line > total_lines or start_line > end_line:
            return f"Error: Invalid area {start_line}-{end_line}. File has {total_lines} lines."

        # Refactoring of new content to list with linebreaks
        new_lines = [line + "\n" for line in new_content.splitlines()]

        # Replace original lines with new lines and write to file
        lines[start_line - 1 : end_line] = new_lines

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return f"Sucess: Lines {start_line} to {end_line} were overwritten."

    except Exception as e:
        return f"Error while replacing lines: {e}"

def insert_at_line(filepath: str, target_line: int, content_to_insert: str) -> str:
    """
    Inserts new content at the specified line number (1-indexed).
    The existing line at target_line and all lines below it will be pushed down.
    It is advised to use smaller texts to stay inside the context window.
    """
    path = Path(filepath)
    if not path.exists():
        return f"Error: File '{filepath}' does not exist."

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)
        
        # If target line is greater than total lines, append at file end
        if target_line > total_lines + 1:
            target_line = total_lines + 1
        elif target_line < 1:
            target_line = 1

        insert_lines = [line + "\n" for line in content_to_insert.splitlines()]

        # Insert at specified position and write changes to file
        lines[target_line - 1 : target_line - 1] = insert_lines

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return f"Success: Content inserted before line {target_line}."

    except Exception as e:
        return f"Error while inserting: {e}"

def read_file_with_line_numbers(filepath: str, from_line: int=0, to_line: int=0) -> str:
    """
    Reads a file and returns its content with explicit line numbers (e.g. "1: import os").
    Optionally pass from_line and to_line, including the line from_line, excluding to_line. If no from / to is given, the whole document will be read.
    """
    path = Path(filepath)
    if not path.exists():
        return f"Fehler: Datei '{filepath}' existiert nicht."

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        numbered_lines = [f"{i + 1}: {line}" for i, line in enumerate(lines)]

        # Return only portion of document
        if from_line > 0 and to_line > 0 and from_line < len(numbered_lines) and to_line < len(numbered_lines):
            return "".join(numbered_lines[from_line-1:to_line-1])
        
        # Return whole document
        return "".join(numbered_lines)

    except Exception as e:
        return f"Fehler beim Lesen der Datei: {e}"

def replace_block(filepath: str, search_text: str, replace_text: str) -> str:
    """
    Replaces a unique block of text (search_text) with replace_text in the given file.
    It is advised to use smaller texts to stay inside the context window.
    """
    path = Path(filepath)
    if not path.exists():
        return f"Error: File '{filepath}' does not exist."

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if search_text not in content:
        return "Error: The given search_text was not found in the file. Check for correct spelling."

    if content.count(search_text) > 1:
        return "Error: The given search_text appears more than once. Please pass an unique block."

    new_content = content.replace(search_text, replace_text)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return "Success: Textblock replaced sucessfully."

def write_file(filepath: str, content: str) -> str:
    """
    Writes the given content into a file. If the file already exists, the content will be overwritten.
    Else a new file will be created.
    """
    path = Path(filepath)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"Error while writing file: {e}"
    return "Content written into file successfully."


# +----------------+
# |  OS NAVIGATION |
# +----------------+

def change_directory(dirpath: str) -> str:
    """
    Changes the working directory of the Python agent process.
    """
    try:
        os.chdir(dirpath)
        return f"Changed process working directory to: {os.getcwd()}"
    except FileNotFoundError:
        return f"Error: Directory '{dirpath}' does not exist."
    except PermissionError:
        return f"Error: Permission denied for directory '{dirpath}'."


# +-----------------+
# |  PLAN HANDLING  |
# +-----------------+

def create_execution_plan(plan_json: str) -> dict:
    """
    The function takes a json string that describes an execution plan used to break down complex tasks.
    The format for the json is {"summary": <plan_summary>, "steps": {<step_name>: <step_description"}}.
    For example: {"summary": "Update the Arch Linux System.", "steps": {"Terminal": "Open a new Terminal", "System Updaten": "Führe sudo pacman -Syu aus"}}
    """
    try:
        return json.loads(plan_json)
    except json.JSONDecodeError as e:
        return f"Fehler bei der JSON-Verarbeitung: {e}"

def mark_task_as_completed() -> True:
    """
    If you sucessfully achieved to goal of your task, call this tool to move on to the next one.
    It returns True so that the program can handle the logic for serving the next task.
    """
    return True

# Include all tools that may be used by LLMs here
available_functions = [
    open_browser,
    open_terminal,

    execute_terminal_command,

    get_current_date_and_time,

    replace_lines,
    insert_at_line,
    read_file_with_line_numbers,
    # replace_block,
    write_file,

    change_directory,

    create_execution_plan,
    mark_task_as_completed
]