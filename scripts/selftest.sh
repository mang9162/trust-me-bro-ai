#!/usr/bin/env bash
# selftest.sh — regression gauntlet for the kit's 5 python tools.
#
# Usage: scripts/selftest.sh        # run all tests, isolated temp dir
#        scripts/selftest.sh -v     # also echo output on passing checks
#
# Covers, per tool:
#   T1 generate-report  render --all / --check, idempotent re-render, missing
#                       scenario exits non-zero, --help exits 0
#   T2 init-kit         first run creates 9 targets, boilerplate stripped,
#                       re-run skips untouched, --dry-run writes nothing
#   T3 taskctl          scaffold defaults, validate, status transitions,
#                       issue lane defaults, negative specs (missing cases,
#                       id/type mismatch), deps deadlock detector, --help
#   T4 export-requests  --all emits one .requests.json per scenario with
#                       task_id + uses preserved
#   T5 self-report      add / dedup / list, header + ids preserved, --help
#
# Exit 0 only if every check passes. Never modifies the kit repo: init-kit
# runs against a copy of the payload, all other tools run on generated
# fixtures. Requires python3 only.
set -u

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAYLOAD="$KIT/trust-me-bro-ai"
PY="${PYTHON:-python3}"
VERBOSE=0
[ "${1:-}" = "-v" ] && VERBOSE=1

GR="$PAYLOAD/skills/generate-report/scripts/generate-report.py"
INIT="$PAYLOAD/skills/initialize/scripts/init-kit.py"
TASKCTL="$PAYLOAD/skills/maintenance/scripts/taskctl.py"
EXPORT="$PAYLOAD/skills/workflow/Stage-5/api-test/scripts/export-requests.py"
SELF="$PAYLOAD/skills/self-learn/self-report/scripts/self-report.py"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/kit-selftest.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

PASS=0
FAIL=0
FAILED=()

say() { printf '%s\n' "$*"; }

# run <cmd...> — captures stdout+stderr into $OUT and exit code into $RC
run() { OUT="$("$@" 2>&1)"; RC=$?; }

# check <name> <want_rc> — asserts $RC from the last run()
check() {
    if [ "$RC" -eq "$2" ]; then
        PASS=$((PASS + 1)); say "    PASS  $1"
        [ "$VERBOSE" = 1 ] && printf '%s\n' "$OUT" | sed 's/^/          /'
    else
        FAIL=$((FAIL + 1)); FAILED+=("$1")
        say "    FAIL  $1 (want rc=$2, got rc=$RC)"
        printf '%s\n' "$OUT" | sed 's/^/          /'
    fi
}

# contains <name> <pattern> — asserts $OUT matches the grep pattern
contains() {
    if printf '%s' "$OUT" | grep -q "$2"; then
        PASS=$((PASS + 1)); say "    PASS  $1"
    else
        FAIL=$((FAIL + 1)); FAILED+=("$1")
        say "    FAIL  $1 (output lacks \`$2')"
        printf '%s\n' "$OUT" | sed 's/^/          /'
    fi
}

# not_contains <name> <pattern> — asserts $OUT does NOT match
not_contains() {
    if printf '%s' "$OUT" | grep -q "$2"; then
        FAIL=$((FAIL + 1)); FAILED+=("$1")
        say "    FAIL  $1 (output unexpectedly contains \`$2')"
        printf '%s\n' "$OUT" | sed 's/^/          /'
    else
        PASS=$((PASS + 1)); say "    PASS  $1"
    fi
}

# file_exists <name> <path>
file_exists() {
    if [ -f "$2" ]; then
        PASS=$((PASS + 1)); say "    PASS  $1"
    else
        FAIL=$((FAIL + 1)); FAILED+=("$1")
        say "    FAIL  $1 (missing: $2)"
    fi
}

# md5_of <file> — portable md5 via python3 (macOS/BSD `md5` vs GNU `md5sum`)
md5_of() {
    "$PY" -c "import sys,hashlib;print(hashlib.md5(open(sys.argv[1],'rb').read()).hexdigest())" "$1"
}

# pyassert <name> <expr> — runs a python3 -c check; expr may use `p` as the path
pyassert() {
    if "$PY" -c "import json,sys; $2" "$3" 2>/dev/null; then
        PASS=$((PASS + 1)); say "    PASS  $1"
    else
        FAIL=$((FAIL + 1)); FAILED+=("$1")
        say "    FAIL  $1 (assertion failed)"
    fi
}

