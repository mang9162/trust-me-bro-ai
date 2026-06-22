# skill-eval

LLM-as-judge runner for the kit's `skill-evaluation` scenarios. It drives both the actor and the judge through the **Claude Code CLI (`claude -p`)**, so it uses your existing Claude Code login — **no `ANTHROPIC_API_KEY` required**.

- **actor** — `claude -p` (default `claude-opus-4-8`, `--effort high`) with the target skill's `SKILL.md` + its 1-level `## References` injected as the system prompt (content refs inlined, trigger skills named only). Tools are disallowed and it runs in a throwaway cwd, so it describes what it would do without touching anything.
- **judge** — `claude -p` (default `claude-sonnet-4-6`, `--effort low`) scores each `expectation` independently, returning JSON. An eval passes only if **all** its expectations pass.
- output — a self-contained `out/report.html` (open it directly; toggle "show failures only").

This is **dev tooling**, not kit runtime. It lives outside `skills/` and is meant to be run by the kit maintainer. It is excluded from a lean runtime install of the kit. (Re-running in CI, or `npx` for other projects, is a later step — would swap the engine back to the SDK or a headless token.)

## Prerequisites
- Claude Code installed and logged in (`claude` on PATH). Check: `claude --version`.

## Run

```bash
cd skill-eval
npm install
npm run eval          # initialize only (scans ../ for SKILL.md + scenario-*.json)
npm run eval:all      # every skill's scenarios
```

### Flags
```
tsx src/index.ts --root ..            # repo root to scan (default: cwd)
  --skill initialize                  # only this skill_name
  --scenario scenario-05              # only matching scenario files
  --actor-model / --judge-model       # override models
  --concurrency 3                     # parallel evals (each spawns 2 claude -p)
  --out out/report.html
```

Exit code is non-zero if any eval fails or errors.

## Notes
- Scenario shapes handled: behavioral (with `conversation_history`) and `skill-edit`.
- A content ref pointing at a not-yet-generated target (e.g. `context/data.md`) falls back to the `*-format.md` whose `Target:` names it.
- Cost is billed against your Claude Code plan (each `claude -p` call has ~12k tokens of base CLI context).
- Known limitation: global Claude Code auto-memory/settings may still load into the actor (the repo's own `CLAUDE.md` is avoided via a temp cwd, but `--bare` isn't usable since it forces API-key auth).
