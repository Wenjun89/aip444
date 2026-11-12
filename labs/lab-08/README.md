# Lab 8: A Visual Debugger

A TypeScript CLI tool that captures or takes screenshots of technical errors, optimizes them, analyzes them using a multimodal LLM (via OpenRouter), and searches the web using the Tavily API to fetch current documentation and solutions.

## Prerequisites

- Node.js (v18+ recommended)
- OpenRouter API Key
- Tavily API Key

## Installation & Dependencies

1. Navigate to the lab directory:
   ```bash
   cd labs/lab-08

Install the required dependencies (sharp, openai, @tavily/core, dotenv, and TypeScript execution tools):

Bash
npm install sharp openai @tavily/core dotenv
npm install -D typescript @types/node tsx

Create a .env file in the lab-08 directory and add your API keys:

Code snippet
OPENROUTER_API_KEY=your_openrouter_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

Run the visual debugger by passing the path to an error screenshot and an optional prompt:

npx tsx img-debug.ts ./error-screenshot.png "Why am I getting this TypeError?"