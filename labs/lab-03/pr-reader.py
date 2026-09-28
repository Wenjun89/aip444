#!/usr/bin/env python3
"""
Lab 3: GitHub PR Reading Partner
Author: Wenjun Wei
Program: Computer Programming and Analysis, Seneca Polytechnic
Description: A CLI tool that fetches a GitHub PR's diff, details, and comments, 
             incorporates student understanding, and uses an LLM acting as 
             a Senior Engineer to analyze them.
"""

import os
import sys
import argparse
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
import requests

def print_header() -> None:
    print("=" * 60)
    print("  AIP444 Lab 3: GitHub PR Explainer (pr-reader)")
    print("  Student Name: Wenjun Wei")
    print("  Program: Computer Programming and Analysis")
    print("=" * 60)

def initialize_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY is not set in environment or .env file.")
        sys.exit(1)
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/Wenjun89/aip444",
            "X-Title": "AIP444-Lab-03-PR-Explainer",
        }
    )
    return client

def parse_pr_url(url: str) -> Dict[str, str]:
    """Parse standard GitHub PR URL to extract owner, repo, and issue/PR number."""
    pattern = r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip())
    if not match:
        print(f"❌ Error: Invalid GitHub PR URL format: '{url}'")
        print("Expected format: https://github.com/owner/repo/pull/123")
        sys.exit(1)
    
    owner, repo, number = match.groups()
    return {"owner": owner, "repo": repo, "number": number}

def fetch_diff(owner: str, repo: str, number: str) -> str:
    """Fetch the raw diff of the PR from GitHub with a 95,000 character limit."""
    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    headers = {"User-Agent": "AIP444-Lab-03"}
    
    try:
        response = requests.get(diff_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error: Failed to fetch diff (HTTP Status: {response.status_code})")
            sys.exit(1)
        
        diff_text = response.text
        max_chars = 95000
        if len(diff_text) > max_chars:
            print(f"⚠️ Warning: Diff length ({len(diff_text)} chars) exceeds {max_chars} limit. Truncating...")
            diff_text = diff_text[:max_chars] + "\n...[Diff Truncated]..."
            
        return diff_text
    except Exception as err:
        print(f"❌ Error fetching diff: {err}")
        sys.exit(1)

def fetch_pull_request(owner: str, repo: str, issue_num: str) -> Dict[str, str]:
    """Fetch PR metadata (title, body, author, etc.) using GitHub API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{issue_num}"
    headers = {
        "User-Agent": "AIP444-Lab-03",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ GitHub API Error: HTTP {response.status_code}")
            sys.exit(1)
            
        data = response.json()
        return {
            "title": data.get("title", "No Title"),
            "body": data.get("body") or "[No description provided]",
            "author": data.get("user", {}).get("login", "unknown"),
            "created_at": data.get("created_at", ""),
            "url": data.get("html_url", "")
        }
    except Exception as err:
        print(f"❌ Error fetching PR metadata: {err}")
        sys.exit(1)

def fetch_comments(owner: str, repo: str, issue_num: str) -> List[Dict[str, str]]:
    """Fetch issue comments using GitHub API with proper request headers."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments?per_page=100"
    headers = {
        "User-Agent": "AIP444-Lab-03",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            if response.status_code == 403:
                print("❌ GitHub API Error: 403 Forbidden. You may have hit the 60 requests/hour unauthenticated rate limit.")
            else:
                print(f"❌ GitHub API Error: HTTP {response.status_code}")
            sys.exit(1)
            
        data = response.json()
        return [
            {
                "username": item.get("user", {}).get("login", "unknown"),
                "body": item.get("body") or "[No message content]",
                "date": item.get("created_at", "")
            }
            for item in data
        ]
    except Exception as err:
        print(f"❌ Error fetching comments: {err}")
        sys.exit(1)

def get_file_contents(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as err:
        print(f"❌ Error reading system prompt file '{path}': {err}")
        sys.exit(1)

def main() -> None:
    print_header()
    
    parser = argparse.ArgumentParser(description="Analyze GitHub PR code changes and human context.")
    parser.add_argument("pr_url", help="Standard GitHub Pull Request URL")
    args = parser.parse_args()
    
    pr_info_url = parse_pr_url(args.pr_url)
    owner = pr_info_url["owner"]
    repo = pr_info_url["repo"]
    number = pr_info_url["number"]
    
    print(f"\n🔍 Target Repository: {owner}/{repo} | PR #{number}")
    
    system_prompt = get_file_contents("SYSTEM_PROMPT.md")
    
    print("📥 Fetching PR metadata...")
    pr_meta = fetch_pull_request(owner, repo, number)
    
    print("📥 Fetching PR code diff...")
    diff_content = fetch_diff(owner, repo, number)
    
    print("📥 Fetching PR discussion comments via GitHub API...")
    comments = fetch_comments(owner, repo, number)
    
    print("\n" + "~" * 60)
    print("  FORM YOUR INITIAL UNDERSTANDING (Step 4)")
    print("~" * 60)
    interpretation = input("1. In 2-4 sentences, what do you think this PR is changing, and why?\n> ")
    question = input("2. What is one thing about the PR that you don't understand yet?\n> ")
    
    student_understanding_xml = (
        f"<student-understanding>\n"
        f"  <interpretation>\n"
        f"    {interpretation}\n"
        f"  </interpretation>\n"
        f"  <question>\n"
        f"    {question}\n"
        f"  </question>\n"
        f"</student-understanding>"
    )

    comments_xml = "<thread>\n"
    if comments:
        for c in comments:
            comments_xml += f'  <comment username="{c["username"]}" date="{c["date"]}">\n{c["body"]}\n  </comment>\n'
    else:
        comments_xml += '  <comment username="system" date="N/A">\nNo public discussion comments found on this issue timeline.\n  </comment>\n'
    comments_xml += "</thread>"

    user_prompt = (
        f"<pull-request>\n"
        f"  Title: {pr_meta['title']}\n"
        f"  Author: {pr_meta['author']}\n"
        f"  Created At: {pr_meta['created_at']}\n"
        f"  URL: {pr_meta['url']}\n\n"
        f"  Description:\n"
        f"  {pr_meta['body']}\n"
        f"</pull-request>\n\n"
        f"```diff\n"
        f"{diff_content}\n"
        f"```\n\n"
        f"{comments_xml}\n\n"
        f"{student_understanding_xml}"
    )

    print("\n⏳ Sending data to Code-Reading Mentor LLM via OpenRouter...")
    client = initialize_client()
    
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
        
        output = response.choices[0].message.content
        if not output:
            print("❌ Error: Model returned empty response.")
            sys.exit(1)
            
        print("\n" + "=" * 60)
        print("  SENIOR ENGINEER PR ANALYSIS REPORT")
        print("=" * 60 + "\n")
        print(output)
        print("\n" + "=" * 60)
        
    except Exception as err:
        print(f"\n❌ API Error during completion: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()