# ---------------------------------------------------------------- fixtures

WORK="$TMP/work/Scenario/TEMPLATE_STATUS/Success/01-SELFTEST_DEMO"
mkdir -p "$WORK/01-Testdata" "$WORK/02-Task/02-Backlog" "$WORK/02-Task/03-Api-test"

cat > "$WORK/scenario.html" <<'EOF'
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>selftest</title></head>
<body>
<script id="scenario-meta" type="application/json">
{"scenario":"SELFTEST_DEMO","category":"Success","description":"selftest fixture scenario","steps":["Create template","Approve template"],"accepted":true,"acceptanceHistory":[{"round":1,"result":"accepted","feedback":"selftest round"}]}
</script>
</body></html>
EOF

cat > "$WORK/01-Testdata/Datatest.md" <<'EOF'
## Accounts
| accountId | name |
| --------- | ---- |
| 100000000000004 | selftest account |
EOF

cat > "$WORK/02-Task/02-Backlog/01-demo-code-task.json" <<'EOF'
{"id":"01-demo-code-task","type":"code-task","status":"done","title":"demo code","purpose":"selftest","targets":[{"path":"src/a.ts","mode":"create","at":"selftest"}],"depends_on":["00-env-setup"],"assume":"env ready","contract":"contract","command":"echo ok","acceptance":"runs","effort":"low"}
EOF

cat > "$WORK/02-Task/03-Api-test/01-demo-api-test.json" <<'EOF'
{"id":"01-demo-api-test","type":"api-test","status":"done","title":"demo api","purpose":"selftest","targets":[{"path":"api/demo.http","mode":"create","at":"selftest"}],"depends_on":["01-demo-code-task"],"assume":"done","contract":"contract-x","cases":[{"given":"g","assert":["200"]}],"uses":{"requests":[{"name":"get","refId":"100000000000004"}]},"command":"echo ok","acceptance":"ok","effort":"low"}
EOF

# -------------------------------------------------------------------- T1

say "T1 generate-report"
SCNROOT="$TMP/work/Scenario/TEMPLATE_STATUS"
run "$PY" "$GR" --all "$SCNROOT"
check "render --all exits 0" 0
contains "renders the scenario [ok]" '\[ok\]'
contains "names the rendered scenario" '01-SELFTEST_DEMO'
H1="$(md5_of "$WORK/scenario.html")"
run "$PY" "$GR" --all "$SCNROOT"
check "second render exits 0" 0
H2="$(md5_of "$WORK/scenario.html")"
if [ "$H1" = "$H2" ]; then
    PASS=$((PASS + 1)); say "    PASS  re-render is idempotent (md5 identical)"
else
    FAIL=$((FAIL + 1)); FAILED+=("re-render is idempotent (md5 identical)")
    say "    FAIL  re-render is idempotent (md5 identical)"
fi
run "$PY" "$GR" --check "$WORK"
check "--check exits 0" 0
run "$PY" "$GR" "$TMP/does-not-exist"
check "missing scenario exits non-zero" 1
run "$PY" "$GR" --help
check "--help exits 0" 0

# -------------------------------------------------------------------- T2

say "T2 init-kit"
cp -R "$PAYLOAD" "$TMP/kit"
run "$PY" "$INIT" "$TMP/kit"
check "first run exits 0" 0
if [ "$(printf '%s' "$OUT" | grep -c '^created')" -eq 9 ]; then
    PASS=$((PASS + 1)); say "    PASS  creates 9 targets"
else
    FAIL=$((FAIL + 1)); FAILED+=("creates 9 targets")
    say "    FAIL  creates 9 targets"
    printf '%s\n' "$OUT" | sed 's/^/          /'
fi
file_exists "context/data.md written" "$TMP/kit/context/data.md"
file_exists "tech-stack/tech-stack.md written" "$TMP/kit/tech-stack/tech-stack.md"
if grep -q 'Target:' "$TMP/kit/context/data.md" || grep -q 'How to scan' "$TMP/kit/context/data.md"; then
    FAIL=$((FAIL + 1)); FAILED+=("boilerplate stripped from targets")
    say "    FAIL  boilerplate stripped from targets"
else
    PASS=$((PASS + 1)); say "    PASS  boilerplate stripped from targets"
