"""
AIP444 Lab 5: Tool Calling with GitHub Context - Test Tool
Student Name: Wenjun Wei
Student ID: 169010238
Date: 10/09/2026

Description:
This script tests the `read_github_files` tool independently by invoking it with 
a sample request to a public GitHub repository (e.g., Microsoft VS Code package.json) 
to verify successful retrieval and formatting.
"""

from tools import read_github_files

def test():
    print("Testing read_github_files...\n")

    content = read_github_files([
        {
            "owner": "microsoft",
            "repo": "vscode",
            "path": "package.json",
            "ref": "main"
        }
    ])

    print("--- Test Result Output ---")
    print(content)
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test()