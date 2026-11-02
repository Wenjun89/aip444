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
import { readFile } from 'fs/promises';
import fetch from 'node-fetch';
export const MIN_SIMILARITY_SCORE = 0.45;
export function serializeProduct(product) {
    return `Title: ${product.title} | Category: ${product.category} | Description: ${product.description} | Tags: ${product.tags?.join(', ')} | Brand: ${product.brand || 'N/A'}`;
}
export function dotProduct(vecA, vecB) {
    return vecA.reduce((sum, val, i) => sum + val * vecB[i], 0);
}
export async function loadDatabase() {
    const productsData = await readFile('products.json', 'utf-8');
    const products = JSON.parse(productsData);
    const vectorsData = await readFile('vectors.tsv', 'utf-8');
    const lines = vectorsData.trim().split('\n');
    const productsWithEmbeddings = products.map((product, index) => {
        const vectorString = lines[index];
        const vector = vectorString.split('\t').map(Number);
        return { ...product, embedding: vector };
    });
    return productsWithEmbeddings;
}
export async function rerankResults(query, candidates, topN = 5) {
    const documents = candidates.map((p) => serializeProduct(p));
    const response = await fetch('https://openrouter.ai/api/v1/rerank', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model: 'cohere/rerank-4-pro',
            query,
            documents,
            top_n: topN,
        }),
    });
    const data = await response.json();
    if (!data.results) {
        return candidates.slice(0, topN);
    }
    return data.results.map((r) => ({
        ...candidates[r.index],
        rerankScore: r.relevance_score,
    }));
}
export async function searchProducts(query, products, minScore = MIN_SIMILARITY_SCORE) {
    const response = await fetch('https://openrouter.ai/api/v1/embeddings', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model: 'openai/text-embedding-3-small',
            input: query,
        }),
    });
    const data = await response.json();
    const queryEmbedding = data.data[0].embedding;
    const scored = products.map((product) => {
        const score = dotProduct(queryEmbedding, product.embedding);
        return { ...product, vectorScore: score };
    });
    scored.sort((a, b) => b.vectorScore - a.vectorScore);
    const filtered = scored.filter((p) => p.vectorScore >= minScore);
    if (filtered.length === 0) {
        return [];
    }
    const candidates = filtered.slice(0, 20);
    const finalResults = await rerankResults(query, candidates, 5);
    return finalResults;
}
