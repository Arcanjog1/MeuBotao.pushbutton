# REFERENCE CORPUS SUMMARY

Projetos executados: 5

- IMPROVED: 0
- NEUTRAL: 0
- REGRESSED: 2
- MIXED: 1
- NOT_COMPARABLE: 2

**OVERALL: CRITICAL_REGRESSION_PRESENT**

Uma media boa NUNCA esconde isto (item 19) - pelo menos um projeto tem regressao em invariante critico:

## REGRESSOES CRITICAS

- **torre_easy_lo_r00_tgd**: `COVERAGE_MISSING_ROW` 265 -> 293
- **torre_easy_lo_r00_tgd**: `COVERAGE_ROW_MOSTLY_EMPTY` 171 -> 187
- **torre_easy_lo_r00_tgd**: `OPENING_BLOCK_INSIDE_DOOR` 45 -> 49
- **torre_easy_lo_r00_tp1**: `COVERAGE_MISSING_ROW` 16 -> 18

## Projetos

| projeto | kind | confidence | comparavel | veredito/motivo |
|---|---|---|---|---|
| torre_easy_lo_r00_tgd | HUMAN | MEDIUM | sim | REGRESSED |
| torre_easy_lo_r00_tp1 | HUMAN | MEDIUM | sim | REGRESSED |
| piloto_sintetico_2x2 | SYNTHETIC | NONE | sim | MIXED |
| chacara_torre_easy_lo_tropicale | ANALYSIS_ONLY | NONE | nao | reference_kind=ANALYSIS_ONLY nao e' reproduzivel (input.json/input_real.json (linhas de CAD por layer + aberturas medidas), reference.json (posicao XY/Z, rotacao e codigo de CADA instancia de bloco, nao so' a contagem agregada por tipo), wall_modeling_snapshot.json (eixos/nos L-T-X reconstruidos), confirmacao de qual dos 22 niveis ('00. FUN' a '21. COB') vira o par input/reference, como foi feito para TGD/TP1 dentro de TORRE_EASY-LO-R00) |
| torre_easy_lo_r00_full_building | ANALYSIS_ONLY | NONE | nao | reference_kind=ANALYSIS_ONLY nao e' reproduzivel (extracao (input_real.json + reference.json) de cada um dos ~19 niveis alem de 04. TGD e 05. TP1 (ja catalogados como torre_easy_lo_r00_tgd/torre_easy_lo_r00_tp1), confirmacao de pareamento input x referencia por nivel, como foi feito para TGD) |

## Matriz projeto x metrica

| projeto | coverage | prism | openings | L/T/X | collisions | non_modular | compensators |
|---|---|---|---|---|---|---|---|
| torre_easy_lo_r00_tgd | UNCHANGED | IMPROVED | REGRESSED | IMPROVED | UNCHANGED | UNCHANGED | IMPROVED |
| torre_easy_lo_r00_tp1 | UNCHANGED | IMPROVED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | IMPROVED |
| piloto_sintetico_2x2 | UNCHANGED | IMPROVED | UNCHANGED | UNCHANGED | UNCHANGED | UNCHANGED | REGRESSED |
| chacara_torre_easy_lo_tropicale | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE |
| torre_easy_lo_r00_full_building | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE | NOT_COMPARABLE |