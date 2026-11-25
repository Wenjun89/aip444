/**
 * AIP444 Lab 9: Source Credibility Analyzer Agent
 * Author: Wenjun Wei
 * Student ID: 169010238
 * Program: Computer Programming and Analysis
 * Description: An autonomous source credibility evaluation CLI agent built with
 *              Node.js, TypeScript, and @openai/agents via OpenRouter. It retrieves
 *              web pages with Jina Reader, conducts cross-verification searches
 *              via the Tavily Search API, enforces structured six-dimension
 *              credibility assessments validated with Zod, saves Markdown reports,
 *              and records full execution traces to JSON.
 */

import "dotenv/config";
import fs from "node:fs/promises";
import path from "node:path";
import OpenAI from "openai";
import {
  Agent,
  Runner,
  tool,
  setDefaultOpenAIClient,
  setOpenAIAPI,
  setTracingDisabled,
} from "@openai/agents";
import { z } from "zod";
import { tavily } from "@tavily/core";
import { CREDIBILITY_SYSTEM_PROMPT } from "./prompt.js";

const openrouterClient = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: "https://openrouter.ai/api/v1",
});

setDefaultOpenAIClient(openrouterClient);
setOpenAIAPI("chat_completions");
setTracingDisabled(true);

const tvly = tavily({ apiKey: process.env.TAVILY_API_KEY || "" });

const readUrlTool = tool({
  name: "read_url",
  description:
    "Fetch a web page via Jina Reader and return its content as Markdown.",
  parameters: z.object({
    url: z.string().url().describe("The target URL to fetch and read"),
  }),
  execute: async ({ url }) => {
    try {
      const res = await fetch(`https://r.jina.ai/${url}`, {
        headers: { Accept: "text/markdown" },
      });
      if (!res.ok) {
        return `Error fetching URL (${res.status} ${res.statusText}) for ${url}`;
      }
      const text = await res.text();
      return text.slice(0, 10000);
    } catch (err) {
      return `Failed to fetch ${url}: ${
        err instanceof Error ? err.message : String(err)
      }`;
    }
  },
});

const webSearchTool = tool({
  name: "web_search",
  description:
    "Search the web using Tavily to investigate authors, publications, claims, primary sources, or fact-checks.",
  parameters: z.object({
    query: z.string().min(1).describe("Targeted web search query"),
  }),
  execute: async ({ query }) => {
    try {
      const result = await tvly.search(query, { maxResults: 5 });
      return JSON.stringify(
        result.results.map((r) => ({
          title: r.title,
          url: r.url,
          content: r.content,
        })),
        null,
        2
      );
    } catch (err) {
      return `Search error for "${query}": ${
        err instanceof Error ? err.message : String(err)
      }`;
    }
  },
});

const credibilitySchema = z.object({
  source_url: z.string().describe("The URL being evaluated"),
  source_type: z
    .enum([
      "peer_reviewed_journal",
      "news_organization",
      "government_agency",
      "nonprofit_organization",
      "corporate_blog",
      "personal_blog",
      "social_media",
      "wiki",
      "unknown",
    ])
    .describe("Primary classification of the source"),
  author: z.object({
    name: z
      .string()
      .describe('Author name, or "Unknown" with explanation of what was checked'),
    credentials: z
      .string()
      .describe(
        "Qualifications/background found, or search attempts if unknown"
      ),
    credibility_assessment: z
      .string()
      .describe("Assessment of author reliability and impact on verdict"),
  }),
  publication: z.object({
    name: z
      .string()
      .describe("Publication or website name, or domain name if unrecognized"),
    reputation: z
      .string()
      .describe("Findings on publication reputation or search attempts"),
    editorial_process: z
      .enum(["peer_reviewed", "editor_reviewed", "self_published", "unknown"])
      .describe("Editorial oversight model"),
  }),
  content_analysis: z.object({
    claims_supported_by_evidence: z
      .boolean()
      .describe("Whether main claims are backed by evidence"),
    sources_cited: z
      .boolean()
      .describe("Whether the source cites references or primary sources"),
    corroborated_by_other_sources: z
      .boolean()
      .describe("Whether credible sources corroborate claims"),
    contradicted_by_other_sources: z
      .boolean()
      .describe("Whether credible sources contradict claims"),
    primary_vs_secondary: z
      .enum(["primary_source", "secondary_source", "tertiary_source"])
      .describe(
        "Whether the content acts as a primary, secondary, or tertiary source"
      ),
    funding_or_sponsorship: z
      .string()
      .describe("Any discovered funding, sponsorship, or conflicts"),
    date_published: z
      .string()
      .describe("Publication/update date and currency assessment"),
  }),
  transparency_score: z
    .number()
    .int()
    .min(1)
    .max(5)
    .describe(
      "1-5 score for transparency on authorship, methods, evidence, and funding"
    ),
  overall_credibility: z
    .enum(["high", "medium", "low", "very_low"])
    .describe("Overall credibility rating"),
  reasoning: z
    .string()
    .describe(
      "Detailed explanation grounded in evidence gathered during investigation"
    ),
});

