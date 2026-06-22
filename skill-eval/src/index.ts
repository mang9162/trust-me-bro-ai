#!/usr/bin/env -S npx tsx
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { DEFAULTS, type Config } from "./config.ts";
import { claudeAvailable } from "./claude.ts";
import { buildSkillMap } from "./skillMap.ts";
import { discoverEvals } from "./discover.ts";
import { runAll } from "./run.ts";
import { renderHtml } from "./report.ts";

function parseArgs(argv: string[]): Config {
  const args = new Map<string, string>();
  for (let i = 0; i < argv.length; i++) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const nextIsFlag = argv[i + 1] === undefined || argv[i + 1].startsWith("--");
    args.set(key, nextIsFlag ? "true" : argv[++i]);
  }
  return {
    root: path.resolve(args.get("root") ?? process.cwd()),
    actorModel: args.get("actor-model") ?? DEFAULTS.actorModel,
    judgeModel: args.get("judge-model") ?? DEFAULTS.judgeModel,
    concurrency: Number(args.get("concurrency") ?? DEFAULTS.concurrency),
    outPath: path.resolve(args.get("out") ?? path.join(process.cwd(), DEFAULTS.outPath)),
    skillFilter: args.get("skill"),
    scenarioFilter: args.get("scenario"),
  };
}

async function main() {
  const cfg = parseArgs(process.argv.slice(2));

  if (!(await claudeAvailable())) {
    console.error("`claude` CLI not found on PATH. Install Claude Code and log in (it uses your Claude Code session, no API key needed).");
    process.exit(2);
  }

  const [skillMap, cases] = await Promise.all([
    buildSkillMap(cfg.root),
    discoverEvals(cfg.root, cfg.skillFilter, cfg.scenarioFilter),
  ]);

  if (!cases.length) {
    console.error(`No evals found under ${cfg.root} (skill=${cfg.skillFilter ?? "*"}, scenario=${cfg.scenarioFilter ?? "*"}).`);
    process.exit(1);
  }
  const skills = [...new Set(cases.map((c) => c.skillName))].join(", ");
  console.error(`Running ${cases.length} evals (skills: ${skills}) · actor=${cfg.actorModel} judge=${cfg.judgeModel} conc=${cfg.concurrency}`);

  const results = await runAll(cfg, cases, skillMap, (d, t) => process.stderr.write(`\r  ${d}/${t} done`));
  process.stderr.write("\n");

  await mkdir(path.dirname(cfg.outPath), { recursive: true });
  await writeFile(cfg.outPath, renderHtml(results, cfg), "utf8");

  const pass = results.filter((r) => r.status === "pass").length;
  const fail = results.filter((r) => r.status === "fail").length;
  const err = results.filter((r) => r.status === "errored").length;
  console.error(`\n${pass} pass · ${fail} fail · ${err} errored → ${path.relative(process.cwd(), cfg.outPath)}`);
  process.exit(fail + err ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
