import fg from "fast-glob";
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { ChatMessage, EvalCase, EvalMode } from "./types.ts";

const IGNORE = ["**/node_modules/**", "**/.git/**"];

interface RawScenario {
  skill_name?: string;
  group?: string;
  evals?: RawEval[];
}
interface RawEval {
  id: string | number;
  label?: string;
  prompt?: string;
  /** scenario-03/04 style: [{ role, content }, ...] ending on a user turn. */
  conversation_history?: ChatMessage[];
  /** scenario-01/02/03 (bootstrap) style: [{ user }|{ ai }, ...] ending on an ai turn. */
  conversation?: Array<Record<string, string>>;
  expectations?: string[];
  expected_output?: string;
}

/** Find scenario-*.json under any skill-evaluation/ folder and normalize to EvalCase[]. */
export async function discoverEvals(
  root: string,
  skillFilter?: string,
  scenarioFilter?: string
): Promise<EvalCase[]> {
  const files = await fg("**/skill-evaluation/**/scenario-*.json", { cwd: root, absolute: true, ignore: IGNORE });

  const cases: EvalCase[] = [];
  for (const file of files.sort()) {
    const scenarioName = path.basename(file, ".json");
    if (scenarioFilter && !scenarioName.includes(scenarioFilter)) continue;

    let json: RawScenario;
    try {
      json = JSON.parse(await readFile(file, "utf8"));
    } catch {
      continue;
    }
    const skillName = json.skill_name;
    if (!skillName) continue;
    if (skillFilter && skillName !== skillFilter) continue;

    const mode: EvalMode = json.group === "skill-edit" ? "skill-edit" : "behavioral";
    for (const ev of json.evals ?? []) {
      cases.push({
        scenarioFile: file,
        scenarioName,
        skillName,
        mode,
        id: ev.id,
        label: ev.label,
        messages: normalizeMessages(ev, mode),
        expectations: ev.expectations ?? [],
        expectedOutput: ev.expected_output,
      });
    }
  }
  return cases;
}

/**
 * Build the conversation fed to the actor.
 * - skill-edit: just the prompt as a single user turn.
 * - behavioral: prefer conversation_history, else the {user}/{ai} `conversation`, else prompt.
 *   Then drop any trailing assistant turn(s) so the history ends on a user turn and the
 *   actor regenerates the next assistant turn (the one the expectations are about).
 */
function normalizeMessages(ev: RawEval, mode: EvalMode): ChatMessage[] {
  if (mode === "skill-edit") return [{ role: "user", content: ev.prompt ?? "" }];

  let msgs: ChatMessage[];
  if (ev.conversation_history?.length) {
    msgs = ev.conversation_history;
  } else if (ev.conversation?.length) {
    msgs = ev.conversation.map((turn) =>
      "user" in turn
        ? { role: "user" as const, content: turn.user }
        : { role: "assistant" as const, content: turn.ai }
    );
  } else {
    msgs = [{ role: "user", content: ev.prompt ?? "" }];
  }

  msgs = [...msgs];
  while (msgs.length && msgs[msgs.length - 1].role === "assistant") msgs.pop();
  return msgs;
}
