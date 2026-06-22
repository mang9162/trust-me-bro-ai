import fg from "fast-glob";
import { readFile } from "node:fs/promises";

const IGNORE = ["**/node_modules/**", "**/.git/**"];

/** Map a skill's frontmatter `name:` → its SKILL.md path (handles nested skills). */
export async function buildSkillMap(root: string): Promise<Map<string, string>> {
  const files = await fg("**/SKILL.md", { cwd: root, absolute: true, ignore: IGNORE });
  const map = new Map<string, string>();
  for (const f of files) {
    const name = parseFrontmatterName(await readFile(f, "utf8"));
    if (name && !map.has(name)) map.set(name, f);
  }
  return map;
}

function parseFrontmatterName(md: string): string | null {
  const fm = md.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) return null;
  const nm = fm[1].match(/^name:\s*(.+)$/m);
  return nm ? nm[1].trim() : null;
}
