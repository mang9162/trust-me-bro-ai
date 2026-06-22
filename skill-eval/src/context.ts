import fg from "fast-glob";
import { readFile } from "node:fs/promises";
import path from "node:path";

const IGNORE = ["**/node_modules/**", "**/.git/**"];

export interface SkillContext {
  skillName: string;
  system: string;
  inlinedRefs: string[];
  missingRefs: string[];
  triggerSkills: string[];
}

/**
 * Build the actor's system context (level B, references 1 level deep):
 *   SKILL.md + content refs from its `## References` inlined (with *-format.md
 *   fallback when the target file isn't generated in the kit). Trigger skills
 *   are named only — their bodies are intentionally omitted.
 */
export async function buildSkillContext(
  skillName: string,
  skillPath: string,
  root: string
): Promise<SkillContext> {
  const skillMd = await readFile(skillPath, "utf8");
  const skillDir = path.dirname(skillPath);
  const skillsRoot = findSkillsRoot(skillDir);
  const bases = [root, skillsRoot, skillDir];

  const refSection = extractSection(skillMd, /References/i) ?? "";
  const triggerSection = extractSection(skillMd, /Trigger Skill/i) ?? "";
  const refTokens = backtickMdTokens(refSection);
  const triggerSkills = triggerNames(triggerSection);

  const inlinedRefs: string[] = [];
  const missingRefs: string[] = [];
  const refBlocks: string[] = [];
  const seen = new Set<string>([skillPath]);

  for (const token of refTokens) {
    let files = await resolveToken(token, bases);
    let fallback = false;
    if (!files.length) {
      files = await fallbackFormat(token, skillsRoot);
      fallback = files.length > 0;
    }
    if (!files.length) {
      missingRefs.push(token);
      continue;
    }
    for (const f of files) {
      if (seen.has(f)) continue;
      seen.add(f);
      const rel = path.relative(root, f);
      refBlocks.push(
        `### REFERENCED FILE: ${rel}${fallback ? `  (format fallback for \`${token}\`)` : ""}\n\n${(await readFile(f, "utf8")).trim()}`
      );
      inlinedRefs.push(rel);
    }
  }

  let system = `# SKILL UNDER TEST: ${skillName}\n\n${skillMd.trim()}`;
  if (refBlocks.length) {
    system += `\n\n---\n# REFERENCED FILES (inlined, 1 level deep)\n\n${refBlocks.join("\n\n---\n\n")}`;
  }
  if (triggerSkills.length) {
    system += `\n\n---\n# TRIGGER SKILLS (available by name; bodies intentionally omitted): ${triggerSkills.join(", ")}`;
  }

  return { skillName, system, inlinedRefs, missingRefs, triggerSkills };
}

function extractSection(md: string, heading: RegExp): string | null {
  const lines = md.split("\n");
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (/^##\s/.test(lines[i]) && heading.test(lines[i])) {
      start = i + 1;
      break;
    }
  }
  if (start === -1) return null;
  const out: string[] = [];
  for (let i = start; i < lines.length; i++) {
    if (/^##\s/.test(lines[i])) break;
    out.push(lines[i]);
  }
  return out.join("\n");
}

function backtickMdTokens(section: string): string[] {
  const tokens: string[] = [];
  const re = /`([^`]+\.md[^`]*)`/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(section))) tokens.push(m[1].trim());
  return [...new Set(tokens)];
}

function triggerNames(section: string): string[] {
  const names: string[] = [];
  for (const line of section.split("\n")) {
    const m = line.match(/^\s*-\s*([a-z0-9-]+)\b/i);
    if (m) names.push(m[1]);
  }
  return [...new Set(names)];
}

function findSkillsRoot(skillDir: string): string {
  let d = skillDir;
  while (d !== path.dirname(d)) {
    if (path.basename(d) === "skills") return d;
    d = path.dirname(d);
  }
  return skillDir;
}

async function resolveToken(token: string, bases: string[]): Promise<string[]> {
  for (const base of bases) {
    try {
      const matches = await fg(token, { cwd: base, absolute: true, onlyFiles: true, ignore: IGNORE });
      if (matches.length) return matches;
    } catch {
      /* token not a valid glob relative to this base — try next */
    }
  }
  return [];
}

/** When a content ref points at a not-yet-generated target (e.g. context/data.md),
 *  fall back to the *-format.md whose `Target:` line names that path. */
async function fallbackFormat(token: string, skillsRoot: string): Promise<string[]> {
  const tail = token.replace(/^trust-me-bro-ai\//, "").replace(/^\.\//, "");
  if (tail.includes("*")) return [];
  const formats = await fg("**/*-format.md", { cwd: skillsRoot, absolute: true, ignore: IGNORE });
  const hits: string[] = [];
  for (const f of formats) {
    if ((await readFile(f, "utf8")).includes("Target: `" + tail + "`")) hits.push(f);
  }
  return hits;
}
