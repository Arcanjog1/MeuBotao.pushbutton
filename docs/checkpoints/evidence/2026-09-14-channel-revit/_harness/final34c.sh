S="C:/Users/twitc/AppData/Local/Temp/claude/C--Users-twitc-Desktop-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton/62996b12-9314-442c-9f86-45843276ca9c/scratchpad"
cd "$S"
IDS=$(py -3 -c "import json;print(json.dumps(json.load(open('r_cfg.json'))['ids']))")
echo "{\"ids\":$IDS,\"strategy\":\"CHANNEL\",\"create\":true,\"purge_bench\":true,\"level_pe_cm\":272.0,\"out\":\"r_final34c_run1.json\"}" > r_cfg.json
echo "START run1 $(date +%T)"
sh run.sh r_channel.py
echo "END run1 $(date +%T)"
echo "{\"ids\":$IDS,\"strategy\":\"CHANNEL\",\"create\":true,\"purge_bench\":false,\"level_pe_cm\":272.0,\"out\":\"r_final34c_run2.json\"}" > r_cfg.json
sh run.sh r_channel.py
echo "END run2 $(date +%T)"
py -3 summarize.py r_final34c_run1.json
py -3 summarize.py r_final34c_run2.json
