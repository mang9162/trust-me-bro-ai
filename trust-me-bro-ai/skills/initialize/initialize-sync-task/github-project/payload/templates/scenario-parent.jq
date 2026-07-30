# scenario-parent.jq — body ของ parent issue (สาย scenario)
# input: scenario-meta JSON · --arg scenario <full scenario name>
(.description // "")
+ "\n\n## Steps\n"
+ ((.steps // []) | to_entries | map("\(.key+1). \(.value | if type=="string" then . else tojson end)") | join("\n"))
+ "\n\n**accepted:** \(.accepted // false)\n"
+ ((.acceptanceHistory // []) | if length>0 then
    "\n<details><summary>acceptance history</summary>\n\n"
    + (map("**round \(.round)** — \(.result)\n\n\(.feedback)") | join("\n\n"))
    + "\n</details>\n" else "" end)
+ "\n---\n_Synced from Trust me bro ai · " + $scenario + "_"
