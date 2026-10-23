# Checkpoint 2026-10-23 — §88 DONA FRANCISCA: planta de estudo de massa levada para a grade de 5 cm e modulada

- **Branch:** `claude/revit-access-cee13e` sobre a main `c855397` (sem mudança de código de produto; só documentação:
  REGRAS §88, skill EXAMPLES.md, este checkpoint).
- **Base:** main `c855397` (§87.7). PR: nenhum.
- **Revit:** cópia `T:\EM ANDAMENTO\HALSTEN\DONA FRANCISCA - MODULACAO 2026-10-23.rvt` (salva) com 79 Walls
  contínuas, 99 aberturas + 99 recortes nativos e **16 767 blocos** (CHANNEL, 13 fiadas, 2,60 m). Original intocado.
- **Evidência (rascunho local, não versionado):** `%LOCALAPPDATA%\Temp\claude\df_geometry.json` (entrada do solve),
  `df_solve.json` (resultado, 20 MB), `df_snap_plan.json`, logs `solve_offline*.log`, scripts `scratchpad/revit/`
  (`revit_http.py`, `b1_main.py`, `c2_existing.py`, `c3_apply_snap.py`, `c4_fix_rest.py`, `c6_fix_dentes_cortes.py`,
  `b2e_export.py`, `b4_inject.py`, `b5_create.py`) e `scratchpad/oracle.py` (regras medidas da §88.2).
- **Números finais:** solve 16 791 peças / 0 não modulares / 0 colisões / 0 invasões; criação 16 767 / 24 puladas /
  8 amarrações não resolvidas / 40 reforços sem solução / 3 154 em vermelho; 41 de 79 paredes reprovadas na
  validação de qualidade (bonecas de 20 cm).
- **Pendências:** ver REGRAS §88.1 (arredondar CAD no `main()`), §88.5 (revisão das peças em vermelho; `math.isfinite`
  no IronPython); CR de performance do solve NONE (§80) — perfil em §88.3.
- Estado candidato, não oficial: nenhuma medição independente ainda.
