import os
import sys
import datetime
import subprocess
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

FULL_NAME = "[Wenjun Wei]"
STUDENT_ID = "[169010238]"
run_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

print(f"git-cm: Developed by {FULL_NAME} - {STUDENT_ID}")
print(f"Run Date: {run_date}")
print("-" * 62)

load_dotenv(find_dotenv())
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found")
    sys.exit(1)

is_creative = "--creative" in sys.argv

try:
    result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True, check=True)
    diff = result.stdout.strip()
    if not diff:
        print("❌ No staged changes found")
        sys.exit(1)
    print(f"✅ Diff found: {len(diff)} characters")
except subprocess.CalledProcessError:
    print("❌ Not a git repo.")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODEL_NAME = "openrouter/free"

if is_creative:
    system_prompt = (
        "Use Gitmoji and write a commit message using 17th Century Pirate slang. "
        "Output ONLY the commit message with no Markdown and no rationale."
    )
    temperature = 0.9
else:
    system_prompt = (
        "You are an LLM running in a CLI tool, which writes semantic commit messages for the user. "
        "You will be given a git diff. You must output ONLY the commit message using the Conventional Commits "
        "standard format (e.g., 'feat: add logging'). Respond in plain text suitable for pasting into "
        "git commit -m '...'; just the plain text commit message with no Markdown, no rationale."
    )
    temperature = 0.1

print("\nGenerating Commit Message options...")
for i in range(1, 3):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": diff}
            ],
            temperature=temperature
        )
        commit_message = response.choices[0].message.content.strip()
        print(f"\n[Option {i}]:")
        print(commit_message)
    except Exception as e:
        print(f"\n❌ Error on Option {i}: {e}")