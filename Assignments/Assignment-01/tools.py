"""
AIP444 Assignment 1: AI Code Review 
Author: Wenjun Wei
Student ID: 169010238
Program: Computer Programming and Analysis
Description: A multi-agent CLI code review tool supporting Git Mode and File Mode. 
             It utilizes parallel specialized reviewers (The Security Auditor and The Maintainability Critic) 
             equipped with local file reading and ripgrep tools, whose findings are validated and 
             synthesized by a Lead Developer (Judge) model to generate a professional, self-contained HTML report.
"""

import os
import subprocess
from typing import Optional

def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """
    Reads a file from disk using only the Python standard library.
    Supports optional start_line and end_line parameters (1-indexed).
    Includes safety truncation for excessively large files to protect token limits.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        
        if not os.path.isfile(file_path):
            return f"Error: Path '{file_path}' is not a valid file."

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total_lines = len(lines)
        
        MAX_LINES_LIMIT = 1000
        is_truncated_by_size = False

        if total_lines > MAX_LINES_LIMIT and (end_line is None or (end_line - (start_line or 1)) > MAX_LINES_LIMIT):
            if start_line is None:
                start_line = 1
            end_line = min(start_line + MAX_LINES_LIMIT - 1, total_lines)
            is_truncated_by_size = True

        if start_line is not None or end_line is not None:
            start_idx = max(0, (start_line - 1) if start_line else 0)
            end_idx = min(total_lines, end_line if end_line else total_lines)
            selected_lines = lines[start_idx:end_idx]
            file_content = "".join(selected_lines)
            header = f"--- File: {file_path} (Showing lines {start_idx + 1} to {end_idx} of {total_lines}) ---\n"
        else:
            file_content = "".join(lines)
            header = f"--- File: {file_path} (Total lines: {total_lines}) ---\n"

        if is_truncated_by_size:
            file_content += f"\n[Warning: File truncated to {MAX_LINES_LIMIT} lines due to size constraints.]"

        return header + file_content

    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"


def ripgrep(search_pattern: str, path: str = ".") -> str:
    """
    Performs a recursive search across the codebase using the 'ripgrep' (rg) command-line tool.
    Returns matching lines, file paths, and line numbers.
    """
    try:
        result = subprocess.run(
            ["rg", "--line-number", "--no-heading", "--smart-case", search_pattern, path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            max_output_length = 5000
            if len(output) > max_output_length:
                output = output[:max_output_length] + "\n[Output truncated due to excessive length]"
            return f"--- Ripgrep Search Results for '{search_pattern}' ---\n{output}"
        elif result.returncode == 1:
            return f"Info: No matches found for pattern '{search_pattern}'."
        else:
            return f"Error executing ripgrep: {result.stderr.strip()}"
            
    except FileNotFoundError:
        return "Error: 'rg' (ripgrep) is not installed or not found in system PATH. Please ensure ripgrep is installed."
    except subprocess.TimeoutExpired:
        return "Error: Ripgrep search timed out."
    except Exception as e:
        return f"Error during ripgrep execution: {str(e)}"