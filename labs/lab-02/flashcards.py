#!/usr/bin/env python3
"""
Lab 2: ACE Flashcard Generator
Author: Wenjun Wei
Program: Computer Programming and Analysis, Seneca Polytechnic
Description: A CLI tool that converts course notes into custom ACE format 
             flashcards using OpenRouter.ai and prompt engineering.
"""

import os
import sys
import argparse
import re
from dotenv import load_dotenv
from openai import OpenAI

def print_header():
    print("=" * 60)
    print("  AIP444 Lab 2: ACE Flashcard Generator")
    print("  Student Name: Wenjun Wei")
    print("  Program: Computer Programming and Analysis")
    print("=" * 60)

def initialize_client():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY is not set in the environment or .env file.")
        sys.exit(1)
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return client

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert course notes into custom ACE format flashcards."
    )
    parser.add_argument(
        "notes_path",
        help="Path to the course notes file (Markdown, text, or HTML)."
    )
    parser.add_argument(
        "--cards",
        type=int,
        default=3,
        help="Number of flashcards to generate (minimum 1, maximum 5, default: 3)."
    )

    args = parser.parse_args()

    if args.cards < 1 or args.cards > 5:
        print("❌ Error: --cards must be between 1 and 5.")
        sys.exit(1)

    return args

def get_file_contents(path, description):
    """Read a file safely and return its contents, or exit on error."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            if not content.strip():
                print(f"⚠️ Warning: The {description} at '{path}' is empty.")
            return content
    except FileNotFoundError:
        print(f"❌ Error: {description} not found at path: {path}")
        sys.exit(1)
    except Exception as err:
        print(f"❌ Error reading {description} ({path}): {err}")
        sys.exit(1)

def main():
    print_header()
    
    args = parse_arguments()
    notes_path = args.notes_path
    num_cards = args.cards

    system_prompt = get_file_contents("SYSTEM_PROMPT.md", "System prompt file")
    notes_content = get_file_contents(notes_path, "Notes file")

    client = initialize_client()

    card_templates = "\n".join([
        f"=== CARD {i} ===\n-APPLICATION: ...\n-CHALLENGE: ...\n-ANSWER: ...\n-EVIDENCE: \"...\"\n-MISCONCEPTION: \"...\"\n-CORRECTION: ...\n===" 
        for i in range(1, num_cards + 1)
    ])

    user_prompt = f"""
Generate exactly {num_cards} flashcards in the ACE format based on the following notes.

You must output ALL {num_cards} cards following this exact structure template:
{card_templates}

<notes>
{notes_content}
</notes>
"""

    print(f"\n⏳ Analyzing notes and generating {num_cards} flashcard(s)...")

    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3, 
        )

        output = response.choices[0].message.content

        if not output:
            print("\n❌ Error: The model returned empty content or was filtered.")
            sys.exit(1)

        cards = re.findall(
            r'(=== CARD \d+ ===.*?)(?=(=== CARD \d+ ===|\Z))',
            output,
            re.DOTALL
        )
        
  
        card_list = [c[0].strip() for c in cards if c[0].strip().startswith("=== CARD")]

        if not card_list:
            print("\n📌 Model Raw Output:\n")
            print(output)
            sys.exit(0)

        print(f"\n✅ Successfully generated {len(card_list)} flashcard(s):\n")
        print("-" * 60)
        for card in card_list:
            print(card)
            print("-" * 60)

    except Exception as err:
        print(f"\n❌ API Error during generation: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()