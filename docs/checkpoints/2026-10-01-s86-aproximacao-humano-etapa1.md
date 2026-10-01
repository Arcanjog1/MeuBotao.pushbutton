# §85/§86 — aproximação do projeto humano BUTANTÃ R08_LT, etapa 1 (base medida, análise e R1/R5 aplicadas)

Checkpoint INTERMEDIÁRIO pedido pelo usuário ("salve tudo que já foi processado até essa etapa", 2026-10-01).
Estado CANDIDATO local da branch `claude/revit-butanta-modulation-8611b5` — sem PR, sem push, sem merge. Não é
estado oficial nem aprovação normativa.

```json
{
  "date": "2026-10-01",
  "scope": "current",
  "branch": "claude/revit-butanta-modulation-8611b5",
  "head": "88a67c8cb654b3f1e0d89edaf862572eb8de3f7a",
  "base": "894e3f5278ffa9cb030efe01a70c7305b252af15",
  "pr": "not-created",
  "objective": "Pedido do usuario (2026-10-01): observar e analisar como foi feito o projeto HUMANO (BUTANTA R08_LT, 1o pavimento) e chegar no resultado mais proximo possivel ajustando as REGRAS e o CALCULO de modulacao, sem copiar pecas; pode alterar qualquer coisa no butanta testes; no fim, relatorio e o pavimento inteiro recriado e visivel no Revit. Esta etapa: base medida, analise do humano (regras R1-R10), R1/R5 aplicadas no butanta testes, registro das regras na secao 86.",
  "changes": [
    "77dd0be, c64c7f8, 88a67c8 (antes desta etapa, sem checkpoint proprio): secao 83 renumerada; secao 85/85.8/85.9 (prisma pela area real, correcoes do usuario, grade de B34); secao 85.9/85.10 (familias gemeas na jamba, canaleta logica no catalogo, guarda de faixa vertical REPEATED_SPECIAL_STRIP, registros das rodadas 2/W1 no Revit) em nuvem/core/engine/b34_run_arrangement.py, nuvem/core/wall_modeling.py e testes.",
    "DOCS (esta etapa, sem codigo de producao): REGRAS secao 86 (86.0 regua da comparacao com o humano e numeros da base; 86.1 R1 aberturas na posicao ORIGINAL - REGRA OBRIGATORIA, aplicada; 86.5 R5 13 fiadas + calco - aplicada a altura, calco pendente de codigo; 86.11 indice R1-R10 com conflitos e bloqueios); evidencias em docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/; este checkpoint; PROJECT_STATUS.",
    "REVIT (butanta testes, por titulo; referencia R08_LT so lida): 19 aberturas deslocadas pelo microajuste voltaram a posicao original (desvio maximo das 44 = 0,0005 cm; comentarios MICROAJUSTE limpos); 46 paredes 280 -> 260 cm. Arquivo salvo pelo usuario as 14:11 de 2026-10-01 (depois destas mudancas, feitas ~13:22)."
  ],
  "tests": [
    "HEAD 88a67c8 (antes desta etapa): py -3 -m pytest tests/test_script.py -q -> 262 passaram; tests/test_jamb_compensator_alignment.py + tests/test_opening_micro_adjust_mover.py -> 34 passaram.",
    "Suite completa NAO executada nesta etapa (maquina com 0,4-0,8 GB livres; testes longos rodam nas worktrees de implementacao). Fica para a entrega final.",
    "Medicao contra o humano (docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/run_r4.sh + r4_score.py): motor 88a67c8 com aberturas originais: 14 fiadas F1 24,2 % (solve 602 s), 13 fiadas F1 26,4 % (solve 1 008 s)."
  ],
  "known_failures": [
    "Nenhuma observada no escopo dos testes executados; a suite completa nao foi rodada nesta etapa.",
    "Qualidade da base com aberturas originais (regua r2_eval, f0-11): furos quebrados 630 (humano 407), septos sem apoio 239 (humano 60) - o deslocamento das aberturas mascarava parte dos furos quebrados (Revit com aberturas deslocadas: 467)."
  ],
  "physical_deltas": [
    "Semelhanca de pecas com o humano (F1 1:1, mesmo codigo, lado do vazado menor, centro +-2 cm): Revit atual (rodada 2 + W1, 19 aberturas deslocadas, 14 fiadas) 20,8 %; motor 88a67c8 aberturas originais 14 fiadas 24,2 % (7 062 pecas); 13 fiadas 26,4 % (6 492 pecas; humano 6 634).",
    "Paredes com a fase invertida em relacao ao humano: W18 identica ao humano com fiadas pares/impares trocadas; W15, W20, W24, W25, W26 com 0 % - alvo da R2/R4 (86.2)."
  ],
  "decisions_taken": [
    "Usuario (2026-10-01): pode alterar qualquer coisa no butanta testes; sem copiar o humano; canaleta nunca serve de amarracao (por isso a cinta de topo segue a variante A, bloco de amarracao no quadrado do no).",
    "R1 (aberturas originais) reconfirma a secao 25.1 e desliga, neste modo, a autorizacao de deslocamento da secao 85.4."
  ],
  "decisions_pending": [
    "R4 x secao 30.5 (alternancia de papel obrigatoria): o humano contraria 9/9 paredes entre dois L - promover a 30.7?",
    "R7 cinta de topo: variante A (implementando) x variante B (igual ao humano, excecao a secao 75 so para TOP_BOND_BEAM).",
    "Shaft W27/W33: solucao humana (cantos na mesma fiada, sem B54 no miolo) x excecao B54+C09 da secao 85.8.",
    "Calco de C09 deitado (R5) e fiada partida H9 (secao 51.8) sem codigo.",
    "Passagem livre 51.9 fora do CHANNEL (conflito com a secao 80)."
  ],
  "next_steps": [
    "Integrar, uma por vez, as implementacoes R2/R4, R3, R7A/R8, R6/R10 e R9 (worktrees wf_ff7686b5-095-*), com testes e calculo completo medido contra o humano a cada passo; depois recriar o pavimento inteiro no butanta testes (Revit aberto), ler de volta, gerar as vistas e o relatorio final."
  ],
  "references": [
    {"path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"},
    {"path": "docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/LEIAME.txt"},
    {"path": "docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/r4_synthesis.txt"},
    {"path": "docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/placar_base13.txt"},
    {"path": "docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/placar_base14.txt"},
    {"path": "docs/checkpoints/evidence/2026-10-01-s86-aproximacao-humano/revert_plan.json"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Onde está cada coisa

- Regras: `nuvem/REGRAS_MODULACAO_BLOCOS.md` §86 (86.0, 86.1, 86.5, 86.11; as subseções 86.2, 86.3, 86.6–86.10
  entram com as implementações).
- Evidência versionada: [LEIAME da evidência](evidence/2026-10-01-s86-aproximacao-humano/LEIAME.txt) (humano em
  fileiras, scripts de extração/placar/cálculo, placares da base, plano das aberturas, síntese da análise).
- Rascunho local completo (não versionado, ~49 MB): `.claude/checkpoints/2026-10-01-s86-humano/` — extração bruta
  do humano, soluções completas da base, scripts dos analistas e da rodada 2.
- Implementações em andamento (branches locais, não integradas): `worktree-wf_ff7686b5-095-1` (R2/R4, WIP),
  `worktree-wf_ff7686b5-095-2` (R3, commits e48d38c/fea1b17), `worktree-wf_ff7686b5-095-3` (R7A/R8).
- Revit: `butanta testes.rvt` salvo pelo usuário em 2026-10-01 14:11 com as aberturas originais e paredes de 260 cm;
  a modulação existente ainda é a da rodada 2 + W1 (14 fiadas) e será substituída na recriação final.
