/**
 * AIP444 Lab 8: A Visual Debugger
 * Author: Wenjun Wei
 * Student ID: 169010238
 * Program: Computer Programming and Analysis
 * Description: A multimodal CLI debugging tool built for Node.js and TypeScript. 
 *              It implements local image pre-processing (Sharp resizing to max 1024px, 
 *              85% JPEG quality compression, and Base64 encoding), multimodal vision analysis 
 *              via OpenRouter using a vision-capable LLM, tool calling integration with the 
 *              Tavily Search API for real-time web documentation retrieval, and a multi-turn 
 *              interaction loop to provide accurate technical error fixes.
 */

import fs from 'fs';
import path from 'path';
import sharp from 'sharp';
import dotenv from 'dotenv';
import OpenAI from 'openai';
import { tavily } from '@tavily/core';
import type { ChatCompletionMessageParam, ChatCompletionTool } from 'openai/resources/chat/completions';

dotenv.config();

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
});

const tvly = tavily({ apiKey: process.env.TAVILY_API_KEY! });

async function processImage(imagePath: string): Promise<string> {
  const absolutePath = path.resolve(imagePath);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`File not found: ${absolutePath}`);
  }

  const originalStats = fs.statSync(absolutePath);
  const originalSizeBytes = originalStats.size;

  const processedBuffer = await sharp(absolutePath)
    .rotate() 
    .resize(1024, 1024, { fit: 'inside', withoutEnlargement: true })
    .flatten({ background: '#ffffff' }) 
    .jpeg({ quality: 85 })
    .toBuffer();

  const processedSizeBytes = processedBuffer.length;
  const base64String = processedBuffer.toString('base64');
  const base64SizeBytes = Buffer.byteLength(base64String, 'utf-8');

  console.error('\n--- Image Optimization Stats ---');
  console.error(`Original Image Size:  ${(originalSizeBytes / 1024).toFixed(2)} KB (${originalSizeBytes} bytes)`);
  console.error(`Processed JPEG Size:  ${(processedSizeBytes / 1024).toFixed(2)} KB (${processedSizeBytes} bytes)`);
  console.error(`Base64 String Size:   ${(base64SizeBytes / 1024).toFixed(2)} KB (${base64SizeBytes} bytes)`);
  console.error('--------------------------------\n');

  return base64String;
}

const lookupErrorTool: ChatCompletionTool = {
  type: 'function',
  function: {
    name: 'lookup_error',
    description: 'Searches the web for technical documentation, coding errors, and recent library details to help debug issues.',
    parameters: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The search query based on error messages, version numbers, or stack trace details from the screenshot.',
        },
      },
      required: ['query'],
    },
  },
};

const SYSTEM_PROMPT = `
You are an expert full-stack visual debugging assistant ("img-debug").
Your task is to analyze developer screenshots containing terminal errors, stack traces, CSS misalignments, or IDE exceptions, and provide precise fixes.

Follow these strict guidelines:
1. Describe: Identify what is visible in the image (error names, exact line numbers, file names, frameworks, or UI defects).
2. Verify: If the error involves specific software versions, recent syntax changes, or unknown errors, MUST call the \`lookup_error\` tool to retrieve current official documentation.
3. Analyze: Explain the root cause clearly, incorporating information found via \`lookup_error\`. Always cite web search sources if used.
4. Fix: Provide concrete solutions including code snippets, shell commands, or configuration changes.
5. Non-technical Images: If the image is unrelated to software development or technical errors (e.g., animals, landscapes), politely decline to debug and explain that you can only process developer error screenshots.
`.trim();

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: npx tsx img-debug.ts <path-to-screenshot> [optional user prompt]');
    process.exit(1);
  }

  const imagePath = args[0];
  const userTextPrompt = args[1] || 'Please analyze this screenshot, find any errors, and tell me how to fix them.';

  try {
    const base64Image = await processImage(imagePath);
    const dataUrl = `data:image/jpeg;base64,${base64Image}`;
    const messages: ChatCompletionMessageParam[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      {
        role: 'user',
        content: [
          { type: 'text', text: userTextPrompt },
          { type: 'image_url', image_url: { url: dataUrl } },
        ],
      },
    ];

    const maxIterations = 5;
    let iteration = 0;

    console.log('Analyzing screenshot...');

    while (iteration < maxIterations) {
      iteration++;

      const response = await openai.chat.completions.create({
        model: 'google/gemini-2.5-flash', 
        messages,
        tools: [lookupErrorTool],
        tool_choice: 'auto',
      });

      const responseMessage = response.choices[0].message;
      messages.push(responseMessage);

      if (responseMessage.tool_calls && responseMessage.tool_calls.length > 0) {
        for (const toolCall of responseMessage.tool_calls) {
          if (toolCall.type === 'function' && toolCall.function.name === 'lookup_error') {
            const args = JSON.parse(toolCall.function.arguments);
            const searchQuery = args.query;

            console.log(`[Tool Execution] Executing search for: "${searchQuery}"...`);

            let searchResultsText = '';
            try {
              const searchResponse = await tvly.search(searchQuery, {
                maxResults: 3,
                searchDepth: 'advanced',
              });

              searchResultsText = searchResponse.results
                .map((res: { title: string; url: string; content: string }) => `Title: ${res.title}\nURL: ${res.url}\nContent: ${res.content}`)
                .join('\n\n');
            } catch (err: any) {
              searchResultsText = `Search failed: ${err.message || String(err)}`;
            }

            messages.push({
              role: 'tool',
              tool_call_id: toolCall.id,
              content: searchResultsText,
            });
          }
        }
      } else {
        console.log('\n=== Final Debugger Output ===\n');
        console.log(responseMessage.content);
        break;
      }
    }
  } catch (error: any) {
    console.error('Error running img-debug:', error.message || error);
  }
}

main();