import type { Config } from "./config.ts";
import type { EvalResult } from "./types.ts";

const esc = (s: string): string =>
  s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

export function renderHtml(results: EvalResult[], cfg: Config): string {
  const total = results.length;
  const pass = results.filter((r) => r.status === "pass").length;
  const fail = results.filter((r) => r.status === "fail").length;
  const errored = results.filter((r) => r.status === "errored").length;
  const pct = total ? Math.round((pass / total) * 100) : 0;

  const byFile = new Map<string, EvalResult[]>();
  for (const r of results) {
    const arr = byFile.get(r.eval.scenarioName) ?? [];
    if (!byFile.has(r.eval.scenarioName)) byFile.set(r.eval.scenarioName, arr);
    arr.push(r);
  }

  const sections = [...byFile.entries()]
    .map(([name, rs]) => {
      const p = rs.filter((r) => r.status === "pass").length;
      const allPass = rs.every((r) => r.status === "pass");
      return `<section class="file ${allPass ? "ok" : "bad"}">
  <h2>${esc(name)} <span class="rollup">${p}/${rs.length}</span> <span class="skill">${esc(rs[0]?.eval.skillName ?? "")}</span></h2>
  ${rs.map(card).join("\n")}
</section>`;
    })
    .join("\n");

  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill Eval Report</title>
<style>${CSS}</style></head>
<body>
<header>
  <h1>Skill Evaluation Report</h1>
  <div class="summary">
    <span class="badge pass">${pass} pass</span>
    <span class="badge fail">${fail} fail</span>
    <span class="badge err">${errored} errored</span>
    <span class="pct">${pct}% pass · ${total} total</span>
  </div>
  <div class="meta">actor <code>${esc(cfg.actorModel)}</code> · judge <code>${esc(cfg.judgeModel)}</code> · ${esc(new Date().toLocaleString())}</div>
  <label class="filter"><input type="checkbox" id="failsOnly"> show failures only</label>
</header>
<main>${sections}</main>
<script>
const cb=document.getElementById('failsOnly');
cb.addEventListener('change',()=>document.body.classList.toggle('fails-only',cb.checked));
</script>
</body></html>`;
}

function card(r: EvalResult): string {
  const badge =
    r.status === "pass"
      ? `<span class="badge pass">PASS</span>`
      : r.status === "errored"
        ? `<span class="badge err">ERROR</span>`
        : `<span class="badge fail">FAIL</span>`;
  const title = `${esc(String(r.eval.id))}${r.eval.label ? " · " + esc(r.eval.label) : ""}`;
  const lastUser = [...r.eval.messages].reverse().find((m) => m.role === "user");
  const prompt = lastUser ? `<div class="prompt"><b>prompt:</b> ${esc(lastUser.content)}</div>` : "";
  const errbox = r.error ? `<div class="errbox">${esc(r.error)}</div>` : "";
  const rows = r.verdicts
    .map(
      (v) =>
        `<tr class="${v.pass ? "vp" : "vf"}"><td>${v.pass ? "✓" : "✗"}</td><td>${esc(v.expectation)}</td><td>${esc(v.reason)}</td></tr>`
    )
    .join("");
  const table = r.verdicts.length
    ? `<table class="exp"><tr><th></th><th>expectation</th><th>reason</th></tr>${rows}</table>`
    : "";
  const resp = r.actorResponse
    ? `<details class="resp"><summary>actor response (${r.ms} ms)</summary><pre>${esc(r.actorResponse)}</pre></details>`
    : "";
  return `<article class="eval" data-status="${r.status}">
    <div class="ehead">${badge} <span class="etitle">${title}</span></div>
    ${prompt}${errbox}${table}${resp}
  </article>`;
}

const CSS = `
:root{--g:#1a7f37;--r:#cf222e;--y:#9a6700;--bg:#f6f8fa;--bd:#d0d7de}
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;color:#1f2328;background:#fff}
header{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--bd);padding:16px 24px;z-index:5}
h1{margin:0 0 8px;font-size:20px}
.summary{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.pct{color:#57606a}
.meta{color:#57606a;font-size:12px;margin-top:6px}
.meta code{background:var(--bg);padding:1px 5px;border-radius:4px}
.filter{display:inline-flex;gap:6px;align-items:center;margin-top:10px;font-size:13px;cursor:pointer}
main{padding:16px 24px;max-width:1100px}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;color:#fff}
.badge.pass{background:var(--g)}.badge.fail{background:var(--r)}.badge.err{background:var(--y)}
.file{margin:18px 0;border:1px solid var(--bd);border-radius:8px;overflow:hidden}
.file h2{margin:0;padding:10px 14px;font-size:15px;background:var(--bg);border-bottom:1px solid var(--bd)}
.file .rollup{color:#57606a;font-weight:400}
.file .skill{float:right;color:#8c959f;font-weight:400;font-size:12px}
.eval{padding:12px 14px;border-bottom:1px solid #eaeef2}
.eval:last-child{border-bottom:0}
.ehead{display:flex;gap:8px;align-items:center}
.etitle{font-weight:600}
.prompt{margin:8px 0;color:#444;background:var(--bg);padding:8px 10px;border-radius:6px;white-space:pre-wrap}
.errbox{margin:8px 0;color:var(--r);background:#fff0f0;padding:8px 10px;border-radius:6px;white-space:pre-wrap}
table.exp{width:100%;border-collapse:collapse;margin:8px 0;font-size:13px}
table.exp th{text-align:left;color:#57606a;font-weight:600;border-bottom:1px solid var(--bd);padding:4px 6px}
table.exp td{padding:4px 6px;border-bottom:1px solid #eaeef2;vertical-align:top}
table.exp td:first-child{width:18px;font-weight:700}
tr.vp td:first-child{color:var(--g)}tr.vf td:first-child{color:var(--r)}
tr.vf{background:#fff6f6}
.resp{margin-top:6px}
.resp summary{cursor:pointer;color:#57606a}
.resp pre{white-space:pre-wrap;background:var(--bg);padding:10px;border-radius:6px;overflow:auto;max-height:480px}
body.fails-only section.ok{display:none}
body.fails-only .eval[data-status="pass"]{display:none}
`;
