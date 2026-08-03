# scenario-parent.jq — rich parent-issue body for a scenario (edit the layout freely)
# input: scenario-meta JSON
# args (the engine gathers these): --arg scenario --arg repo --arg feature
#       --arg testdata (Datatest.md content) --argjson counts ({byType,mocks}) --arg fndesign (text)

# ---- header: a plain list ----
"- **Repo:** `\($repo)`\n"
+ (if ($feature // "") != "" then "- **Feature:** \($feature)\n" else "" end)
+ "- **Category:** \(.category // "?")\n"
+ (if (.description // "") != "" then "\n" + .description + "\n" else "" end)

# ---- E2E flow: a mermaid flowchart (GitHub renders it in the issue) ----
# step text is sanitized so mermaid doesn't choke on " [ ] { } | < > ` newlines
+ "\n## E2E Flow\n\n```mermaid\nflowchart TD\n"
+ ((.steps // []) | to_entries | map("  S\(.key)[\""
    + ((.key+1|tostring) + ". " + (.value | if type=="string" then . else tojson end)
       | gsub("[\\[\\]{}|<>]"; " ") | gsub("\"";"'") | gsub("`";"'") | gsub("\n";" "))
    + "\"]") | join("\n"))
+ "\n  " + ((.steps // []) | to_entries | map("S\(.key)") | join(" --> "))
+ "\n```\n"

# ---- test data: the Datatest.md tables, as-is ----
+ (if ($testdata // "") != "" then "\n## Test Data\n\n" + $testdata + "\n" else "" end)

# ---- functional design: text tree in a code block (best-effort) ----
+ (if ($fndesign // "") != "" then "\n## Functional Design\n\n```\n" + $fndesign + "\n```\n" else "" end)

# ---- flow summary: counts as a plain list ----
+ "\n## Flow Summary\n\n"
+ "**Tasks:**\n\n" + (($counts.byType // {}) | to_entries | map("- \(.key) ×\(.value)") | join("\n")) + "\n\n"
+ "**Mocks (stubs):** ×\($counts.mocks // 0)\n"

# ---- acceptance: one AI summary line per round ($summary keyed by round), raw rounds collapsed ----
+ "\n**accepted:** \(.accepted // false)\n"
+ ((.acceptanceHistory // []) | if length>0 then
    "\n" + (map("- **Round \(.round)** (\(.result))"
      + (((($summary // {})[(.round|tostring)]) // "") | if . != "" then " — " + . else "" end)
      ) | join("\n")) + "\n"
    + "\n<details><summary>acceptance history (raw)</summary>\n\n"
    + (map("**round \(.round)** — \(.result)\n\n\(.feedback)") | join("\n\n"))
    + "\n</details>\n" else "" end)

# ---- footer ----
+ "\n---\n_Synced from Trust me bro ai · " + $scenario + "_"