fi
M1="$(md5_of "$TMP/kit/context/data.md")"
run "$PY" "$INIT" "$TMP/kit"
check "re-run exits 0" 0
not_contains "re-run creates nothing" '^created'
M2="$(md5_of "$TMP/kit/context/data.md")"
if [ "$M1" = "$M2" ]; then
    PASS=$((PASS + 1)); say "    PASS  re-run leaves targets untouched"
else
    FAIL=$((FAIL + 1)); FAILED+=("re-run leaves targets untouched")
    say "    FAIL  re-run leaves targets untouched"
fi
cp -R "$PAYLOAD" "$TMP/kit2"
run "$PY" "$INIT" "$TMP/kit2" --dry-run
check "--dry-run exits 0" 0
contains "--dry-run reports intent" '(dry-run)'
if [ -f "$TMP/kit2/context/data.md" ] || [ -f "$TMP/kit2/tech-stack/tech-stack.md" ]; then
    FAIL=$((FAIL + 1)); FAILED+=("--dry-run writes no files")
    say "    FAIL  --dry-run writes no files"
else
    PASS=$((PASS + 1)); say "    PASS  --dry-run writes no files"
fi
run "$PY" "$INIT" --help
check "--help exits 0" 0

# -------------------------------------------------------------------- T3

say "T3 taskctl"
SPEC="$TMP/t3-spec.json"
cat > "$SPEC" <<'EOF'
{"id":"01-foo-unit-test","type":"unit-test","title":"selftest unit","purpose":"selftest","targets":[{"path":"src/foo.ts","mode":"create","at":"selftest"}],"contract":"contract","cases":[{"given":"g","assert":[]}],"pseudocode":"step 1","command":"echo ok","acceptance":"green"}
EOF
run "$PY" "$TASKCTL" scaffold "$SPEC" "$TMP/t3out"
check "scaffold exits 0" 0
file_exists "scaffold writes Backlog file" "$TMP/t3out/02-Backlog/01-foo-unit-test.json"
pyassert "scenario defaults (pending / 00-env-setup / low)" \
    "p='$TMP/t3out/02-Backlog/01-foo-unit-test.json'; t=json.load(open(p)); assert t['status']=='pending' and t['depends_on']==['00-env-setup'] and t['effort']=='low' and t['folder']=='02-Backlog'" \
    "$TMP/t3out/02-Backlog/01-foo-unit-test.json"
run "$PY" "$TASKCTL" validate "$TMP/t3out/02-Backlog/01-foo-unit-test.json"
check "validate ok" 0
run "$PY" "$TASKCTL" status "$TMP/t3out/02-Backlog/01-foo-unit-test.json" in_progress
check "pending -> in_progress ok" 0
pyassert "in_progress stamps startedAt" \
    "p='$TMP/t3out/02-Backlog/01-foo-unit-test.json'; t=json.load(open(p)); assert t.get('startedAt')" \
    "$TMP/t3out/02-Backlog/01-foo-unit-test.json"
run "$PY" "$TASKCTL" status "$TMP/t3out/02-Backlog/01-foo-unit-test.json" done
check "in_progress -> done ok" 0
pyassert "done stamps finishedAt" \
    "p='$TMP/t3out/02-Backlog/01-foo-unit-test.json'; t=json.load(open(p)); assert t.get('finishedAt')" \
    "$TMP/t3out/02-Backlog/01-foo-unit-test.json"
run "$PY" "$TASKCTL" status "$TMP/t3out/02-Backlog/01-foo-unit-test.json" done
check "done -> done rejected" 1
run "$PY" "$TASKCTL" scaffold "$SPEC" "$TMP/t3issue" --lane issue
check "issue-lane scaffold exits 0" 0
file_exists "issue lane writes Backlog file" "$TMP/t3issue/Backlog/01-foo-unit-test.json"
pyassert "issue-lane defaults (00-check-test baseline)" \
    "p='$TMP/t3issue/Backlog/01-foo-unit-test.json'; t=json.load(open(p)); assert t['depends_on']==['00-check-test'] and '00-check-test' in t['assume']" \
    "$TMP/t3issue/Backlog/01-foo-unit-test.json"
