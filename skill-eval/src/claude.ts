import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

export type Effort = "low" | "medium" | "high" | "xhigh" | "max";

export interface ClaudeOpts {
  systemPrompt: string;
  userPrompt: string;
  model: string;
  effort: Effort;
  /** Tool names to deny (variadic, space-joined). */
  disallowedTools?: string[];
  bin?: string;
}

/**
 * Run one headless `claude -p` turn using the user's Claude Code login (no API key).
 * System prompt goes via a temp file; the user prompt is piped on stdin. Runs in a
 * throwaway cwd so the repo's CLAUDE.md / project context doesn't bleed into the actor.
 */
export async function callClaude(opts: ClaudeOpts): Promise<string> {
  const dir = await mkdtemp(path.join(tmpdir(), "skill-eval-"));
  const sysFile = path.join(dir, "system.txt");
  await writeFile(sysFile, opts.systemPrompt, "utf8");

  const args = [
    "-p",
    "--system-prompt-file", sysFile,
    "--model", opts.model,
    "--effort", opts.effort,
    "--output-format", "json",
  ];
  if (opts.disallowedTools?.length) {
    args.push("--disallowedTools", opts.disallowedTools.join(" "));
  }

  try {
    const stdout = await exec(opts.bin ?? "claude", args, opts.userPrompt, dir);
    const env = JSON.parse(stdout) as {
      result?: string;
      is_error?: boolean;
      api_error_status?: string | null;
    };
    if (env.is_error) {
      throw new Error(`claude error: ${env.api_error_status ?? "unknown"} — ${env.result ?? ""}`);
    }
    return (env.result ?? "").trim();
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

export async function claudeAvailable(bin = "claude"): Promise<boolean> {
  try {
    await exec(bin, ["--version"], "", process.cwd());
    return true;
  } catch {
    return false;
  }
}

function exec(bin: string, args: string[], stdin: string, cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const p = spawn(bin, args, { cwd, stdio: ["pipe", "pipe", "pipe"] });
    let out = "";
    let err = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (err += d));
    p.on("error", reject);
    p.on("close", (code) => {
      if (code === 0) resolve(out);
      else reject(new Error(`claude exited ${code}: ${(err || out).trim().slice(0, 500)}`));
    });
    p.stdin.write(stdin);
    p.stdin.end();
  });
}
