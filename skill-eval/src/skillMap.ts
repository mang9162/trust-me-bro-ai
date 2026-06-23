import fg from "fast-glob";
import { readFile } from "node:fs/promises";
import path from "node:path";

const IGNORE = ["**/node_modules/**", "**/.git/**"];

/**
 * Map a skill's name → the file that defines it:
 *  - a SKILL.md by its frontmatter `name:` (handles nested skills);
 *  - a `<name>-format.md` by `<name>` — format-template "skills" that have no
 *    SKILL.md (e.g. error-codes, database-schema). SKILL.md wins on a name clash.
 */
export async function buildSkillMap(root: string): Promise<Map<string, string>> {
  const map = new Map<string, string>();

  const skillFiles = await fg("**/SKILL.md", { cwd: root, absolute: true, ignore: IGNORE });
  for (const f of skillFiles) {
    const name = parseFrontmatterName(await readFile(f, "utf8"));
    if (name && !map.has(name)) map.set(name, f);
  }

  const formatFiles = await fg("**/*-format.md", { cwd: root, absolute: true, ignore: IGNORE });
  for (const f of formatFiles) {
    const name = path.basename(f).replace(/-format\.md$/, "");
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
