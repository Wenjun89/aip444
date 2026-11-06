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

import path from 'path';
import fs from 'fs/promises';
import { ChromaClient, type EmbeddingFunction } from 'chromadb';
import OpenAI from 'openai';
import { chunkMarkdown } from './chunker.js';
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

async function main() {
  const collection = await client.getOrCreateCollection({
    name: 'node-docs',
    embeddingFunction,
    configuration: {
      hnsw: {
        space: 'cosine',
      },
    },
  });

  const docsDir = path.join('.', 'docs');
  const files = await fs.readdir(docsDir);

  for (const file of files) {
    if (!file.endsWith('.md')) {
      continue;
    }

    console.log(`Processing ${file}...`);
    const text = await fs.readFile(path.join(docsDir, file), 'utf-8');

    const chunks = chunkMarkdown(text, file);
    if (chunks.length === 0) {
      continue;
    }

    const ids = chunks.map((c) => c.id);
    const documents = chunks.map((c) => c.content);
    const metadatas = chunks.map((c) => c.metadata);

    await collection.add({
      ids,
      documents,
      metadatas,
    });
  }

  console.log('Indexing complete!');
}

main();