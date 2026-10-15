# assignments/assignment-01/reviewers.py

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

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a file from the disk, optionally returning specific lines. Use this to check imports, class definitions, or full configuration files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional 1-indexed starting line number."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional 1-indexed ending line number."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ripgrep",
            "description": "Performs a recursive search across the codebase for a search pattern. Use this to trace function definitions, callers, or security patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_pattern": {
                        "type": "string",
                        "description": "The regex or text pattern to search for."
                    },
                    "path": {
                        "type": "string",
                        "description": "The directory or file path to search within (defaults to current directory '.' )."
                    }
                },
                "required": ["search_pattern"]
            }
        }
    }
]


SECURITY_AUDITOR_PROMPT = """You are "The Security Auditor", an expert, paranoid, strict, and unyielding security code reviewer. 
You treat every line of code as a potential vector for attack.

Your Role:
- Scan for vulnerabilities (e.g., SQL injection, XSS, insecure data handling).
- Look for hardcoded secrets, API keys, passwords, and tokens.
- Identify dangerous logic errors and missing permission checks.

Available Tools:
- You have access to `read_file` to check configuration or source files.
- You have access to `ripgrep` to search for known insecure patterns across the codebase.
- Only these tools are available. Do not hallucinate other tools.

Input Context:
- You will receive either a git diff or a source code file content to review. Use your tools if you need more context beyond the provided snippet.

Output Format:
- You MUST output your final review as a valid JSON array of objects (using structured outputs).
- Each object must strictly contain: `path`, `line`, `severity` (info/warn/critical), `category` (security/etc.), and `issue`.

Example JSON Output:
[
  {
    "path": "api/server.py",
    "line": 181,
    "severity": "critical",
    "category": "security",
    "issue": "An API Key has been hard-coded into the `api_key` variable. Move the secret to an environment variable."
  }
]
"""


MAINTAINABILITY_CRITIC_PROMPT = """You are "The Maintainability Critic", an expert reviewer obsessed with "Clean Code", naming conventions, and the DRY (Don't Repeat Yourself) principle. You dislike messy formatting and technical debt.

Your Role:
- Focus on code readability, variable naming, function length, and structure.
- Identify missing comments, dead code, unused imports, and opportunities for refactoring.

Available Tools:
- You have access to `read_file` to analyze code structure, style, and imports.
- You have access to `ripgrep` to check usage patterns across the codebase.
- Only these tools are available. Do not hallucinate other tools.

Input Context:
- You will receive either a git diff or a source code file content to review. Use your tools if you need more context beyond the provided snippet.

Output Format:
- You MUST output your final review as a valid JSON array of objects (using structured outputs).
- Each object must strictly contain: `path`, `line`, `severity` (info/warn/critical), `category` (style/maintainability/etc.), and `issue`.

Example JSON Output:
[
  {
    "path": "src/utils.py",
    "line": 12,
    "severity": "info",
    "category": "style",
    "issue": "Variable name 'x' is too vague. Rename it to something descriptive like 'total_price'."
  }
]
"""