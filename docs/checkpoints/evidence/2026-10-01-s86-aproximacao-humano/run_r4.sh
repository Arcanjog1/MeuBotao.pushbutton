#!/bin/bash
# uso: run_r4.sh REPO TAG [COURSES] -> sol_TAG.json, rows_TAG.json e placar contra o humano
W=/c/Users/CIVIX/AppData/Local/Temp/s85r4
REPO="$1"; TAG="$2"; export COURSES="${3:-14}"
cd "$W"
t0=$(date +%s)
OPENBLAS_NUM_THREADS=1 py -3 -u export_r4.py "$REPO" "sol_$TAG.json" > "solve_$TAG.log" 2>&1
py -3 sol_to_rows.py "sol_$TAG.json" "rows_$TAG.json" >> "solve_$TAG.log" 2>&1
echo "== $TAG (fiadas $COURSES) $(( $(date +%s) - t0 ))s $(tail -3 solve_$TAG.log | head -2 | tr '\n' ' ')"
PYTHONIOENCODING=utf-8 py -3 r4_score.py "rows_$TAG.json"