cat > "$TMP/t3-bad.json" <<'EOF'
{"id":"01-bar-unit-test","type":"unit-test","title":"bad","purpose":"selftest","targets":[{"path":"src/bar.ts","mode":"create","at":"selftest"}],"contract":"contract","command":"echo ok","acceptance":"green"}
EOF
run "$PY" "$TASKCTL" scaffold "$TMP/t3-bad.json" "$TMP/t3badout"
check "spec missing cases rejected" 1
contains "error names the missing field" 'cases'
cat > "$TMP/t3-id.json" <<'EOF'
{"id":"01-foo-modify","type":"interface","title":"id mismatch","purpose":"selftest","targets":[{"path":"api/x.ts","mode":"modify","at":"selftest"}],"contract":"contract"}
EOF
run "$PY" "$TASKCTL" scaffold "$TMP/t3-id.json" "$TMP/t3idout"
check "id/type mismatch rejected" 1
contains "error names the id rule" 'id does not match'
mkdir -p "$TMP/q"
cat > "$TMP/q/00-env-setup.json" <<'EOF'
{"id":"00-env-setup","status":"done"}
EOF
cat > "$TMP/q/01-a-unit-test.json" <<'EOF'
{"id":"01-a-unit-test","status":"pending","depends_on":["00-env-setup"]}
EOF
run "$PY" "$TASKCTL" deps "$TMP/q"
check "runnable queue ok" 0
contains "reports runnable queue" 'queue runnable'
"$PY" -c "import json; p='$TMP/q/01-a-unit-test.json'; t=json.load(open(p)); t['depends_on']=['00-missing']; json.dump(t, open(p,'w'))"
run "$PY" "$TASKCTL" deps "$TMP/q"
check "broken dependency flagged" 1
contains "names the missing dependency" 'missing'
run "$PY" "$TASKCTL" -h
check "-h exits 0" 0

# -------------------------------------------------------------------- T4

say "T4 export-requests"
run "$PY" "$EXPORT" --all "$SCNROOT" "$TMP/t4out"
check "export --all exits 0" 0
file_exists "emits requests file per scenario" "$TMP/t4out/01-SELFTEST_DEMO.requests.json"
pyassert "task_id + uses refId preserved" \
    "p='$TMP/t4out/01-SELFTEST_DEMO.requests.json'; d=json.load(open(p)); r=d['requests']; assert len(r)==1 and r[0]['task_id']=='01-demo-api-test' and r[0]['uses']['requests'][0]['refId']=='100000000000004'" \
    "$TMP/t4out/01-SELFTEST_DEMO.requests.json"
run "$PY" "$EXPORT" --help
check "--help exits 0" 0

# -------------------------------------------------------------------- T5

say "T5 self-report"
cp "$PAYLOAD/skills/self-learn/tech-debt.js" "$TMP/t5.js"
run "$PY" "$SELF" add "$TMP/t5.js" --kind issue --title "selftest entry" --problem "selftest unique problem 42" --places "a.ts,b.ts" --reported-by selftest
check "add first entry exits 0" 0
contains "reports added entry" 'added entry'
run "$PY" "$SELF" add "$TMP/t5.js" --kind issue --title "selftest second" --problem "selftest unique problem 43" --places "c.ts" --reported-by selftest
check "add second entry exits 0" 0
pyassert "two distinct entries, one occurrence each" \
    "p='$TMP/t5.js'; t=open(p).read(); import re,json; e=json.loads(re.search(r'var\s+TECH_DEBT\s*=\s*(\[.*?\])\s*;', t, re.S).group(1)); assert len(e)==2 and all(len(x.get('occurrences',[]))==1 for x in e)" \
    "$TMP/t5.js"
run "$PY" "$SELF" add "$TMP/t5.js" --kind issue --title "selftest entry" --problem "selftest unique problem 42" --places "a.ts" --reported-by selftest
check "duplicate add exits 0" 0
contains "dedup appends occurrence" 'appended occurrence'
pyassert "dedup keeps 2 entries, occurrence count 2" \
    "p='$TMP/t5.js'; t=open(p).read(); import re,json; e=json.loads(re.search(r'var\s+TECH_DEBT\s*=\s*(\[.*?\])\s*;', t, re.S).group(1)); assert len(e)==2 and e[0]['occurrences'] and len(e[0]['occurrences'])==2" \
    "$TMP/t5.js"
if head -n 1 "$TMP/t5.js" | grep -q '^var TECH_DEBT'; then
    PASS=$((PASS + 1)); say "    PASS  header preserved"
else
    FAIL=$((FAIL + 1)); FAILED+=("header preserved")
    say "    FAIL  header preserved"
fi
run "$PY" "$SELF" --help
check "--help exits 0" 0

# ------------------------------------------------------------------ result

say ""
say "result: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    say "failed: ${FAILED[*]}"
    exit 1
fi
exit 0
