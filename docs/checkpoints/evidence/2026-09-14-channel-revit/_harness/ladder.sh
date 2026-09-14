#!/bin/sh
S="C:/Users/twitc/AppData/Local/Temp/claude/C--Users-twitc-Desktop-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton/62996b12-9314-442c-9f86-45843276ca9c/scratchpad"
cd "$S"
for n in "$@"; do
  ids=$(py -3 -c "import json;print(json.dumps(json.load(open('ladder_ids.json'))['$n']))")
  echo "{\"ids\":$ids,\"strategy\":\"CHANNEL\",\"create\":true,\"purge_bench\":true,\"level_pe_cm\":272.0,\"out\":\"r_ladder_$n.json\"}" > r_cfg.json
  echo "=== START ladder $n $(date +%H:%M:%S)"
  sh run.sh r_channel.py
  py -3 summarize.py r_ladder_$n.json
  echo "=== END ladder $n $(date +%H:%M:%S)"
done
