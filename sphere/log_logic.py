'''
Logic for the `sphere log` command.

Author: Rich Hickey
'''

import subprocess
import datetime

def get_log(limit=10, query=None, after=None, before=None):
    """
    Retrieves and parses the Git log from the .sphere repository.
    """
    repo_path = "/home/ubuntu/.sphere"
    base_cmd = [
        "git",
        "-C",
        repo_path,
        "log",
        f"--pretty=format:%H|%at|%s",
        f"-n{limit}",
    ]

    if query:
        base_cmd.append(f"--grep={query}")
    if after:
        base_cmd.append(f"--after={after}")
    if before:
        base_cmd.append(f"--before={before}")

    try:
        result = subprocess.run(base_cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        log_entries = []
        for line in lines:
            if not line:
                continue
            parts = line.split("|")
            if len(parts) == 3:
                hash, timestamp, subject = parts
                dt_object = datetime.datetime.fromtimestamp(int(timestamp))
                log_entries.append({
                    "hash": hash,
                    "date": dt_object.strftime("%Y-%m-%d %H:%M:%S"),
                    "subject": subject,
                })
        return log_entries
    except subprocess.CalledProcessError as e:
        if "does not have any commits" in e.stderr:
            return [] # Return empty list if no commits yet
        print(f"Error getting git log: {e.stderr}")
        return None

def show_report(commit_hash):
    """
    Shows the content of the report file for a specific commit.
    """
    repo_path = "/home/ubuntu/.sphere"

    try:
        # First, get the filename from the commit
        name_cmd = ["git", "-C", repo_path, "show", "--name-only", "--pretty=''", commit_hash]
        name_result = subprocess.run(name_cmd, capture_output=True, text=True, check=True)
        # The first line after the commit info is the filename
        filename = name_result.stdout.strip().split("\n")[-1]

        if not filename.endswith(".md"):
            return "Error: No report file found for this commit."

        # Now, get the content of that file
        show_cmd = ["git", "-C", repo_path, "show", f"{commit_hash}:{filename}"]
        show_result = subprocess.run(show_cmd, capture_output=True, text=True, check=True)
        return show_result.stdout

    except subprocess.CalledProcessError as e:
        return f"Error showing report: {e.stderr}"
    except IndexError:
        return "Error: Could not determine report filename for this commit."
