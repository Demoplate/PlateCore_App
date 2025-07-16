import getpass
import os
import sys
import time
import json
from datetime import datetime
import pytz # For time zone handling

# ANSI color codes
COLORS = {
    "green": "\033[92m",
    "cyan": "\033[96m",
    "blue": "\033[94m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "white": "\033[97m",
    "gray": "\033[90m"
}
RESET = "\033[0m"

SESSION_FILE = "session.txt"
PROFILES_FILE = "profiles.json"
LOGS_FILE = "logs.json"
SESSION_HISTORY_FILE = "session_history.json"
PROJECTS_FILE = "projects.json"

# --- Global session variables (to store login info) ---
current_platecore_id = None # Will store the logged-in ID
current_session_start_time = None # To track session duration

# --- ASCII Art for "platecore" ---
# Generated using a tool for 'platecore'
PLATECORE_ASCII_ART = f"""{COLORS['cyan']}
██████╗ ██╗     █████╗ ████████╗██████╗  ██████╗██████╗  ██████╗ ███████╗
██╔══██╗██║    ██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██╔════╝ ██╔════╝
██████╔╝██║    ███████║   ██║   ██████╔╝██║     ██████╔╝██║  ███╗█████╗  
██╔══██╗██║    ██╔══██║   ██║   ██╔══██╗██║     ██╔══██╗██║   ██║██╔══╝  
██║  ██║███████╗██║  ██║   ██║   ██║  ██║╚██████╗██║  ██║╚██████╔╝███████╗
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
{RESET}"""


# --- Utility Functions ---

def pause_print(text, delay=0.05):
    """Prints text after a short delay, with a cyan '$' prefix."""
    time.sleep(delay)
    print(f"{COLORS['cyan']}${RESET} {text}")

def prompt_input(prompt_text=None):
    """Gets input with the colored prompt (gray, with cyan '@').
    Uses a static prompt based on current_platecore_id.
    """
    global current_platecore_id

    if prompt_text: # If a specific prompt text is passed (e.g., for password or simple yes/no)
        formatted_prompt = prompt_text.replace("@", f"{COLORS['cyan']}@{COLORS['gray']}")
        return input(f"{COLORS['gray']}{formatted_prompt}{RESET}")

    # Static prompt: [user]@platecore
    user_part = current_platecore_id if current_platecore_id else "guest"
    prompt_string = f"{user_part}@{COLORS['cyan']}platecore{COLORS['gray']} "
    
    return input(f"{COLORS['gray']}{prompt_string}{RESET}")

def prompt_getpass(prompt_text=None):
    """Gets password input with the colored prompt, hiding characters."""
    global current_platecore_id

    # For getpass, we'll use the static prompt if no specific text is provided
    if prompt_text is None:
        user_part = current_platecore_id if current_platecore_id else "guest"
        prompt_text = f"{user_part}@{COLORS['cyan']}platecore{COLORS['gray']} "
    else:
        # If a specific prompt text is passed, use it directly
        prompt_text = prompt_text.replace("@", f"{COLORS['cyan']}@{COLORS['gray']}")

    return getpass.getpass(f"{COLORS['gray']}{prompt_text}{RESET}")

def print_error(text):
    """Prints an error message in red without the '$' prefix."""
    print(f"{COLORS['red']}{text}{RESET}")

def is_logged_in():
    """Checks if a session file exists."""
    return os.path.exists(SESSION_FILE)

def mark_logged_in(user_id):
    """Creates a session file to mark as logged in, storing the user ID."""
    global current_platecore_id
    current_platecore_id = user_id
    with open(SESSION_FILE, "w") as f:
        f.write(user_id) # Store the actual ID

def get_logged_in_user():
    """Retrieves the logged-in user ID from the session file."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return f.read().strip()
    return None

def clear_session():
    """Removes the session file, logging out the user."""
    global current_platecore_id
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    current_platecore_id = None # Clear the global variable

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def load_json_file(filepath, default_data={}):
    """Loads data from a JSON file, handles errors and non-existent files."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print_error(f"Error reading {filepath}. File might be corrupted. Starting with default data.")
            return default_data
        except Exception as e:
            print_error(f"An unexpected error occurred while loading {filepath}: {type(e).__name__}: {e}")
            return default_data
    return default_data

def save_json_file(filepath, data):
    """Saves data to a JSON file."""
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print_error(f"Error: Could not write to {filepath}. Check permissions or disk space. {type(e).__name__}: {e}")
        raise # Re-raise to let the main loop's error handler catch it
    except TypeError as e:
        print_error(f"Error: Data format issue when saving to {filepath}. {type(e).__name__}: {e}")
        raise
    except Exception as e:
        print_error(f"An unexpected error occurred while saving {filepath}: {type(e).__name__}: {e}")
        raise # Re-raise to let the main loop's error handler catch it

# --- Data Loading (Specific for Logs, Profiles, Projects) ---
def load_profiles():
    """Loads profiles from profiles.json."""
    return load_json_file(PROFILES_FILE, {})

def save_profiles(profiles_data):
    """Saves profiles to profiles.json."""
    save_json_file(PROFILES_FILE, profiles_data)

def load_logs():
    """Loads logs from logs.json and ensures keys are integers."""
    loaded_data = load_json_file(LOGS_FILE, {})
    # Ensure keys are integers if they were loaded as strings (JSON default)
    return {int(k): v for k, v in loaded_data.items()}

def save_logs(logs_data):
    """Saves logs to logs.json (converts integer keys to strings for JSON)."""
    save_json_file(LOGS_FILE, {str(k): v for k, v in logs_data.items()})

def load_projects():
    """Loads projects from projects.json."""
    return load_json_file(PROJECTS_FILE, {})

def save_projects(projects_data):
    """Saves projects to projects.json."""
    save_json_file(PROJECTS_FILE, projects_data)

# --- Session History Functions ---
def load_session_history():
    """Loads session history from session_history.json."""
    return load_json_file(SESSION_HISTORY_FILE, [])

def save_session_history(history_data):
    """Saves session history to session_history.json."""
    save_json_file(SESSION_HISTORY_FILE, history_data)

def record_session_event(user_id, event_type, start_time, end_time=None):
    """Records an event in the session history."""
    history = load_session_history()
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')

    start_time_str = start_time.astimezone(malaysia_tz).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    end_time_str = end_time.astimezone(malaysia_tz).strftime('%Y-%m-%d %H:%M:%S %Z%z') if end_time else "N/A"

    new_entry = {
        "timestamp": datetime.now(malaysia_tz).strftime('%Y-%m-%d %H:%M:%S %Z%z'),
        "user_id": user_id,
        "event_type": event_type,
        "session_start": start_time_str,
        "session_end": end_time_str
    }
    history.append(new_entry)
    save_session_history(history)

def show_session_history():
    """Displays the session history."""
    history = load_session_history()
    if not history:
        pause_print(f"{COLORS['yellow']}No session history found.{RESET}")
        return

    pause_print(f"{COLORS['yellow']}Recent Session History (most recent first):{RESET}")
    for entry in reversed(history[-10:]): # Display last 10 entries for brevity, reverse for most recent first
        pause_print(f"{COLORS['gray']}--------------------{RESET}", delay=0.01)
        print(f"{COLORS['cyan']}  Time Recorded:{RESET} {entry['timestamp']}")
        print(f"{COLORS['cyan']}  User ID:{RESET} {entry['user_id']}")
        print(f"{COLORS['cyan']}  Event Type:{RESET} {entry['event_type']}")
        print(f"{COLORS['cyan']}  Session Start:{RESET} {entry['session_start']}")
        if entry['session_end'] != "N/A":
            print(f"{COLORS['cyan']}  Session End:{RESET} {entry['session_end']}")
    pause_print(f"{COLORS['gray']}--------------------{RESET}", delay=0.01)

# --- Project Management Functions ---

def projects_list_command(projects_data):
    """Lists all available projects."""
    if not projects_data:
        pause_print(f"{COLORS['yellow']}No projects found.{RESET}")
        return
    pause_print(f"{COLORS['yellow']}PlateCore Projects:{RESET}")
    for proj_id, proj_info in sorted(projects_data.items()):
        name = proj_info.get("Name", "N/A")
        status = proj_info.get("Status", "Unknown")
        due_date = proj_info.get("DueDate", "N/A")
        print(f"{COLORS['cyan']}  - {proj_id}:{RESET} {name} (Status: {status}, Due: {due_date})")

def project_view_command(projects_data, project_id):
    """Views details of a specific project."""
    if not project_id:
        print_error(f"Usage: projectview <PROJECT_ID>")
        return
    proj_id = project_id.upper()
    if proj_id in projects_data:
        proj = projects_data[proj_id]
        pause_print(f"\n{COLORS['yellow']}Project Details: {proj.get('Name', 'N/A')} ({proj_id}){RESET}")
        print(f"{COLORS['cyan']}  Description:{RESET} {proj.get('Description', 'N/A')}")
        print(f"{COLORS['cyan']}  Status:{RESET} {proj.get('Status', 'Unknown')}")
        print(f"{COLORS['cyan']}  Due Date:{RESET} {proj.get('DueDate', 'N/A')}")
        
        tasks = proj.get("Tasks", [])
        if tasks:
            print(f"\n  {COLORS['white']}--- Tasks ---{RESET}")
            for task in tasks:
                task_id = task.get('TaskID', 'N/A')
                desc = task.get('Description', 'N/A')
                assigned = task.get('AssignedTo', 'Unassigned')
                status = task.get('Status', 'Pending')
                print(f"{COLORS['gray']}    - {task_id}:{RESET} {desc} (Assigned: {assigned}, Status: {status})")
        else:
            pause_print(f"\n{COLORS['yellow']}No tasks for this project.{RESET}")
    else:
        print_error(f"Project '{proj_id}' not found.")

def project_add_command(projects_data):
    """Adds a new project."""
    pause_print(f"{COLORS['yellow']}--- Add New Project ---{RESET}")
    new_proj_id = prompt_input("Enter new Project ID (e.g., PROJ-001): ").strip().upper()
    if not new_proj_id:
        print_error(f"Project ID cannot be empty.")
        return None
    if new_proj_id in projects_data:
        print_error(f"Project ID '{new_proj_id}' already exists. Use 'projectedit' to modify.")
        return None

    name = prompt_input("Enter Project Name: ").strip()
    desc = prompt_input("Enter Description: ").strip()
    status = prompt_input("Enter Status (e.g., Active, On Hold, Completed): ").strip() or "Active"
    due_date = prompt_input("Enter Due Date (YYYY-MM-DD, or N/A): ").strip() or "N/A"

    projects_data[new_proj_id] = {
        "Name": name,
        "Description": desc,
        "Status": status,
        "DueDate": due_date,
        "Tasks": [] # Initialize with an empty list of tasks
    }
    save_projects(projects_data)
    pause_print(f"{COLORS['yellow']}Project '{new_proj_id}' added successfully!{RESET}")
    return new_proj_id # Return the new ID so main can set context

def project_edit_command(projects_data, project_id):
    """Edits an existing project."""
    if not project_id:
        print_error(f"Usage: projectedit <PROJECT_ID>")
        return False
    proj_id = project_id.upper()
    if proj_id in projects_data:
        proj = projects_data[proj_id]
        pause_print(f"{COLORS['yellow']}--- Editing Project '{proj_id}' ---{RESET}")
        
        new_name = prompt_input(f"Enter new Name (current: '{proj.get('Name', 'N/A')}', leave blank to keep): ").strip()
        if new_name: proj['Name'] = new_name

        new_desc = prompt_input(f"Enter new Description (current: '{proj.get('Description', 'N/A')}', leave blank to keep): ").strip()
        if new_desc: proj['Description'] = new_desc

        new_status = prompt_input(f"Enter new Status (current: '{proj.get('Status', 'Unknown')}', leave blank to keep): ").strip()
        if new_status: proj['Status'] = new_status

        new_due_date = prompt_input(f"Enter new Due Date (current: '{proj.get('DueDate', 'N/A')}', leave blank to keep): ").strip()
        if new_due_date: proj['DueDate'] = new_due_date

        save_projects(projects_data)
        pause_print(f"{COLORS['yellow']}Project '{proj_id}' updated successfully!{RESET}")
        return True # Indicate success
    else:
        print_error(f"Project '{proj_id}' not found.")
        return False

def project_delete_command(projects_data, project_id):
    """Deletes a project."""
    if not project_id:
        print_error(f"Usage: projectdelete <PROJECT_ID>")
        return False
    proj_id = project_id.upper()
    if proj_id in projects_data:
        confirm = prompt_input(f"{COLORS['yellow']}Are you sure you want to delete project '{proj_id}'? (y/n): {RESET}").lower()
        if confirm == 'y':
            del projects_data[proj_id]
            save_projects(projects_data)
            pause_print(f"{COLORS['yellow']}Project '{proj_id}' deleted.{RESET}")
            return True # Indicate success
        else:
            pause_print(f"{COLORS['yellow']}Deletion cancelled.{RESET}")
            return False
    else:
        print_error(f"Project '{proj_id}' not found.")
        return False

def task_add_command(projects_data, project_id):
    """Adds a task to a project."""
    if not project_id:
        print_error(f"Usage: taskadd <PROJECT_ID>")
        return False
    proj_id = project_id.upper()
    if proj_id not in projects_data:
        print_error(f"Project '{proj_id}' not found.")
        return False

    pause_print(f"{COLORS['yellow']}--- Add New Task to Project '{proj_id}' ---{RESET}")
    task_desc = prompt_input("Enter Task Description: ").strip()
    if not task_desc:
        print_error(f"Task description cannot be empty.")
        return False

    tasks = projects_data[proj_id].get("Tasks", [])
    next_task_id = 1
    if tasks:
        # Find highest existing numeric task ID and add 1
        max_id = 0
        for task in tasks:
            tid_str = task.get('TaskID', 'T-0').replace('T-', '')
            if tid_str.isdigit():
                max_id = max(max_id, int(tid_str))
        next_task_id = max_id + 1
    
    new_task_id = f"T-{next_task_id}"

    assigned_to = prompt_input("Assign to Profile ID (leave blank for Unassigned): ").strip().upper()
    if assigned_to and assigned_to not in load_profiles(): # Check if profile exists
        pause_print(f"{COLORS['yellow']}Warning: Profile '{assigned_to}' not found. Task will remain unassigned.{RESET}")
        assigned_to = "Unassigned"
    elif not assigned_to:
        assigned_to = "Unassigned"

    new_task = {
        "TaskID": new_task_id,
        "Description": task_desc,
        "AssignedTo": assigned_to,
        "Status": "Pending"
    }
    projects_data[proj_id]["Tasks"].append(new_task)
    save_projects(projects_data)
    pause_print(f"{COLORS['yellow']}Task '{new_task_id}' added to Project '{proj_id}' successfully!{RESET}")
    return True # Indicate success

def task_update_command(projects_data, args_str, profiles_data):
    """Updates a task's status or assignment."""
    args = args_str.split(" ", 3)
    if len(args) < 3:
        print_error(f"Usage: taskupdate <PROJECT_ID> <TASK_ID> <status|assigned> <VALUE>")
        return False
    
    proj_id_raw, task_id_raw, update_type = args[0], args[1], args[2].lower()
    value = args[3] if len(args) > 3 else ""

    proj_id = proj_id_raw.upper()
    task_id = task_id_raw.upper()

    if proj_id not in projects_data:
        print_error(f"Project '{proj_id}' not found.")
        return False
    
    project_tasks = projects_data[proj_id].get("Tasks", [])
    task_found = False
    
    for task in project_tasks:
        if task.get("TaskID") == task_id:
            task_found = True
            if update_type == "status":
                if value.lower() in ["pending", "in progress", "complete"]:
                    task["Status"] = value.title()
                    pause_print(f"{COLORS['yellow']}Task '{task_id}' status updated to '{task['Status']}' in Project '{proj_id}'.{RESET}")
                else:
                    print_error(f"Invalid status. Use 'pending', 'in progress', or 'complete'.")
                    return False
            elif update_type == "assigned":
                if value and value.upper() not in profiles_data:
                    pause_print(f"{COLORS['yellow']}Warning: Profile '{value}' not found. Task will remain unassigned.{RESET}")
                    task["AssignedTo"] = "Unassigned"
                elif not value:
                    task["AssignedTo"] = "Unassigned"
                    pause_print(f"{COLORS['yellow']}Task '{task_id}' unassigned in Project '{proj_id}'.{RESET}")
                else:
                    task["AssignedTo"] = value.upper()
                    pause_print(f"{COLORS['yellow']}Task '{task_id}' assigned to '{task['AssignedTo']}' in Project '{proj_id}'.{RESET}")
            else:
                print_error(f"Invalid update type. Use 'status' or 'assigned'.")
                return False
            
            save_projects(projects_data)
            return True # Indicate success

    if not task_found:
        print_error(f"Task '{task_id}' not found in Project '{proj_id}'.")
    return False

def task_delete_command(projects_data, args_str):
    """Deletes a task from a project."""
    args = args_str.split(" ", 1)
    if len(args) < 2:
        print_error(f"Usage: taskdelete <PROJECT_ID> <TASK_ID>")
        return False
    
    proj_id_raw, task_id_raw = args[0], args[1]
    proj_id = proj_id_raw.upper()
    task_id = task_id_raw.upper()

    if proj_id not in projects_data:
        print_error(f"Project '{proj_id}' not found.")
        return False
    
    tasks = projects_data[proj_id].get("Tasks", [])
    initial_task_count = len(tasks)
    
    projects_data[proj_id]["Tasks"] = [t for t in tasks if t.get("TaskID") != task_id]

    if len(projects_data[proj_id]["Tasks"]) < initial_task_count:
        save_projects(projects_data)
        pause_print(f"{COLORS['yellow']}Task '{task_id}' deleted from Project '{proj_id}'.{RESET}")
        return True # Indicate success
    else:
        print_error(f"Task '{task_id}' not found in Project '{proj_id}'.")
        return False

# --- Export/Import Data Functions ---

def export_all_data(profiles, logs, projects, session_history):
    """Exports all data (profiles, logs, projects, session history) to a single JSON file."""
    export_filename = prompt_input(f"{COLORS['yellow']}Enter filename for data export (e.g., all_platecore_data.json): {RESET}").strip()
    if not export_filename:
        print_error(f"Export cancelled: No filename provided.")
        return

    # Convert integer keys in logs to strings for JSON serialization
    logs_serializable = {str(k): v for k, v in logs.items()}

    all_data = {
        "profiles": profiles,
        "logs": logs_serializable,
        "projects": projects,
        "session_history": session_history
    }

    try:
        with open(export_filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4)
        pause_print(f"{COLORS['yellow']}All data exported to '{export_filename}' successfully!{RESET}")
    except IOError as e:
        print_error(f"Error exporting data: {type(e).__name__}: {e}")
    except Exception as e:
        print_error(f"An unexpected error occurred during export: {type(e).__name__}: {e}")

def import_all_data(profiles, logs, projects, session_history):
    """Imports data from a JSON file, skipping entries that already exist."""
    import_filename = prompt_input(f"{COLORS['yellow']}Enter filename for data import (e.g., all_platecore_data.json): {RESET}").strip()
    if not import_filename:
        print_error(f"Import cancelled: No filename provided.")
        return

    if not os.path.exists(import_filename):
        print_error(f"File '{import_filename}' not found.")
        return
    
    try:
        with open(import_filename, "r", encoding="utf-8") as f:
            imported_data = json.load(f)

        imported_counts = {"profiles": 0, "logs": 0, "projects": 0, "session_history": 0}
        skipped_counts = {"profiles": 0, "logs": 0, "projects": 0}
        tasks_updated_in_existing_projects = 0
        tasks_added_to_existing_projects = 0

        # Import Profiles
        imported_profiles = imported_data.get("profiles", {})
        for profile_id, profile_info in imported_profiles.items():
            if profile_id in profiles:
                pause_print(f"{COLORS['yellow']}Profile '{profile_id}' already exists. Skipping import.{RESET}")
                skipped_counts["profiles"] += 1
            else:
                profiles[profile_id] = profile_info
                imported_counts["profiles"] += 1
        save_profiles(profiles)
        pause_print(f"{COLORS['yellow']}{imported_counts['profiles']} profile(s) imported, {skipped_counts['profiles']} skipped.{RESET}")

        # Import Logs
        imported_logs = imported_data.get("logs", {})
        # Ensure imported keys are integers for comparison with 'stories' dict
        imported_logs_int_keys = {int(k): v for k, v in imported_logs.items()}
        for log_id, log_entry in imported_logs_int_keys.items():
            if log_id in logs:
                pause_print(f"{COLORS['yellow']}Log '{log_id}' already exists. Skipping import.{RESET}")
                skipped_counts["logs"] += 1
            else:
                logs[log_id] = log_entry
                imported_counts["logs"] += 1
        save_logs(logs)
        pause_print(f"{COLORS['yellow']}{imported_counts['logs']} log(s) imported, {skipped_counts['logs']} skipped.{RESET}")


        # Import Projects
        imported_projects = imported_data.get("projects", {})
        for project_id, project_info in imported_projects.items():
            if project_id in projects:
                pause_print(f"{COLORS['yellow']}Project '{project_id}' already exists. Skipping project import (but checking tasks).{RESET}")
                skipped_counts["projects"] += 1
                # If the project itself exists, still process its tasks for updates/additions
                current_tasks_map = {t.get("TaskID"): t for t in projects[project_id].get("Tasks", [])}
                imported_tasks = project_info.get("Tasks", [])
                
                for imported_task in imported_tasks:
                    imported_task_id = imported_task.get("TaskID")
                    if imported_task_id and imported_task_id in current_tasks_map:
                        pause_print(f"{COLORS['gray']}  Task '{imported_task_id}' in project '{project_id}' exists. Updating fields.{RESET}")
                        current_tasks_map[imported_task_id].update(imported_task)
                        tasks_updated_in_existing_projects += 1
                    else:
                        pause_print(f"{COLORS['gray']}  Adding new task '{imported_task_id}' to existing project '{project_id}'.{RESET}")
                        current_tasks_map[imported_task_id] = imported_task
                        tasks_added_to_existing_projects += 1
                projects[project_id]["Tasks"] = list(current_tasks_map.values())
            else:
                projects[project_id] = project_info
                imported_counts["projects"] += 1
        save_projects(projects)
        pause_print(f"{COLORS['yellow']}{imported_counts['projects']} project(s) imported (new), {skipped_counts['projects']} skipped (project already existed).{RESET}")
        if tasks_added_to_existing_projects > 0 or tasks_updated_in_existing_projects > 0:
             pause_print(f"{COLORS['yellow']}  Within existing projects: {tasks_added_to_existing_projects} tasks added, {tasks_updated_in_existing_projects} tasks updated.{RESET}")

        # Import Session History (always append, but check for exact duplicates)
        imported_session_history = imported_data.get("session_history", [])
        current_session_history = load_session_history()
        for entry in imported_session_history:
            if entry not in current_session_history: # Simple check for exact duplicate entry
                current_session_history.append(entry)
                imported_counts["session_history"] += 1

        save_session_history(current_session_history)
        pause_print(f"{COLORS['yellow']}{imported_counts['session_history']} session history entry(ies) imported.{RESET}")

        pause_print(f"{COLORS['green']}Data import process finished!{RESET}")

    except json.JSONDecodeError:
        print_error(f"Error reading {import_filename}. File might be corrupted or not a valid JSON.")
    except Exception as e:
        print_error(f"An unexpected error occurred during import: {type(e).__name__}: {e}")


# --- Help Function (Categorized) ---
def show_help(category=None):
    help_categories = {
        "journal": {
            "title": "Journal/Logbook Commands",
            "commands": [
                ("loglist", "Show available logbook IDs and dates"),
                ("logbook <ID>", "View a specific journal entry"),
                ("newlog", "Create a new log entry"),
                ("editlog <ID>", "Modify an existing log entry"),
                ("deletelog <ID>", "Delete a log entry (requires ID confirmation)"),
                ("exportlogs", "Export all log entries to a text file")
            ]
        },
        "profiles": {
            "title": "Profile Management Commands",
            "commands": [
                ("profileslist", "List all available profile IDs"),
                ("profilesview <ID>", "View a specific person's profile"),
                ("profilesadd", "Add a new profile"),
                ("profilesedit <ID>", "Edit an existing profile"),
                ("profilesdelete <ID>", "Delete a profile"),
                ("searchprofile <KEYWORD>", "Search profiles by name, role, IC, PN, or CB") # Updated search fields
            ]
        },
        "projects": {
            "title": "Project Management Commands",
            "commands": [
                ("projectslist", "List all active projects"),
                ("projectview <ID>", "View details of a specific project and its tasks"),
                ("projectadd", "Create a new project"),
                ("projectedit <ID>", "Modify an existing project's details"),
                ("projectdelete <ID>", "Delete a project"),
                ("taskadd <PROJECT_ID>", "Add a new task to a project"),
                ("taskupdate <PROJ_ID> <TASK_ID> <status|assigned> <VALUE>", "Update task status or assignment"),
                ("taskdelete <PROJ_ID> <TASK_ID>", "Delete a task from a project")
            ]
        },
        "system": {
            "title": "System/Utility Commands",
            "commands": [
                ("login", "Log in to PlateCore"),
                ("logout", "Log out from PlateCore"),
                ("clear", "Clear the terminal screen"),
                ("whoami", "Display current user and session info"),
                ("history", "View session login/logout history"),
                ("exportdata", "Export all system data (profiles, logs, projects, history) to JSON"),
                ("importdata", "Import data from a JSON file, skipping existing entries"),
                ("help [CATEGORY]", "Show this help message or commands in a category"),
                ("exit", "Exit the session"),
                ("hyprctl dispatch exit", "Restart the program")
            ]
        },
        "customization": {
            "title": "Customization Commands",
            "commands": [
                ("Refer to https://youtube.com/@demoplate?si=r6UJTJl7hgdl_bot", "Placeholder for customization options")
            ]
        }
    }

    if category:
        # User requested a specific category
        normalized_category = category.lower()
        if normalized_category in help_categories:
            cat_info = help_categories[normalized_category]
            pause_print(f"\n{COLORS['white']}--- {cat_info['title']} ---{RESET}")
            for cmd, desc in cat_info['commands']:
                # Pad command to a fixed width for alignment
                print(f"  {COLORS['blue']}{cmd:<40}{RESET} - {desc}")
        else:
            print_error(f"Unknown help category: '{category}'.")
            pause_print(f"{COLORS['yellow']}Available categories: {', '.join(help_categories.keys())}{RESET}")
    else:
        # User requested general help, list categories
        pause_print(f"{COLORS['yellow']}Available command categories (type 'help <CATEGORY>' for details):{RESET}")
        for key, info in help_categories.items():
            print(f"{COLORS['cyan']}- {key.capitalize()}: {info['title']}{RESET}")
        pause_print(f"\n{COLORS['yellow']}For specific command details, type 'help <category_name>' (e.g., 'help journal').{RESET}")


# --- Who Am I Command Function ---
def who_am_i_command():
    global current_platecore_id
    if not current_platecore_id:
        current_platecore_id = get_logged_in_user()

    pause_print(f"{COLORS['yellow']}Current Session Information:{RESET}")
    print(f"{COLORS['cyan']}  PlateCore ID:{RESET} {current_platecore_id if current_platecore_id else 'Not Logged In'}")
    
    print(f"{COLORS['cyan']}  Prompt Color:{RESET} Gray for input, Cyan for output")

    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_time_malaysia = datetime.now(malaysia_tz)
    
    print(f"{COLORS['cyan']}  Current Time:{RESET} {current_time_malaysia.strftime('%A, %B %d, %Y %I:%M:%S %p %Z%z')}")
    print(f"{COLORS['cyan']}  Location:{RESET} Bentong, Pahang, Malaysia")


# --- Main Application Logic ---

def main():
    global current_platecore_id, current_session_start_time

    # Clear screen and display ASCII art at startup
    clear_screen()
    print(PLATECORE_ASCII_ART)
    time.sleep(1) # A small pause to let the user see the art
    pause_print(f"{COLORS['yellow']}Type 'login' to log in or 'help' for available commands.{RESET}")

    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_session_start_time = datetime.now(malaysia_tz)

    # Attempt to load an existing session from file
    current_platecore_id = get_logged_in_user()
    if current_platecore_id:
        pause_print(f"{COLORS['yellow']}Session found. Logged in as {current_platecore_id}.{RESET}")
        record_session_event(current_platecore_id, "Session Resumed", current_session_start_time)


    stories = load_logs()
    profiles = load_profiles()
    projects = load_projects()

    if not stories:
        stories = {
            1: ["March 12, 2025 — Mia smiled at me during the group work.",
                "She looked shy but happy."],
            2: ["March 20, 2025 — Helped someone with their book.",
                "They said thank thank you with a smile."],
            3: ["April 5, 2025 — The class clapped when I sat down.",
                "Felt like a main character moment."]
        }
        save_logs(stories)

    log_dates = {}
    for lid, entry in stories.items():
        if entry and isinstance(entry, list) and len(entry) > 0 and "—" in entry[0]:
            log_dates[lid] = entry[0].split("—")[0].strip()
        elif entry and isinstance(entry, list) and len(entry) > 0:
            log_dates[lid] = entry[0].strip()
        else:
            log_dates[lid] = "No Date (Malformed Entry)"


    if not profiles:
        profiles["Z-1"] = {
            "Name": "Zaheerul Islam",
            "ID": "Z-1",
            "Role": "Creator of this log system",
            "IC": "N/A", # Added IC
            "PN": "N/A", # Added PN
            "CB": 12345 # Added CB with a number
        }
        save_profiles(profiles)
    
    if not projects:
        projects["PROJ-001"] = {
            "Name": "Phase 1: Terminal UI Overhaul",
            "Description": "Improve the user interface and add core corporate functionalities.",
            "Status": "Active",
            "DueDate": "2025-08-15",
            "Tasks": [
                {"TaskID": "T-1", "Description": "Implement Project Management Module", "AssignedTo": "Z-1", "Status": "In Progress"},
                {"TaskID": "T-2", "Description": "Design new splash screen", "AssignedTo": "Unassigned", "Status": "Pending"},
                {"TaskID": "T-3", "Description": "Integrate user roles and permissions", "AssignedTo": "Z-1", "Status": "Pending"}
            ]
        }
        save_projects(projects)

    try:
        while True:
            command_raw = prompt_input().strip() # Static prompt call
            command_parts = command_raw.lower().split(" ", 1)
            base_command = command_parts[0]
            arg = command_parts[1] if len(command_parts) > 1 else ""

            # Commands allowed when not logged in
            allowed_guest_commands = ["login", "help", "clear", "exit", "hyprctl dispatch exit", "importdata"] # Added importdata for guest use

            if not current_platecore_id and base_command not in allowed_guest_commands:
                print_error(f"Command '{base_command}' needs privileges. Please 'login' first.")
                continue # Skip to next prompt

            # --- System/Utility Commands (Login/Logout first for precedence) ---
            if base_command == "login":
                if current_platecore_id:
                    pause_print(f"{COLORS['yellow']}You are already logged in as {current_platecore_id}. Type 'logout' to switch users.{RESET}")
                else:
                    pause_print(f"{COLORS['yellow']}Insert PlateCore Interactive ID:{RESET}")
                    platecore_id_input = prompt_input()
                    pause_print(f"{COLORS['yellow']}Password:{RESET}")
                    password_input = prompt_getpass()

                    if platecore_id_input == "demoplate" and password_input == "245225":
                        pause_print(f"{COLORS['yellow']}Access Granted{RESET}")
                        mark_logged_in(platecore_id_input)
                        current_session_start_time = datetime.now(malaysia_tz) # Reset session start time for new login
                        record_session_event(platecore_id_input, "Login Success", current_session_start_time)
                    else:
                        print_error(f"Access Denied.")
                        record_session_event(platecore_id_input if platecore_id_input else "UNKNOWN", "Login Denied", datetime.now(malaysia_tz), datetime.now(malaysia_tz))
            
            elif base_command == "logout":
                if current_platecore_id:
                    pause_print(f"{COLORS['yellow']}Logging out from {current_platecore_id}...{RESET}")
                    record_session_event(current_platecore_id, "Logout", current_session_start_time, datetime.now(malaysia_tz))
                    clear_session()
                    pause_print(f"{COLORS['yellow']}Logged out successfully. Type 'login' to log back in.{RESET}")
                else:
                    pause_print(f"{COLORS['yellow']}You are not currently logged in.{RESET}")

            # --- Journal/Logbook Commands ---
            elif base_command == "logbook":
                if not arg:
                    print_error(f"Usage: logbook <ID>")
                    continue
                try:
                    logbook_id = int(arg)
                    if logbook_id in stories:
                        pause_print(f"\n{COLORS['yellow']}Logbook Entry {logbook_id}{RESET}")
                        for line in stories[logbook_id]:
                            print(f"{COLORS['cyan']}>> {line}{RESET}")
                    else:
                        print_error(f"No logbook found with that ID.")
                except ValueError:
                    print_error(f"Invalid logbook ID. Please enter a number.")

            elif base_command == "loglist":
                pause_print(f"{COLORS['yellow']}Available Logbook Entries:{RESET}")
                if log_dates:
                    for lid in sorted(log_dates.keys()):
                        print(f"{COLORS['cyan']}{lid} : {log_dates[lid]}{RESET}")
                else:
                    pause_print(f"{COLORS['yellow']}No log entries found.{RESET}")

            elif base_command == "newlog":
                pause_print(f"{COLORS['yellow']}--- New Log Entry ---{RESET}")
                entry_lines = []
                pause_print(f"{COLORS['yellow']}Enter your log entry (type 'END' on a new line to finish):{RESET}")
                while True:
                    line = prompt_input(">> ").strip()
                    if line.upper() == "END":
                        break
                    entry_lines.append(line)

                if not entry_lines:
                    print_error(f"Log entry cancelled (no content).")
                    continue

                next_id = max(stories.keys()) + 1 if stories else 1
                
                current_date_str = datetime.now(malaysia_tz).strftime("%B %d, %Y")

                if "—" not in entry_lines[0]:
                    entry_lines[0] = f"{current_date_str} — {entry_lines[0]}"

                stories[next_id] = entry_lines
                log_dates[next_id] = current_date_str
                pause_print(f"{COLORS['yellow']}Log Entry {next_id} saved successfully!{RESET}")
                save_logs(stories)

            elif base_command == "editlog":
                if not arg:
                    print_error(f"Usage: editlog <ID>")
                    continue
                try:
                    log_id_to_edit = int(arg)
                except ValueError:
                    print_error(f"Invalid log ID. Please enter a number.")
                    continue

                if log_id_to_edit in stories:
                    pause_print(f"{COLORS['yellow']}--- Editing Log Entry {log_id_to_edit} ---{RESET}")
                    pause_print(f"{COLORS['yellow']}Current Content:{RESET}")
                    for line in stories[log_id_to_edit]:
                        print(f"{COLORS['cyan']}>> {line}{RESET}")
                    
                    pause_print(f"\n{COLORS['yellow']}Enter new content (type 'END' on a new line to finish):{RESET}")
                    new_entry_lines = []
                    while True:
                        line = prompt_input(">> ").strip()
                        if line.upper() == "END":
                            break
                        new_entry_lines.append(line)

                    if not new_entry_lines:
                        print_error(f"No new content entered. Log entry not updated.")
                        continue
                    
                    # Ensure the first line has a date prefix if it doesn't already
                    if stories[log_id_to_edit] and isinstance(stories[log_id_to_edit], list) and len(stories[log_id_to_edit]) > 0:
                        original_first_line = stories[log_id_to_edit][0]
                        if '—' in original_first_line:
                            date_part = original_first_line.split('—', 1)[0].strip()
                            # Check if the new first line already contains a date-like prefix, avoid double-prepending
                            if not any(keyword in new_entry_lines[0] for keyword in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "—"]):
                                new_entry_lines[0] = f"{date_part} — {new_entry_lines[0]}"
                        else:
                            current_date_str = datetime.now(malaysia_tz).strftime("%B %d, %Y")
                            new_entry_lines[0] = f"{current_date_str} — {new_entry_lines[0]}"
                    else: # Fallback if original entry was empty/malformed, just prepend current date
                        current_date_str = datetime.now(malaysia_tz).strftime("%B %d, %Y")
                        new_entry_lines[0] = f"{current_date_str} — {new_entry_lines[0]}"

                    stories[log_id_to_edit] = new_entry_lines
                    
                    # Update log_dates entry based on the new first line
                    if '—' in new_entry_lines[0]:
                        log_dates[log_id_to_edit] = new_entry_lines[0].split('—')[0].strip()
                    else:
                        log_dates[log_id_to_edit] = "No Date (Malformed after edit)"

                    save_logs(stories)
                    pause_print(f"{COLORS['yellow']}Log Entry {log_id_to_edit} updated successfully!{RESET}")
                else:
                    print_error(f"No logbook found with that ID to edit.")

            elif base_command == "deletelog":
                if not arg:
                    print_error(f"Usage: deletelog <ID>")
                    continue
                try:
                    log_id_to_delete = int(arg)
                except ValueError:
                    print_error(f"Invalid log ID. Please enter a number.")
                    continue

                if log_id_to_delete in stories:
                    confirm_id = prompt_input(f"{COLORS['yellow']}To confirm deletion of Log Entry {log_id_to_delete}, type its ID again: {RESET}").strip()
                    if confirm_id == str(log_id_to_delete):
                        del stories[log_id_to_delete]
                        if log_id_to_delete in log_dates:
                            del log_dates[log_id_to_delete]
                        pause_print(f"{COLORS['yellow']}Log Entry {log_id_to_delete} deleted.{RESET}")
                        save_logs(stories)
                    else:
                        pause_print(f"{COLORS['yellow']}Deletion cancelled (IDs did not match).{RESET}")
                else:
                    print_error(f"No logbook found with that ID to delete.")
            
            elif base_command == "exportlogs":
                if not stories:
                    pause_print(f"{COLORS['yellow']}No log entries to export.{RESET}")
                    continue

                export_filename = prompt_input(f"{COLORS['yellow']}Enter filename for export (e.g., my_logs.txt): {RESET}").strip()
                if not export_filename:
                    print_error(f"Export cancelled: No filename provided.")
                    continue
                
                try:
                    with open(export_filename, "w", encoding="utf-8") as f:
                        for lid in sorted(stories.keys()):
                            f.write(f"--- Log Entry {lid} ---\n")
                            for line in stories[lid]:
                                f.write(f"{line}\n")
                            f.write("\n")
                    pause_print(f"{COLORS['yellow']}All log entries exported to '{export_filename}' successfully!{RESET}")
                except IOError as e:
                    print_error(f"Error exporting logs: {type(e).__name__}: {e}")


            # --- Profile Management Commands ---
            elif base_command == "profileslist":
                if profiles:
                    pause_print(f"{COLORS['yellow']}Available Profile IDs:{RESET}")
                    for pid in sorted(profiles.keys()):
                        print(f"{COLORS['cyan']}- {pid} ({profiles[pid].get('Name', 'N/A')}){RESET}")
                else:
                    pause_print(f"{COLORS['yellow']}No profiles found.{RESET}")

            elif base_command == "profilesview":
                profile_id = arg.strip().upper()
                if profile_id:
                    if profile_id in profiles:
                        pause_print(f"\n{COLORS['yellow']}Profile {profile_id}{RESET}")
                        # Displaying fields in a specific order for better readability
                        print(f"{COLORS['cyan']}>> Name: {profiles[profile_id].get('Name', 'N/A')}{RESET}")
                        print(f"{COLORS['cyan']}>> ID: {profiles[profile_id].get('ID', 'N/A')}{RESET}")
                        print(f"{COLORS['cyan']}>> Role: {profiles[profile_id].get('Role', 'N/A')}{RESET}")
                        print(f"{COLORS['cyan']}>> IC: {profiles[profile_id].get('IC', 'N/A')}{RESET}")
                        print(f"{COLORS['cyan']}>> PN: {profiles[profile_id].get('PN', 'N/A')}{RESET}")
                        print(f"{COLORS['cyan']}>> CB: {profiles[profile_id].get('CB', 'N/A')}{RESET}")
                    else:
                        print_error(f"Profile '{profile_id}' not found.")
                else:
                    print_error(f"Usage: profilesview <ID>")

            elif base_command == "profilesadd":
                pause_print(f"{COLORS['yellow']}--- Add New Profile ---{RESET}")
                new_id = prompt_input("Enter new Profile ID (e.g., P-002): ").strip().upper()
                if not new_id:
                    print_error(f"Profile ID cannot be empty.")
                    continue
                if new_id in profiles:
                    print_error(f"Profile ID '{new_id}' already exists. Use 'profilesedit <ID>' to modify.")
                    continue

                new_name = prompt_input("Enter Name: ").strip()
                new_role = prompt_input("Enter Role: ").strip()

                new_ic = prompt_input("Enter Identity Card (IC) No.: ").strip()
                new_pn = prompt_input("Enter Phone Number (PN): ").strip()
                
                new_cb_input = prompt_input("Enter Certification Body (CB) Number: ").strip()
                new_cb = "N/A"
                if new_cb_input:
                    try:
                        new_cb = int(new_cb_input)
                    except ValueError:
                        print_error(f"Invalid input for CB. Please enter a number. Storing as 'N/A'.")


                profiles[new_id] = {
                    "Name": new_name if new_name else "N/A",
                    "ID": new_id,
                    "Role": new_role if new_role else "N/A",
                    "IC": new_ic if new_ic else "N/A",
                    "PN": new_pn if new_pn else "N/A",
                    "CB": new_cb
                }
                pause_print(f"{COLORS['yellow']}Profile '{new_id}' added successfully!{RESET}")
                save_profiles(profiles)

            elif base_command == "profilesedit":
                profile_id_to_edit = arg.strip().upper()
                if profile_id_to_edit:
                    if profile_id_to_edit in profiles:
                        pause_print(f"{COLORS['yellow']}--- Editing Profile '{profile_id_to_edit}' ---{RESET}")
                        current_profile = profiles[profile_id_to_edit]

                        for key in ["Name", "Role"]:
                            current_value = current_profile.get(key, "N/A")
                            new_value = prompt_input(f"Enter new {key} (current: '{current_value}', leave blank to keep): ").strip()
                            if new_value:
                                current_profile[key] = new_value
                        
                        # Handle IC and PN - now correctly keeps old value if blank
                        for key in ["IC", "PN"]:
                            current_value = current_profile.get(key, "N/A")
                            new_value = prompt_input(f"Enter new {key} (current: '{current_value}', leave blank to keep): ").strip()
                            if new_value: # Only update if new_value is NOT blank
                                current_profile[key] = new_value
                        
                        # Special handling for CB to ensure it's a number - now correctly keeps old value if blank
                        current_cb = current_profile.get("CB", "N/A")
                        new_cb_input = prompt_input(f"Enter new CB Number (current: '{current_cb}', leave blank to keep): ").strip()
                        if new_cb_input: # Only update if new_cb_input is NOT blank
                            try:
                                current_profile["CB"] = int(new_cb_input)
                            except ValueError:
                                print_error(f"Invalid input for CB. Please enter a number. CB not updated.")


                        pause_print(f"{COLORS['yellow']}Profile '{profile_id_to_edit}' updated successfully!{RESET}")
                        save_profiles(profiles)
                    else:
                        print_error(f"Profile '{profile_id_to_edit}' not found.")
                else:
                    print_error(f"Usage: profilesedit <ID>")

            elif base_command == "profilesdelete":
                profile_id_to_delete = arg.strip().upper()
                if profile_id_to_delete:
                    if profile_id_to_delete in profiles:
                        confirm = prompt_input(f"{COLORS['yellow']}Are you sure you want to delete profile '{profile_id_to_delete}'? (y/n): {RESET}").lower()
                        if confirm == 'y':
                            del profiles[profile_id_to_delete]
                            pause_print(f"{COLORS['yellow']}Profile '{profile_id_to_delete}' deleted.{RESET}")
                            save_profiles(profiles)
                        else:
                            pause_print(f"{COLORS['yellow']}Deletion cancelled.{RESET}")
                    else:
                        print_error(f"Profile '{profile_id_to_delete}' not found.")
                else:
                    print_error(f"Usage: profilesdelete <ID>")
            
            elif base_command == "searchprofile":
                search_keyword = arg.strip().lower()
                if not search_keyword:
                    print_error(f"Usage: searchprofile <KEYWORD>")
                    continue

                found_profiles = {}
                for pid, profile_data in profiles.items():
                    # Adjusted search fields: Name, Role, IC, PN, CB
                    # Convert CB to string for searching if it's an int
                    cb_value_str = str(profile_data.get("CB", "")).lower() 

                    if (search_keyword in profile_data.get("Name", "").lower() or
                        search_keyword in profile_data.get("Role", "").lower() or
                        search_keyword in profile_data.get("IC", "").lower() or
                        search_keyword in profile_data.get("PN", "").lower() or
                        search_keyword in cb_value_str): # Search CB as string
                        found_profiles[pid] = profile_data.get("Name", "N/A")

                if found_profiles:
                    pause_print(f"{COLORS['yellow']}Profiles matching '{search_keyword}':{RESET}")
                    for pid, name in sorted(found_profiles.items()):
                        print(f"{COLORS['cyan']}- {pid} ({name}){RESET}")
                else:
                    pause_print(f"{COLORS['yellow']}No profiles found matching '{search_keyword}'.{RESET}")


            # --- Project Management Commands ---
            elif base_command == "projectslist":
                projects_list_command(projects)

            elif base_command == "projectview":
                project_view_command(projects, arg)

            elif base_command == "projectadd":
                new_proj_id = project_add_command(projects)

            elif base_command == "projectedit":
                success = project_edit_command(projects, arg)

            elif base_command == "projectdelete":
                deleted_successfully = project_delete_command(projects, arg)

            elif base_command == "taskadd":
                task_args = arg.split(" ", 1)
                if len(task_args) > 0:
                    proj_id_for_task = task_args[0].upper()
                    success = task_add_command(projects, proj_id_for_task)
                else:
                    print_error(f"Usage: taskadd <PROJECT_ID>")


            elif base_command == "taskupdate":
                task_args = arg.split(" ", 1)
                if len(task_args) > 0:
                    proj_id_for_task = task_args[0].upper()
                    success = task_update_command(projects, arg, profiles)
                else:
                    print_error(f"Usage: taskupdate <PROJECT_ID> <TASK_ID> <status|assigned> <VALUE>")


            elif base_command == "taskdelete":
                task_args = arg.split(" ", 1)
                if len(task_args) > 0:
                    proj_id_for_task = task_args[0].upper()
                    success = task_delete_command(projects, arg)
                else:
                    print_error(f"Usage: taskdelete <PROJECT_ID> <TASK_ID>")

            # --- New Export/Import Commands ---
            elif base_command == "exportdata":
                export_all_data(profiles, stories, projects, load_session_history()) # Pass current state

            elif base_command == "importdata":
                # Need to pass mutable objects for them to be updated
                import_all_data(profiles, stories, projects, load_session_history())
                # Re-load from files after import to ensure all in-memory copies are fresh
                profiles = load_profiles()
                stories = load_logs()
                projects = load_projects()
                # Re-populate log_dates after import to reflect any changes
                log_dates = {}
                for lid, entry in stories.items():
                    if entry and isinstance(entry, list) and len(entry) > 0 and "—" in entry[0]:
                        log_dates[lid] = entry[0].split("—")[0].strip()
                    elif entry and isinstance(entry, list) and len(entry) > 0:
                        log_dates[lid] = entry[0].strip()
                    else:
                        log_dates[lid] = "No Date (Malformed Entry)"

            # --- System/Utility Commands ---
            elif base_command == "clear":
                clear_screen()
                print(PLATECORE_ASCII_ART) # Re-display art after manual clear
                time.sleep(0.5) # Small pause
                pause_print(f"{COLORS['yellow']}Type 'login' to log in or 'help' for available commands.{RESET}")
            
            elif base_command == "whoami":
                who_am_i_command()

            elif base_command == "history":
                show_session_history()

            elif base_command == "help":
                if arg:
                    show_help(arg) # Pass the argument to show_help for specific category
                else:
                    show_help() # Call without argument to show categories

            elif base_command == "exit":
                pause_print(f"{COLORS['yellow']}Exiting session...{RESET}")
                # Record exit event for current user, or 'UNKNOWN' if not logged in
                record_session_event(current_platecore_id if current_platecore_id else "UNKNOWN", "Exit", current_session_start_time, datetime.now(malaysia_tz))
                clear_session()
                return

            elif command_raw == "hyprctl dispatch exit":
                pause_print(f"{COLORS['yellow']}Restarting... Please wait for the new prompt.{RESET}")
                # Record restart event for current user, or 'UNKNOWN' if not logged in
                record_session_event(current_platecore_id if current_platecore_id else "UNKNOWN", "Restart", current_session_start_time, datetime.now(malaysia_tz))
                clear_session()
                time.sleep(1)
                os.execv(sys.executable, [sys.executable] + sys.argv)

            else:
                print_error(f"'{command_raw}' is not recognized as an internal or external command,")
                print_error(f"operable program or batch file.")

    except Exception as e:
        # This will now print the exact type and representation of the exception
        print_error(f"An unexpected error occurred: {type(e).__name__}: {repr(e)}")
        record_session_event(current_platecore_id if current_platecore_id else "UNKNOWN", "Error Exit", current_session_start_time, datetime.now(malaysia_tz))
    finally:
        pass


if __name__ == "__main__":
    main()


