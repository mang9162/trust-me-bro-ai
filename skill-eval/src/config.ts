export interface Config {
  /** Repo root to scan for SKILL.md + scenario-*.json. */
  root: string;
  actorModel: string;
  judgeModel: string;
  concurrency: number;
  outPath: string;
  skillFilter?: string;
  scenarioFilter?: string;
}

export const DEFAULTS = {
  // Actor plays the skill faithfully → most capable model.
  actorModel: "claude-opus-4-6",
  // Judge is a constrained scoring task → cheaper model is fine.
  judgeModel: "claude-sonnet-4-6",
  // Each eval spawns 2 `claude -p` subprocesses; keep this modest.
  concurrency: 2,
  outPath: "out/report.html",
};
