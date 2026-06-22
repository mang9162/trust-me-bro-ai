import { callClaude } from "./claude.ts";
import type { EvalCase, EvalMode } from "./types.ts";

const FRAMING: Record<EvalMode, string> = {
  behavioral: `You are an AI assistant in a live session with the skill above loaded; 
    you have already been doing the work shown in the conversation. 
    Produce ONLY the next assistant turn, following the skill's procedure, 
    ordering, pauses, and boundaries exactly. Act as if for real — but you have no live repo/tools, 
    so you SAY what you do: when the skill says to write or update a file, 
    state the exact target path AND the concrete content/structure you write (not just "I updated it"); 
    when it says to trigger another skill (e.g. self-report), 
    state that you trigger it and with what. Do not redo steps already completed earlier in the conversation, 
    and do not invent steps the skill does not specify.
    Do not apologize or provide conversational filler Start directly with the turn.`,
  "skill-edit": `The user is requesting a change to THIS skill's own behavior. 
  Decide, strictly per the skill's "Role & Boundary", whether the requested change is within this skill's scope. 
  If in scope: confirm it is allowed and state where/how it would change. 
  If out of scope: refuse, cite the Role & Boundary, 
  and point to where the change actually belongs. Do not perform the edit. Do not use tools.`,
};

export async function runActor(model: string, ctxSystem: string, ev: EvalCase): Promise<string> {
  const systemPrompt = `${ctxSystem}\n\n---\n# YOUR TASK\n${FRAMING[ev.mode]}`;
  return callClaude({
    systemPrompt,
    userPrompt: flatten(ev),
    model,
    effort: "high",
    disallowedTools: ["Edit", "Write", "Bash", "Read", "Glob", "Grep", "WebSearch", "WebFetch", "Task"],
  });
}

function flatten(ev: EvalCase): string {
  if (ev.mode === "skill-edit") {
    return ev.messages.map((m) => m.content).join("\n\n");
  }
  const convo = ev.messages.map((m) => `[${m.role}]\n${m.content}`).join("\n\n");
  return `Here is the conversation so far. Produce ONLY the next assistant turn (do not repeat prior turns).\n\n${convo}`;
}
