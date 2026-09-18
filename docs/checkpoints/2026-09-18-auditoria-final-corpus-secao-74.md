# Checkpoint — auditoria final independente do corpus da §74

Quarta e última entrega desta sessão. **Produção intocada**:
`git diff origin/main..HEAD -- nuvem/` vazio. PR #42 auditado em worktree
isolado, somente leitura. Nenhum Revit.

```json
{
  "date": "2026-09-18",
  "branch": "claude/jolly-ritchie-0bq5f6",
  "head": "803ddc2a458b91fc10c89275e6fceb671c581e6b",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/48",
  "objective": "Decidir se a limitacao da auditoria anterior (numeros de corpus nao reproduziveis) pode ser removida, agora que a geometria foi versionada. Auditar o corpus s74 em f7c208b / 730ec52 contra o motor 2c55211.",
  "changes": [
    "docs/AUDITORIA_FINAL_CORPUS_SECAO_74.md: NOVO. Relatorio completo com as 18 respostas obrigatorias.",
    "tools/audit/audit_s74_independente.py: NOVO. Auditor independente que NAO importa tools/audit/s74_corpus.py nem o motor; inclui a ancora externa de room_min.",
    "tools/audit/s74_mutation_plugin.py: NOVO. Plugin pytest que prende _t_intersection_room_ok em True/False para medir nao-circularidade.",
    "NENHUM arquivo sob nuvem/ alterado; PR #42 nao tocado."
  ],
  "tests": [
    "tools/audit/audit_s74_corpus.py (oficial, rodado por mim) -> 40 casos, 40 PASS, 0 FAIL, 93,6 s",
    "pytest tests/test_s74_corpus_butanta.py -q -> 39 passed, 163,96 s",
    "pytest tests/test_s74_corpus_butanta.py -q -m 'not slow' -> 33 passed, 6 deselected, 0,27 s",
    "tools/audit/audit_s74_independente.py -> 81 verificacoes OK, 0 falhas",
    "mutacao MUT=true -> 17 falhas; MUT=false -> 11 falhas"
  ],
  "known_failures": [
    "Nenhuma falha observada. Duas imprecisoes DOCUMENTAIS no README do corpus, registradas no relatorio."
  ],
  "physical_deltas": [
    "Nenhum: auditoria somente de leitura.",
    "ANCORA EXTERNA (nova): room_min dos 5 nos de fronteira recalculado com aritmetica 2D pura sobre geometry.json, sem o motor. no 24 = 26,988000; nos 44/46 = 26,996513; no 12 = 27,003487; no 26 = 27,012000. Deltas contra o corpus entre 2,5e-14 e 1,9e-13 cm.",
    "ACHADO: em W04 os nos estao em t exatamente redondo (642,000000 e 987,000000) e as BORDAS DAS ABERTURAS carregam o +0,012. A margem submilimetrica vem da posicao das aberturas na planta, nao de arredondamento do motor.",
    "Cobertura da ancora nos 37 T: room_plus casa em 26, room_minus em 24, ao menos um lado em 30 de 37. Os 7 restantes tem o limite dado por reserva de no'.",
    "MEDIDO: perna do B34 nao exercitada - boneca minima dos 37 T = 69,0002 cm contra 34,0 exigidos.",
    "MEDIDO: hard gates do LEGADO (strategy=None) = non_modular 78, unsupported 67, identicos com a flag ligada e desligada; os 6 casos CHANNEL ficam 0/0/0/0."
  ],
  "decisions_taken": [
    "REMOVER a limitacao da auditoria anterior: o corpus e' reproduzivel sem Revit, sem bancada e sem as entradas brutas. Veredito sobe de SUPPORTED WITH LIMITATIONS para SUPPORTED BY INDEPENDENT AUDIT.",
    "Fechar por conta propria a lacuna que o README declarava aberta (ancorar room_min fora do motor), em vez de apenas registra-la.",
    "Corrigir o escopo do meu proprio teste de hard gates: a alegacao de 0/0/0/0 e' sobre o fluxo CHANNEL; aplicar aos casos de legado era erro meu, nao do corpus."
  ],
  "decisions_pending": [
    "README do corpus: recortar a frase dos hard gates para 'nos casos CHANNEL' (os dois casos de legado gravados tem 78/67) e corrigir que target_s72.clean.json TEM sha256 gravado e que o total com a variante e' 12,2 MB, nao ~9 MB. Imprecisoes conservadoras, nao defeitos.",
    "Perna do B34 da conjuncao continua sem cobertura de regressao (boneca minima 69,0002 cm vs 34). Declarada pelo corpus; nao impede o veredito sobre a §74.",
    "Circularidade residual: 7 dos 37 T tem o limite dado por reserva de no' e continuam sem ancora externa. Suficiente para esta auditoria (a fronteira esta' ancorada); nao suficiente para uma regeneracao futura do corpus.",
    "tools/preflight/purge_guard.py continua pendente de integracao no harness (autorizacao do usuario).",
    "capture_export.py:57: PR separado, fora do #42."
  ],
  "next_steps": [
    "Nenhuma acao pendente desta auditoria. As tres pendencias acima sao decisao do usuario."
  ],
  "references": [
    {"path": "docs/AUDITORIA_FINAL_CORPUS_SECAO_74.md"},
    {"path": "docs/AUDITORIA_SECAO_74_PATCH_2c55211.md"},
    {"path": "docs/RECONCILIACAO_74_2026-09-17.md"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Veredito

**`SUPPORTED BY INDEPENDENT AUDIT`** — a limitação material da auditoria
anterior está removida. O corpus é reproduzível sem Revit, e a âncora
externa de `room_min` fecha, nos cinco nós que decidem a questão, a
lacuna que o próprio README declarava aberta.
