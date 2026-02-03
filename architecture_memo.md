# ARCHITECTURE MEMO: sphere v0.1.0

**DOCUMENT ID**: ARCH-20260202-RH-LT
**STATUS**: Final
**AUTHORS**: Rich Hickey (Data-Oriented Design), Linus Torvalds (Systems Correctness)

---

## 1. Guiding Principles

1.  **Local First, Local Only**: The system must function entirely on the user's local machine with no required network access beyond the LLM API call.
2.  **Simplicity over Complexity**: We will choose the simplest possible implementation that is correct and robust. Anything more is a bug.
3.  **Data as the Log**: The primary artifact of this system is an immutable, chronological log of analyses. The tool is a mechanism for appending to this log.
4.  **No Magic**: The file system is the database. Git is the transaction log. There are no hidden components.

## 2. Directory Structure

The tool will operate within two primary locations:

1.  **The Application Directory**: `/home/ubuntu/sphere_cli/`
2.  **The User Data Directory**: `~/.sphere/`

### 2.1 Application Directory (`/home/ubuntu/sphere_cli/`)

This directory contains the source code for the tool.

```
/home/ubuntu/sphere_cli/
├── sphere/                  # The main Python package
│   ├── __init__.py
│   ├── main.py              # Core execution logic (Beck)
│   ├── logic.py             # The 12-agent workflow logic
│   └── audit.py             # Error handling & logging (Hamilton)
├── setup.py                 # Packaging script (Torvalds)
├── requirements.txt         # Dependencies
└── README.md
```

### 2.2 User Data Directory (`~/.sphere/`)

This directory is the user's private, local data store. It is a Git repository.

-   **Initialization**: The `main.py` script will be responsible for creating this directory and running `git init` if it does not exist upon first execution.
-   **Structure**: The structure is intentionally flat.

```
~/.sphere/
├── .git/                    # The immutable log
├── report_20260202_143005.md # Example report
├── report_20260202_150112.md # Another report
└── ...
```

## 3. Data Schema: The Report

Each analysis generates a single Markdown file. The file is self-contained.

-   **Filename**: `report_<YYYYMMDD>_<HHMMSS>.md` (e.g., `report_20260202_143005.md`). The timestamp is UTC.
-   **Format**: Standard Markdown.

### Report Structure (Inside the Markdown file)

```markdown
# Analysis Report

- **Timestamp**: 2026-02-02T14:30:05Z
- **Query**: "<The user's original question>"

---

## Synthesis

<The final, synthesized output from the 12-agent workflow.>

---

## Audit Trail

<A log of the key steps, agent handoffs, and any errors encountered during the analysis. This is for debugging and transparency.>
```

## 4. The Immutable Log: Git Integration

After a report is successfully generated and saved, the `main.py` script will perform the following Git operations within the `~/.sphere/` directory:

1.  `git add .`
2.  `git commit -m "Analysis complete: <YYYY-MM-DD HH:MM:SS>"`

This creates an atomic, timestamped record of the state of the user's sphere after each analysis. It is simple, robust, and requires no external database.

## 5. Conclusion

This architecture is sufficient. It is simple enough to be implemented correctly and robust enough to be reliable. It provides the core value—an immutable log of analyses—without any unnecessary complexity.

**// END OF MEMO //**
