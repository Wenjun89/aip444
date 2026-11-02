/**
 * AIP444 Lab 6: Semantic Search & Vector Spaces
 * Author: Wenjun Wei
 * Student ID: 169010238
 * Program: Computer Programming and Analysis
 * Description: A semantic search engine built for a product catalog using DummyJSON data. 
 *              It serializes product properties to prevent context rot, computes high-dimensional 
 *              embeddings via OpenAI (openai/text-embedding-3-small), utilizes dot product for 
 *              cosine similarity, implements a similarity threshold to prevent hallucinations, 
 *              and integrates Cohere (cohere/rerank-4-pro) for cross-encoder reranking.
 */

import { loadDatabase, searchProducts } from './utils.js'; 
import * as readline from 'readline';
import 'dotenv/config';

async function main() {
  console.log("Loading database and vector index...");
  const products = await loadDatabase();
  console.log(`Loaded ${products.length} products successfully.\n`);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const promptUser = () => {
    rl.question("What are you looking for? (Type 'exit' to quit): ", async (query) => {
      if (query.toLowerCase() === 'exit') {
        rl.close();
        return;
      }

      if (!query.trim()) {
        promptUser();
        return;
      }

      try {
        const results = await searchProducts(query, products);

        if (results.length === 0) {
          console.log("\nI'm sorry, we don't have anything like that in stock.\n");
        } else {
          console.log(`\nFound ${results.length} matches:`);
          results.forEach((item, index) => {
            const rerank = item.rerankScore ? item.rerankScore.toFixed(2) : 'N/A';
            const vector = item.vectorScore ? item.vectorScore.toFixed(2) : 'N/A';
            console.log(`${index + 1}. ${item.title} - $${item.price} [Rerank: ${rerank} | Vector: ${vector}]`);
          });
          console.log("");
        }
      } catch (error) {
        console.error("Error during search:", error);
      }

      promptUser();
    });
  };

  promptUser();
}

main();