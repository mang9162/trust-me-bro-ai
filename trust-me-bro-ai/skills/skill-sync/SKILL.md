---
name: skill-sync
description: Sync shared skills index to .agents/skills/index and ~/.claude/skills/index. Use this whenever a new skill is added to or removed from docs/ai/shared/.
---

# Skill Sync

Scan `docs/ai/shared/` and regenerate the index for both agents.

## Steps

1. Run `scripts/sync.sh` from the repo root
2. Each teammate runs sync once after pulling new skills (to update ~/.claude/skills/index/)

## Notes
- No symlinks needed — agents read skills directly from docs/ai/shared/
- Safe to run multiple times (idempotent)