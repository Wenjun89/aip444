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
import { writeFile } from 'fs/promises';
import { serializeProduct } from './utils.js';
import fetch from 'node-fetch';
import 'dotenv/config';
async function main() {
    console.log("Fetching products from DummyJSON...");
    const res = await fetch('https://dummyjson.com/products?limit=200');
    const data = await res.json();
    const products = data.products;
    await writeFile('products.json', JSON.stringify(products, null, 2));
    console.log("Saved products.json");
    const texts = products.map((p) => serializeProduct(p));
    console.log("Generating embeddings via OpenRouter...");
    const embedRes = await fetch('https://openrouter.ai/api/v1/embeddings', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model: 'openai/text-embedding-3-small',
            input: texts,
        }),
    });
    const embedData = await embedRes.json();
    const embeddings = embedData.data.map((item) => item.embedding);
    const vectorLines = embeddings.map((vec) => vec.join('\t')).join('\n');
    await writeFile('vectors.tsv', vectorLines);
    console.log("Saved vectors.tsv");
    const metaLines = ["Title\tCategory"];
    for (const p of products) {
        const cleanTitle = p.title.replace(/[\t\n]/g, ' ');
        const cleanCategory = p.category.replace(/[\t\n]/g, ' ');
        metaLines.push(`${cleanTitle}\t${cleanCategory}`);
    }
    await writeFile('metadata.tsv', metaLines.join('\n'));
    console.log("Saved metadata.tsv");
    console.log("Indexing complete!");
}
main();
