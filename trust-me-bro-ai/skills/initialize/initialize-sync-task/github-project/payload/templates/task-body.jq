# task-body.jq — body ของ sub-issue (task) ที่ sync ขึ้น GitHub
# แก้ได้ตามใจ: จัด/เพิ่ม/ตัด section ได้เลย เป็น jq ธรรมดา
# input: task JSON · --arg rel <source path> · --arg scenario <full scenario/topic name>

# ---------- helpers ----------
def trim: sub("^\\s+";"") | sub("\\s+$";"");
# ภาษา: เดาจากนามสกุลไฟล์ target ตัวแรก
def firstpath: (.targets // []) | if length>0 then (.[0] | if type=="object" then .path else . end) else "" end;
def lang: firstpath | ascii_downcase
  | if   test("\\.bru$")       then "Bruno / HTTP"
    elif test("\\.spec\\.ts$") then "TypeScript"
    elif test("\\.ts$")        then "TypeScript"
    elif test("\\.js$")        then "JavaScript"
    elif test("\\.py$")        then "Python"
    elif test("\\.go$")        then "Go"
    elif test("\\.java$")      then "Java"
    else null end;
# acceptance (คั่นด้วย ";") + api-test asserts → รายการ checklist
def criteria:
  ((.acceptance // "") | if . == "" then [] else (split(";") | map(trim) | map(select(length>0))) end)
  + (.asserts // []);

# ==================== ## Contract ====================
# หัวกระดาษที่ต้องรู้: task แบบไหน ทำทำไม
"## Contract\n\n"
+ "- **id:** \(.id // "?")\n"
+ "- **type:** \(.type // "?")\n"
+ "- **status:** \(.status // "pending")\n"
+ (if .effort then "- **effort:** \(.effort)\n" else "" end)
+ ((.purpose // .context) as $p | if $p then "- **purpose:** \($p)\n" else "" end)
+ (lang as $l | if $l then "- **language:** \($l)\n" else "" end)
+ ((.targets // []) | if length>0 then "- **targets:**\n"
    + (map(if type=="object"
             then "    - `\(.path)`" + (if .mode then " — \(.mode)" else "" end) + (if .at then " — \(.at)" else "" end)
             else "    - `\(.)`" end) | join("\n")) + "\n"
   else "" end)
+ ((.depends_on // []) | if length>0 then "- **depends_on:** " + join(", ") + "\n" else "" end)
+ ((.pseudocode // []) | if length>0 then "\n**pseudocode**\n```\n" + join("\n") + "\n```\n" else "" end)
+ (if .contract then "\n**contract**\n```\n" + (if (.contract|type)=="string" then .contract else (.contract|tojson) end) + "\n```\n" else "" end)
+ (if .cases then "\n**cases**\n```json\n" + (.cases|tojson) + "\n```\n" else "" end)
+ (if .uses  then "\n**uses**\n```json\n"  + (.uses|tojson)  + "\n```\n" else "" end)

# =============== ## Acceptance criteria ===============
+ "\n## Acceptance criteria\n\n"
+ (criteria | if length>0 then (map("- [ ] " + .) | join("\n")) + "\n" else "- [ ] —\n" end)

# ================== ## How to test ==================
+ (if .command then "\n## How to test\n\n```\n" + .command + "\n```\n" else "" end)

# ===================== ## Notes =====================
# summary ($summary — AI สรุปตอน sync แล้วส่งเข้ามา, ไม่เก็บใน task) อยู่บน · raw notes พับใน <details>
+ (if (.notes // "") == "" then "" else
    "\n## Notes\n\n"
    + (($summary // "") | if . != "" then . + "\n\n" else "" end)
    + "<details><summary>raw notes</summary>\n\n" + .notes + "\n</details>\n"
  end)

# ==================== footer ====================
+ "\n---\n_Synced from Trust me bro ai · " + $scenario + "_"
