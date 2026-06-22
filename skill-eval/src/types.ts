export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export type EvalMode = "behavioral" | "skill-edit";

/** One normalized eval case, regardless of the source scenario shape. */
export interface EvalCase {
  scenarioFile: string; // absolute path
  scenarioName: string; // basename without extension
  skillName: string;
  mode: EvalMode;
  id: string | number;
  label?: string;
  /** The conversation to feed the actor; the actor produces the next assistant turn. */
  messages: ChatMessage[];
  expectations: string[];
  expectedOutput?: string;
}

export interface ExpectationVerdict {
  index: number;
  expectation: string;
  pass: boolean;
  reason: string;
}

export type RunStatus = "pass" | "fail" | "errored";

export interface EvalResult {
  eval: EvalCase;
  actorResponse: string;
  verdicts: ExpectationVerdict[];
  status: RunStatus;
  error?: string;
  ms: number;
}
