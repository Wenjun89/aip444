# assignments/assignment-01/review.py
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
import sys
import json
import asyncio
import argparse
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  

from tools import read_file, ripgrep
from reviewers import TOOL_SCHEMAS, SECURITY_AUDITOR_PROMPT, MAINTAINABILITY_CRITIC_PROMPT
from judge import synthesize_and_generate_html


def get_git_staged_diff() -> str:
    """Retrieves git diff for staged changes (Git Mode)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return ""


async def run_reviewer_agent(
    client: OpenAI,
    model_name: str,
    system_prompt: str,
    input_text: str,
    debug_mode: bool,
    reviewer_name: str
) -> str:
    """
    Runs a single reviewer agent, handling tool calls (read_file, ripgrep) iteratively
    until the model produces its final JSON structured output.
    """
    if debug_mode:
        sys.stderr.write(f"[Debug] [{reviewer_name}] Started analysis.\n")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the code or git diff to review:\n\n{input_text}"}
    ]

    for turn in range(5):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.1
            )
            
            response_message = response.choices[0].message
            messages.append(response_message)

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    if debug_mode:
                        sys.stderr.write(f"[Debug] [{reviewer_name}] Calling tool '{function_name}' with args: {function_args}\n")

                    tool_output = ""
                    if function_name == "read_file":
                        tool_output = read_file(**function_args)
                    elif function_name == "ripgrep":
                        tool_output = ripgrep(**function_args)
                    else:
                        tool_output = f"Error: Unknown tool '{function_name}'"

                    if debug_mode:
                        sys.stderr.write(f"[Debug] [{reviewer_name}] Tool output received ({len(tool_output)} characters).\n")

                    # Feed tool output back to the model
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_output
                    })
            else:
                findings_text = response_message.content or "[]"
                if debug_mode:
                    sys.stderr.write(f"[Debug] [{reviewer_name}] Finished analysis. Raw findings JSON:\n{findings_text}\n")
                return findings_text

        except Exception as e:
            if debug_mode:
                sys.stderr.write(f"[Debug] [{reviewer_name}] Error during execution: {str(e)}\n")
            break

    return "[]"


async def main_async():
    parser = argparse.ArgumentParser(description="AI Code Review CLI Tool")
    parser.add_argument("--file", type=str, help="Path to a specific file to review (File Mode).")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode, printing detailed logs to stderr.")
    parser.add_argument("--output", type=str, help="Custom output path for the final HTML report.")
    args = parser.parse_args()

    input_text = ""
    if args.file:
        if args.debug:
            sys.stderr.write(f"[Debug] Running in File Mode for file: {args.file}\n")
        input_text = read_file(args.file)
        if input_text.startswith("Error:"):
            print(input_text, file=sys.stderr)
            sys.exit(1)
    else:
        if args.debug:
            sys.stderr.write("[Debug] Running in Git Mode (checking staged changes)...\n")
        input_text = get_git_staged_diff()
        if not input_text:
            print("Error: No staged changes found in git. Stage changes using 'git add' or use --file <filename>.", file=sys.stderr)
            sys.exit(1)

    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    reviewer_model = "openai/gpt-4o-mini"
    judge_model = "openai/gpt-4o"

    if args.debug:
        sys.stderr.write("[Debug] Phase 1: Launching parallel review assistants (Security Auditor & Maintainability Critic)...\n")

    r1_task = run_reviewer_agent(
        client, reviewer_model, SECURITY_AUDITOR_PROMPT, input_text, args.debug, "SecurityAuditor"
    )
    r2_task = run_reviewer_agent(
        client, reviewer_model, MAINTAINABILITY_CRITIC_PROMPT, input_text, args.debug, "MaintainabilityCritic"
    )

    reviewer1_findings, reviewer2_findings = await asyncio.gather(r1_task, r2_task)

    if args.debug:
        sys.stderr.write("[Debug] Phase 2: Handing findings over to Lead Developer (Judge) for synthesis and HTML generation...\n")

    output_filename = synthesize_and_generate_html(
        client=client,
        model_name=judge_model,
        original_input=input_text,
        reviewer1_findings=reviewer1_findings,
        reviewer2_findings=reviewer2_findings,
        output_filename=args.output
    )

    if output_filename:
        print(f"Success! Review report generated and saved to: {output_filename}")
    else:
        print("Error: Failed to generate review report.", file=sys.stderr)
        sys.exit(1)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()