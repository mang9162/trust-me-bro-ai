import { callClaude } from "./claude.ts";
import type { EvalCase } from "./types.ts";

export interface JudgeResult {
  index: number;
  pass: boolean;
  reason: string;
}

const JUDGE_SYSTEM = `You are a strict, precise evaluator of AI-skill behavior tests. 
  Judge each expectation independently against the assistant's behavior. Missing, 
  contradicted, or vague-with-no-specifics satisfaction is a FAIL — don't give the benefit of the doubt.

Two rules specific to this harness:
1. The assistant has no live repo or tools, so it DESCRIBES its actions in text. 
  Treat a clear, specific description of doing X — including the concrete file path and the content/structure 
  it writes — as satisfying an expectation phrased as "AI does/writes/creates/triggers X". 
  (A bare claim like "updated the file" with no specifics does NOT satisfy a "writes X with content Y" expectation.)
2. You are given the assistant's earlier turns in this session AND its latest turn. 
  An expectation PASSES if it is satisfied anywhere in the assistant's own behavior across the session — 
  earlier turns or the latest one.

Output ONLY a JSON object of this exact shape, with one entry per expectation and nothing else (no prose, no code fences):
{"results":[{"index":<int>,"pass":<true|false>,"reason":"<one short sentence>"}]}`;

export async function runJudge(model: string, ev: EvalCase, actorResponse: string): Promise<JudgeResult[]> {
  const convo = ev.messages.map((m) => `[${m.role}]\n${m.content}`).join("\n\n");
  const exp = ev.expectations.map((e, i) => `${i}. ${e}`).join("\n");
  const userPrompt =
    `SKILL UNDER TEST: ${ev.skillName}\nMODE: ${ev.mode}\n\n` +
    `=== ASSISTANT'S SESSION SO FAR (its own earlier turns; the last entry is the user message it is now responding to) ===\n${convo}\n\n` +
    `=== ASSISTANT'S LATEST TURN (newly produced — judge this together with the session above) ===\n${actorResponse || "(empty response)"}\n\n` +
    `=== EXPECTED OUTPUT (guidance only) ===\n${ev.expectedOutput ?? "(none)"}\n\n` +
    `=== EXPECTATIONS (judge each by index) ===\n${exp}\n\n` +
    `Return exactly ${ev.expectations.length} results, indices 0..${ev.expectations.length - 1}.`;

  const out = await callClaude({
    systemPrompt: JUDGE_SYSTEM,
    userPrompt,
    model,
    effort: "low",
    disallowedTools: ["Edit", "Write", "Bash", "Read", "Glob", "Grep", "WebSearch", "WebFetch", "Task"],
  });

  const parsed = JSON.parse(extractJson(out)) as { results?: JudgeResult[] };
  return parsed.results ?? [];
}

function extractJson(s: string): string {
  const fenced = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenced) return fenced[1].trim();
  const i = s.indexOf("{");
  const j = s.lastIndexOf("}");
  return i >= 0 && j > i ? s.slice(i, j + 1) : s.trim();
}
