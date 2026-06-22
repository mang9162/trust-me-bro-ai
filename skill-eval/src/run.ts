import type { Config } from "./config.ts";
import type { EvalCase, EvalResult, ExpectationVerdict, RunStatus } from "./types.ts";
import { buildSkillContext, type SkillContext } from "./context.ts";
import { runActor } from "./actor.ts";
import { runJudge } from "./judge.ts";

async function pool<T, R>(items: T[], limit: number, fn: (t: T) => Promise<R>): Promise<R[]> {
  const ret = new Array<R>(items.length);
  let next = 0;
  const workers = Array.from({ length: Math.max(1, Math.min(limit, items.length)) }, async () => {
    while (true) {
      const i = next++;
      if (i >= items.length) break;
      ret[i] = await fn(items[i]);
    }
  });
  await Promise.all(workers);
  return ret;
}

export async function runAll(
  cfg: Config,
  cases: EvalCase[],
  skillMap: Map<string, string>,
  onProgress?: (done: number, total: number) => void
): Promise<EvalResult[]> {
  const ctxCache = new Map<string, Promise<SkillContext>>();
  const getCtx = (skillName: string): Promise<SkillContext> => {
    let p = ctxCache.get(skillName);
    if (!p) {
      const skillPath = skillMap.get(skillName);
      p = skillPath
        ? buildSkillContext(skillName, skillPath, cfg.root)
        : Promise.reject(new Error(`SKILL.md not found for skill "${skillName}"`));
      ctxCache.set(skillName, p);
    }
    return p;
  };

  let done = 0;
  return pool(cases, cfg.concurrency, async (ev) => {
    const start = Date.now();
    try {
      const ctx = await getCtx(ev.skillName);
      const actorResponse = await runActor(cfg.actorModel, ctx.system, ev);
      const judged = await runJudge(cfg.judgeModel, ev, actorResponse);
      const verdicts: ExpectationVerdict[] = ev.expectations.map((e, i) => {
        const r = judged.find((x) => x.index === i);
        return { index: i, expectation: e, pass: r?.pass ?? false, reason: r?.reason ?? "(no verdict returned)" };
      });
      const status: RunStatus = verdicts.length > 0 && verdicts.every((v) => v.pass) ? "pass" : "fail";
      return { eval: ev, actorResponse, verdicts, status, ms: Date.now() - start };
    } catch (err) {
      return {
        eval: ev,
        actorResponse: "",
        verdicts: [],
        status: "errored" as RunStatus,
        error: err instanceof Error ? err.message : String(err),
        ms: Date.now() - start,
      };
    } finally {
      onProgress?.(++done, cases.length);
    }
  });
}
