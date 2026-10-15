# assignments/assignment-01/judge.py
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
from datetime import datetime
from openai import OpenAI

JUDGE_SYSTEM_PROMPT = """You are "The Lead Developer" (The Judge). Your goal is to review, de-duplicate, validate, and synthesize findings from reviewers into a single, professional HTML report."""

def synthesize_and_generate_html(client: OpenAI, model_name: str, original_input: str, reviewer1_findings: str, reviewer2_findings: str, output_filename: str = None) -> str:
    user_prompt = f"Original Code:\n{original_input}\n\nReviewer 1:\n{reviewer1_findings}\n\nReviewer 2:\n{reviewer2_findings}\n\nSynthesize these into a professional HTML report."
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        
        html_content = response.choices[0].message.content.strip()
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        elif html_content.startswith("```"):
            html_content = html_content[3:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
        html_content = html_content.strip()

        if not output_filename:
            timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            output_filename = f"review-{timestamp}.html"

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_filename
    except Exception as e:
        print(f"Error: {str(e)}")
        return None