import os
from dotenv import load_dotenv
from openai import OpenAI
from schemas import FlashcardResponse

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"  
)

async def generate_flashcards(notes: str, cards: int) -> FlashcardResponse:
    prompt_path = os.path.join(os.path.dirname(__file__), "SYSTEM_PROMPT.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    completion = client.chat.completions.parse(
        model="gpt-4o-mini", 
        messages=[
            {
                "role": "system",
                "content": f"{system_prompt}\n\nPlease generate exactly {cards} flashcard(s) based on the notes provided."
            },
            {
                "role": "user",
                "content": notes
            }
        ],
        response_format=FlashcardResponse,
    )

    return completion.choices[0].message.parsed