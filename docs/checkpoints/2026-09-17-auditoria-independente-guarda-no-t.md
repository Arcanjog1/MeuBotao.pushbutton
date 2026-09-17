# Checkpoint — auditoria adversarial independente da guarda de espaço do nó T

Missão paralela de auditoria. **Produção, solver e PR #42 intocados**:
`git diff --stat 3d4c687 -- nuvem/` vazio. Nenhuma regra física foi
editada (ver "pendência" abaixo).

```json
{
  "date": "2026-09-17",
  "branch": "claude/jolly-ritchie-0bq5f6",
  "head": "3d4c687d14830c39fdf13a1b87bb0fcb76221db0",
  "base": "55e990d962ed22ae1021f0d335db197607bddda1",
  "pr": "not-created",
  "objective": "Tentar REFUTAR, de forma independente, a tese de que o motor so' forca a amarracao especial no no' T quando ha' espaco fisico real, e de que as tolerancias envolvidas sao ruido de calculo e nunca licenca para invadir vao. Auditar PIER_PHYSICAL_FIT_TOLERANCE_CM, as conversoes cm<->pes, _t_intersection_room_ok, monotonicidade, invariancia, faltas reais, legado e o procedimento de purga.",
  "changes": [
    "tests/test_t_room_physical_guard_independent_audit.py: NOVO. 11 verificacoes adversariais; constantes fisicas redigitadas do bloco (B54=54 -> 27cm por lado, B34=34, tolerancia 0,05cm), oraculo recalculado do zero, geometria montada em coordenadas de MUNDO e so' depois convertida para o parametro t de cada parede.",
    "tests/audit_t_room_physical_guard.py: NOVO. Ferramenta rodavel sem pytest; alem da bateria, MEDE por bisseccao (1e-7 cm) onde cada fronteira fica de fato.",
    "docs/AUDITORIA_INDEPENDENTE_GUARDA_ESPACO_T.md: NOVO. Relatorio, achados, checklist de preflight da purga e veredito.",
    "NENHUM arquivo sob nuvem/ alterado; wall_stepper.py, wall_modeling.py, regras fisicas e baseline/golden intocados."
  ],
  "tests": [
    "python3 -m pytest tests/test_t_room_physical_guard_independent_audit.py -q -> 11 passed in 0.44s (HEAD 3d4c687)",
    "python3 tests/audit_t_room_physical_guard.py -> 11 verificacoes, 0 falhas, + fronteiras medidas por bisseccao",
    "python3 -m pytest tests/test_script.py -q -> 262 passed in 50.03s",
    "python3 -m pytest tests/ -q -m \"not slow\" -> 1189 passed, 31 deselected in 665.31s (exit 0)"
  ],
  "known_failures": [
    "Nenhuma falha observada no escopo. Nenhuma contradicao encontrada contra a tese fisica auditada."
  ],
  "physical_deltas": [
    "Nenhum: auditoria somente de leitura, nenhuma peca muda de lugar.",
    "MEDICAO (nao alteracao) - fronteira real do no' T por bisseccao: B54 lado direito 26,999970 cm; B54 lado esquerdo 26,999970 cm; B34 boneca 33,999970 cm. Desvio de -3,048e-05 cm do nominal em todos, que e' 1e-6 pes.",
    "MEDICAO - guarda de jamba, fronteira inclusiva: excesso <= 0,05 cm mantem o layout; 0,0500001 cm remonta; o remontado nunca termina alem de limite + 0,05 cm."
  ],
  "decisions_taken": [
    "Nao inventar a §74: ela nao existe na main (55e990d, maior secao §51), na branch do PR #42 (759bcd4, maior secao §72), em nenhuma branch remota, em nenhum PR aberto nem em git log --all. Auditado o objeto fisico que os dez itens da missao descrevem, com a ressalva registrada na secao 0 do relatorio.",
    "Refazer a busca pela §74 em clone COMPLETO: a primeira varredura rodou em clone raso (252 commits alcancaveis). Apos git fetch --unshallow (480 commits), as buscas por §73/§74 e por r_reset_vaos foram repetidas sobre o historico inteiro e o resultado nao mudou. O validador documental tambem so passou depois do unshallow - antes acusava 8a93a27 como nao integrado, a mesma armadilha ja registrada no PROJECT_STATUS para a leitura de 2026-09-12.",
    "Descartar 10 'refutacoes' de invariancia como defeito do proprio auditor: o gerador de cenario passava coordenada de MUNDO como parametro t. Corrigido e registrado no relatorio - e' o falso positivo que uma auditoria adversarial precisa eliminar antes de acusar."
  ],
  "decisions_pending": [
    "PENDENCIA DE REGISTRO EM REGRA (conflito de instrucoes, decisao do usuario): o CLAUDE.md exige que todo conhecimento novo de AMARRACAO va' para nuvem/REGRAS_MODULACAO_BLOCOS.md; esta missao proibe editar regras fisicas. A missao e' a orientacao mais recente e prevaleceu. Fica pendente registrar la': a guarda do no' T exige 27cm por lado e 34cm na boneca com folga de 1e-6 pes (3,048e-05 cm), 1640x mais apertada que PIER_PHYSICAL_FIT_TOLERANCE_CM - sao guardas de perguntas diferentes.",
    "ACHADO COLATERAL nao corrigido (missao proibe tocar producao): nuvem/core/capture_export.py:57 usa FEET_PER_METER = 0.3048 no fallback de ImportError contra 1.0/0.3048 nas outras seis definicoes; com _ft_to_cm = v*100/FEET_PER_METER o fallback da' 328,08 cm por pe' em vez de 30,48. So' alcancavel fora do layout real do botao; o teste do modulo le' a constante do proprio modulo e por isso nao detecta.",
    "LACUNA DE PREFLIGHT: o procedimento de purga (purge_bench/purge_only em docs/checkpoints/evidence/2026-09-14-channel-revit/_harness/r_channel.py e q08_diag.py) REGISTRA 'remaining' mas nao AFIRMA que e' zero; exclusao parcial (elemento pinado, membro de grupo) deixa o run seguir sobre modelo sujo. Checklist independente na secao 11 do relatorio."
  ],
  "next_steps": [
    "Apresentar a §74 (arquivo + SHA) para o veredito ser reemitido em nome dela, se ela existir fora do que foi buscado por fetch.",
    "Decidir sobre as tres pendencias acima: registro da regra de amarracao, fallback do capture_export e assercao remaining == 0 na purga."
  ],
  "references": [
    {"path": "docs/AUDITORIA_INDEPENDENTE_GUARDA_ESPACO_T.md"},
    {"path": "tests/test_t_room_physical_guard_independent_audit.py"},
    {"path": "tests/audit_t_room_physical_guard.py"},
    {"path": "docs/PROJECT_STATUS.md"}
  ]
}
```

## Veredito

**`SUPPORTED BY INDEPENDENT AUDIT`** — para a tese física auditada, com
as duas ressalvas da seção 12 do relatório: (1) o veredito não cobre a
§74 por nome, porque ela não foi localizada; (2) se a §74 afirmar que
`_t_intersection_room_ok` absorve 0,05 cm, essa afirmação específica é
**falsa** — a guarda do nó T é 1640x mais apertada. Isso não enfraquece a
tese física; torna-a mais forte.
