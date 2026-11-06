import { ChromaClient } from 'chromadb';
import 'dotenv/config';

async function run() {
  const client = new ChromaClient({ host: 'localhost', port: 8000 });
  const collection = await client.getCollection({ name: 'node-docs' });
  const allData = await collection.get();
  
  console.log("=== Chroma Collection: node-docs ===");
  console.log(`Total Chunks / Documents Indexed: ${allData.ids.length}\n`);
  
  allData.ids.forEach((id, index) => {
    console.log(`ID: ${id}`);
    console.log(`Metadata:`, JSON.stringify(allData.metadatas[index]));
    console.log(`Content Preview: ${allData.documents[index]?.substring(0, 80)}...\n`);
  });
}

run();