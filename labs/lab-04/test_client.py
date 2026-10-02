"""
AIP444 Lab 4: Structured Outputs & Code Reading
Student Name: Wenjun Wei
Student ID: 169010238
Date: 10/09/2026

Description:
Client testing script to send a POST request with notes and card count 
to the local FastAPI server and print the structured JSON response.
"""

import requests
import json
import time

notes_path = "notes.md"

def test_server():
    try:
        print(f"📖 Reading notes from: {notes_path}")
        with open(notes_path, "r", encoding="utf-8") as f:
            notes_content = f.read()

        payload = {
            "notes": notes_content,
            "cards": 2
        }

        print("⚡ Sending request to server...")
        start_time = time.time()

        response = requests.post(
            "http://localhost:3000/api/generate",
            json=payload
        )

        end_time = time.time()
        print(f"⏱️  Request took {end_time - start_time:.2f}s")

        if response.status_code != 200:
            print(f"❌ Server error {response.status_code}: {response.text}")
            return

        data = response.json()

        print("\n✅ Success! Received Structured Data:")
        print(json.dumps(data, indent=2))

    except FileNotFoundError:
        print(f"❌ Error: Could not find file at {notes_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_server()