"""
AIP444 Lab 5: Tool Calling with GitHub Context
Student Name: Wenjun Wei
Student ID: 169010238
Date: 10/09/2026

Description:
This module implements the `read_github_files` tool for fetching raw file contents 
from GitHub repositories. It handles large file truncation, line counting, error 
management, and data formatting to support LLM tool calling in the pr-advice utility.
"""

import os
import requests

def read_github_files(files):
    """
    Reads one or more files from GitHub repositories using the raw GitHub URL pattern.
    
    Parameters:
    - files (list of dict): A list of dictionaries, where each dictionary contains:
        - owner (str): The GitHub username or organization.
        - repo (str): The repository name.
        - path (str): The file path within the repository.
        - ref (str, optional): The branch name, tag, or commit SHA (defaults to "main").
        
    Returns:
    - str: A formatted string containing the contents of the requested files, 
           or an appropriate error message if retrieval fails.
    """
    results = []
    
    for file_info in files:
        owner = file_info.get("owner")
        repo = file_info.get("repo")
        path = file_info.get("path")
        ref = file_info.get("ref", "main")  
        
        # --- Design Decision: Input Validation ---
        # Validate required parameters early to prevent malformed requests and 
        # return a clear error message back to the LLM.
        if not all([owner, repo, path]):
            results.append(f"Error: Missing required parameters ('owner', 'repo', or 'path') for file request.")
            continue

        if "/" not in ref and ref not in ["main", "master", "dev", "develop"]:
            ref_path = f"refs/heads/{ref}"
        elif ref.startswith("refs/"):
            ref_path = ref
        else:
            ref_path = f"refs/heads/{ref}"

        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref_path}/{path}"
        
        try:
            response = requests.get(url, timeout=10)
            
            # --- Error Handling: HTTP Status Codes ---
            # Handle specific HTTP errors (404 Not Found, 403 Forbidden/Rate Limit) 
            # gracefully by appending readable error messages instead of raising exceptions.
            if response.status_code == 404:
                results.append(f"--- File: {path} ---\nError: File not found (404). Please verify the owner, repo, branch, or path.")
                continue
            elif response.status_code == 403:
                results.append(f"--- File: {path} ---\nError: Access forbidden or rate limit exceeded (403).")
                continue
            
            response.raise_for_status()
            file_content = response.text
            
            # --- Large File Handling: Line Counting & Truncation ---
            # To prevent overloading the LLM context window with massive files, 
            # we count the total lines and truncate the file if it exceeds max_lines.
            max_lines = 1000
            lines = file_content.splitlines(keepends=True)
            total_lines = len(lines)
            
            if total_lines > max_lines:
                truncated_lines = lines[:max_lines]
                file_content = "".join(truncated_lines)
                file_content += f"\n[File truncated: showing first {max_lines} of {total_lines} lines]"
            
            results.append(f"--- File: {path} (Repo: {owner}/{repo}@{ref}) ---\n{file_content}")
        
        # --- Error Handling: Network & Request Exceptions ---
        # Catch network timeouts, connection drops, or other request exceptions 
        # to ensure the tool remains stable and doesn't crash the main application.
        except requests.exceptions.RequestException as e:
            results.append(f"--- File: {path} ---\nError fetching file from network: {str(e)}")
            
    return "\n\n".join(results)