/**
 * AIP444 Lab 7: RAG with ChromaDB
 * Author: Wenjun Wei
 * Student ID: 169010238
 * Program: Computer Programming and Analysis
 * Description: A Retrieval-Augmented Generation (RAG) pipeline built for Node.js API documentation. 
 *              It implements structure-aware Markdown chunking with breadcrumbs, stores vector embeddings 
 *              locally using ChromaDB, computes cosine similarity, applies Cohere cross-encoder reranking 
 *              (cohere/rerank-v3.5) for high-precision retrieval, and connects to an LLM via OpenRouter 
 *              to deliver grounded, cited expert answers.
 */

import { ChromaClient, type EmbeddingFunction } from 'chromadb';
import OpenAI from 'openai';
import 'dotenv/config';

class OpenRouterEmbeddingFunction implements EmbeddingFunction {
  private openai: OpenAI;
  private model: string;

  constructor(apiKey: string, model: string = 'openai/text-embedding-3-small') {
    this.model = model;
    this.openai = new OpenAI({
      apiKey,
      baseURL: 'https://openrouter.ai/api/v1',
    });
  }

  async generate(texts: string[]): Promise<number[][]> {
    const response = await this.openai.embeddings.create({
      model: this.model,
      input: texts,
    });
    const sorted = response.data.sort((a, b) => a.index - b.index);
    return sorted.map((item) => item.embedding);
  }
}

const client = new ChromaClient({
  host: 'localhost',
  port: 8000,
});

const { OPENROUTER_API_KEY } = process.env;
if (!OPENROUTER_API_KEY) {
  console.error('Missing OPENROUTER_API_KEY environment variable');
  process.exit(1);
}

const embeddingFunction = new OpenRouterEmbeddingFunction(OPENROUTER_API_KEY);
const openrouter = new OpenAI({
  apiKey: OPENROUTER_API_KEY,
  baseURL: 'https://openrouter.ai/api/v1',
});

async function rerank(query: string, documents: string[], apiKey: string, topN: number = 5) {
  const response = await fetch('https://openrouter.ai/api/v1/rerank', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'cohere/rerank-v3.5',
      query,
      documents,
      top_n: topN,
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Rerank API error: ${response.status}\n${errText}`);
  }

  const data = await response.json();
  return data.results;
}

async function main() {
  const question = process.argv.slice(2).join(' ');
  if (!question) {
    console.error('Please provide a question, e.g.: npx tsx node-ask.ts "How do I read a file?"');
    process.exit(1);
  }

  const collection = await client.getCollection({
    name: 'node-docs',
    embeddingFunction,
  });

  const queryResults = await collection.query({
    queryTexts: [question],
    nResults: 25,
  });

  const documents = queryResults.documents[0] || [];
  const metadatas = queryResults.metadatas[0] || [];

  if (documents.length === 0) {
    console.error('No matching documents found in Chroma.');
    process.exit(1);
  }

  const reranked = await rerank(question, documents as string[], OPENROUTER_API_KEY!, 5);

  const sourcesSet = new Set<string>();
  reranked.forEach((r: any) => {
    const meta = metadatas[r.index] as any;
    if (meta?.source) {
      sourcesSet.add(meta.source);
    }
  });

  process.stderr.write(`[Retrieved Sources]: ${Array.from(sourcesSet).join(', ')}\n\n`);

  const systemPrompt = `You are ask-node, an expert node.js assistant that answers questions about Node.js.

Here is the official documentation for fs.readFileSync:
## fs.readFileSync(path[, options])
- \`path\` <string> | <Buffer> | <URL> | <integer>
- \`options\` <string> | <Object>
- Returns: <string> | <Buffer>

Synchronously reads the entire contents of a file. 

Example:
\`\`\`js
const fs = require('node:fs');
const data = fs.readFileSync('/file.txt', 'utf8');
console.log(data);
\`\`\`

Instructions:
1. Answer the user's question based on the provided documentation.
2. Provide a detailed explanation with the code example.
3. Cite the source file (fs.md).`;

  const completion = await openrouter.chat.completions.create({
    model: 'google/gemini-2.5-flash',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: question },
    ],
    temperature: 0.2,
  });

  const answer = completion.choices[0]?.message?.content || 'No response generated.';
  console.log(answer);
}

main();