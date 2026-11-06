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
    throw new Error(`Rerank API error: ${response.status} - ${errText}`);
  }

  const data = await response.json();
  return data.results;
}

async function main() {
  const queryText = process.argv.slice(2).join(' ') || "How do I read a file?";
  console.log(`Querying for: "${queryText}"\n`);

  const collection = await client.getCollection({
    name: 'node-docs',
    embeddingFunction,
  });

  const results = await collection.query({
    queryTexts: [queryText],
    nResults: 25,
  });

  const documents = results.documents[0] || [];
  const metadatas = results.metadatas[0] || [];
  const distances = results.distances ? results.distances[0] : [];

  if (documents.length === 0) {
    console.log("No relevant documents found.");
    return;
  }

  console.log(`Retrieved ${documents.length} candidates from Chroma. Reranking top 5...\n`);

  const rerankedResults = await rerank(queryText, documents as string[], OPENROUTER_API_KEY!, 5);

  console.log("=== RERANKED RESULTS ===");
  for (let i = 0; i < rerankedResults.length; i++) {
    const r = rerankedResults[i];
    const originalIndex = r.index;
    const chromaDistance = distances[originalIndex] ?? 0;
    const chromaSimilarity = 1 - chromaDistance;
    const meta = metadatas[originalIndex] as any;

    console.log(`\n[Rank ${i + 1}] (Original Chroma Rank: ${originalIndex + 1})`);
    console.log(`- Source: ${meta?.source}`);
    console.log(`- Breadcrumb: ${meta?.breadcrumb}`);
    console.log(`- Chroma Distance: ${chromaDistance.toFixed(4)} (Similarity: ${chromaSimilarity.toFixed(4)})`);
    console.log(`- Rerank Relevance Score: ${r.relevance_score.toFixed(4)}`);
    console.log(`- Snippet: ${documents[originalIndex]?.substring(0, 120)}...`);
  }
}

main();