const assessCredibilityTool = tool({
  name: "assess_credibility",
  description:
    "Structured reasoning tool to record a complete credibility evaluation before writing the final report.",
  parameters: credibilitySchema,
  execute: async (evaluation) => ({
    status: "evaluation_recorded",
    evaluation,
  }),
});

const saveReportTool = tool({
  name: "save_report",
  description:
    "Write the final Markdown credibility report to disk inside the reports/ directory.",
  parameters: z.object({
    filename: z
      .string()
      .describe("Output filename ending in .md, e.g. gov-report.md"),
    markdownContent: z.string().describe("Full Markdown report content"),
  }),
  execute: async ({ filename, markdownContent }) => {
    const safeName = path.basename(filename).endsWith(".md")
      ? path.basename(filename)
      : `${path.basename(filename)}.md`;
    const outPath = path.resolve("reports", safeName);
    await fs.mkdir(path.dirname(outPath), { recursive: true });
    await fs.writeFile(outPath, markdownContent, "utf-8");
    return `Saved report to ${outPath}`;
  },
});

async function main() {
  const targetUrl = process.argv[2];
  if (!targetUrl) {
    console.error("Usage: npx tsx src/index.ts <URL>");
    process.exit(1);
  }

  const modelName =
    process.env.OPENROUTER_MODEL || "deepseek/deepseek-v4.1-flash-1017";
  const agent = new Agent({
    name: "Source Credibility Analyzer",
    instructions: CREDIBILITY_SYSTEM_PROMPT,
    model: modelName,
    tools: [readUrlTool, webSearchTool, assessCredibilityTool, saveReportTool],
  });

  const runner = new Runner();
  await fs.mkdir("traces", { recursive: true });
  const traceFile = path.resolve("traces", `trace-${Date.now()}.json`);

  try {
    const result = await runner.run(
      agent,
      `Evaluate the credibility of this source and save the report: ${targetUrl}`,
      { maxTurns: 25 }
    );

    await fs.writeFile(
      traceFile,
      JSON.stringify(
        {
          targetUrl,
          model: modelName,
          finalOutput: result.finalOutput,
          history: result.history,
        },
        null,
        2
      ),
      "utf-8"
    );

    console.log("\n=== FINAL OUTPUT ===\n");
    console.log(result.finalOutput);
    console.log(`\nTrace saved to: ${traceFile}`);
  } catch (err: any) {
    if (err?.state) {
      await fs.writeFile(
        traceFile,
        JSON.stringify(
          {
            targetUrl,
            model: modelName,
            error: err.message,
            generatedItems: err.state._generatedItems,
          },
          null,
          2
        ),
        "utf-8"
      );
      console.error(`Partial trace saved to: ${traceFile}`);
    }
    throw err;
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});