# AIP444 Lab 9: Source Credibility Analyzer Agent

An autonomous CLI source credibility evaluation agent built with Node.js, TypeScript, and `@openai/agents` via OpenRouter. It fetches page content through Jina Reader, runs cross-verification searches using the Tavily Search API, records structured six-dimension evaluations with Zod (`assess_credibility`), writes Markdown credibility reports to `reports/`, and saves full execution traces to `traces/`.

## Prerequisites

- Node.js (v18+ or v20+ recommended) and `npm`
- An **OpenRouter** API key (`OPENROUTER_API_KEY`)
- A **Tavily** API key (`TAVILY_API_KEY`)

## Installation

1. Navigate to the Lab 9 directory:
   cd labs/lab-09

Install dependencies: npm install

API Key Configuration
Create a .env file inside labs/lab-09/ (or copy .env.example if present):
OPENROUTER_API_KEY=your_openrouter_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

Save .env without extra spaces around =. Do not commit .env to Git (it is ignored via .gitignore).

Usage
Run the credibility analyzer on a target URL:
npm start -- "[https://example.com/article](https://example.com/article)"

After execution:

Credibility reports are saved under reports/.

Execution traces are saved under traces/.

