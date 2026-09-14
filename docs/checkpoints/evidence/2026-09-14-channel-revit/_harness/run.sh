#!/bin/sh
# usage: run.sh script.py  -> concatenates head + script and runs
S="C:/Users/twitc/AppData/Local/Temp/claude/C--Users-twitc-Desktop-Scripts-extension-MinhaAba-tab-MeuPainel-panel-MeuBotao-pushbutton/62996b12-9314-442c-9f86-45843276ca9c/scratchpad"
cat "$S/rvlib_head.py" "$S/$1" > "$S/_combined_$1"
py -3 "$S/rmcp.py" "$S/_combined_$1"
