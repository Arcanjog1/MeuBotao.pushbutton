# SPEC — `CR-BENCH-OPENING-RECONSTRUCTION`

> **Não implementada.** Esta spec descreve uma CR **de benchmark**, que
> altera gabarito aprovado e por isso **exige autorização humana explícita
> e específica** antes de qualquer escrita em `nuvem/benchmark/projects/**`.

## 1. Causa-raiz (localizada, com medição)

`nuvem/core/engine/opening_audit.py::detect_wall_openings_from_courses`
agrega o vão como **união** (`min`/`max`) dos vazios por fiada, aceitando
diferença de borda de até `OPENING_RUN_EDGE_MATCH_TOLERANCE_CM = 15,0cm`.
A tolerância deveria decidir **identidade** ("é a mesma abertura?") e acaba
decidindo **geometria** ("onde fica a jamba?").

Onde a jamba coincide com nó T/L, as fiadas alternam entre "reserva de nó
vazia" e "peça de amarração atravessa o nó" — diferença de exatamente
`B34 − B19 = 34 − 19 = 15,0cm`. O envelope grava a borda mais larga.

Defeito secundário, na mesma família: `WALL_SPLIT_GAP_CM =
OPENING_GAP_MAX_CM = 260cm` faz um espaço de 156cm **entre duas paredes
separadas** ser reconstruído como *abertura numa parede só*.

## 2. Evidência de origem

Toda em `reconstruction_evidence.json` deste diretório, mais:

| evidência | valor |
|---|---|
| aberturas com assinatura de envelope | **19 por projeto** (`spread_inicio = spread_fim = 15,0cm`) |
| achados espúrios gerados | **195 por projeto** (`OPENING_BLOCK_CROSSES_JAMB`) |
| nó T/L a 8,0cm da jamba gravada, peça cobrindo o ponto do nó | 116 dos 195 |
| larguras 186cm / 131cm no `input.json` MEDIDO do TGD | **0 / 0** (só reconstruídas) |
| consenso == buraco entre paredes MEDIDAS (TGD) | **16 de 19** |
| `OPENING_BLOCK_CROSSES_JAMB` do solver TP1 com o candidato | **168 → 0** |

## 3. Arquivos afetados

| arquivo | papel |
|---|---|
| `nuvem/core/engine/opening_audit.py` | **produção** — `detect_wall_openings_from_courses`, `OPENING_RUN_EDGE_MATCH_TOLERANCE_CM` |
| `nuvem/benchmark/extract/reconstruct.py` | consumidor (`WALL_SPLIT_GAP_CM`, montagem de parede/abertura) |
| `nuvem/core/wall_modeling.py` | referencia as mesmas constantes (l. 2096) |
| `nuvem/benchmark/projects/*/reference.json`, `input.json` | **gabarito — só com autorização explícita** |
| `nuvem/benchmark/projects/*/reference_score.json` | recalibração |

**Atenção de escopo:** `opening_audit.py` é **produção**, e o solver ao vivo
usa `detect_wall_openings_from_courses`. Isto **não** é uma CR "só de
benchmark" se o detector for alterado. Duas CRs separadas são preferíveis:

- **BENCH-OPENING-RECONSTRUCTION-A** (detector): corrige a agregação em
  `opening_audit.py`, com STATE_A/B próprios e hard gates de produção.
- **BENCH-OPENING-RECONSTRUCTION-B** (gabarito): regrava
  `reference.json`/`input.json` com o detector corrigido — **exige
  autorização humana específica**.

## 4. Metodologia de reconstrução proposta

1. **Agregar por consenso, não por envelope.** A borda do vão passa a ser a
   que **toda** fiada compatível respeita (interseção), com a tolerância
   mantendo só o papel de identidade do run.
2. **Registrar o desacordo**, em vez de apagá-lo: gravar por abertura o
   `jamb_spread_cm` medido, para que a jamba "dentada" seja um dado, não um
   arredondamento silencioso.
3. **Separar parede de abertura.** Quando existir geometria medida no mesmo
   eixo mostrando dois trechos distintos, reconstruir **duas paredes**, não
   uma parede com abertura. Sem geometria medida, marcar
   `opening_provenance = "INCONCLUSIVE"` e **não** decidir por conta própria.
4. **Não usar o resultado do solver como gabarito** em nenhuma etapa.

## 5. Regras de proveniência (obrigatórias)

Cada abertura reconstruída grava:

```
opening_provenance = MEASURED            # veio do Revit (source_element_id)
                   | RECONSTRUCTED_CONSENSUS
                   | RECONSTRUCTED_ENVELOPE   # legado, a eliminar
                   | INCONCLUSIVE
jamb_spread_cm     = <desacordo entre fiadas, em cm>
evidence_ref       = <id do elemento / trechos medidos usados>
```

Abertura sem proveniência não entra em gabarito.

## 6. Testes exigidos

- **Reproducer mínimo, sintético** (sem corpus): parede reta, um nó T na
  jamba, fiadas alternando `C09 570–579` / `B34 560–594`, vazio de 156cm.
  Falha antes (vão detectado = 186cm), passa depois (156cm).
- Teste de que `OPENING_RUN_EDGE_MATCH_TOLERANCE_CM` **não** entra na
  geometria gravada: variar o desencontro entre fiadas de 0 a 14,9cm e
  exigir borda gravada **constante**.
- Teste de proveniência: toda abertura do gabarito tem
  `opening_provenance` preenchido.
- Regressão: as 19 aberturas listadas em `candidate_provenance.json`.

## 7. Comparação antes/depois exigida

Nos 3 projetos, sobre o **gabarito** e sobre o **solver**:
`OPENING_BLOCK_CROSSES_JAMB`, `OPENING_BLOCK_INSIDE_DOOR/WINDOW`,
`OPENING_MISSING_LINTEL`, `OPENING_MISSING_COUNTER_LINTEL`,
`OPENING_SOLID_BELOW_SILL_MISSING`, todos os `JUNCTION_*`, todos os
`COVERAGE_*`, `PRISM_*`, `COMPENSATOR_*`, e fingerprint físico.

## 8. Hard gates

| gate | exigência |
|---|---|
| aberturas **reais** preservadas | nenhuma abertura com `source_element_id` medido pode sumir, encolher ou mudar de parede |
| **nenhum vão encurtado para esconder bloco invasor** | toda redução de largura precisa de evidência de proveniência própria; redução sem evidência é **reprovação** |
| centro do vão | preservado (deslocamento < 0,01cm) salvo evidência medida em contrário |
| paredes fora de escopo | intocadas |
| defeito real do solver | não pode ser apagado: comparar o conjunto de achados por **identidade geométrica**, não por contagem |
| identidade | `wall_id` / `opening_id` estáveis entre versões do gabarito |
| se o detector mudar | fingerprint físico do solver medido nos 3 projetos, STATE_A/B, determinismo em 2 processos novos |
| `baseline.json` | **intocado** enquanto o PR #20 estiver em avaliação |

## 9. Risco de alterar o gabarito

Alto e explícito. O gabarito é a régua: mexer nele **muda todas as métricas
históricas** e pode mascarar defeito real do solver. Mitigações exigidas:

- versionar o gabarito (`reference_schema_version` + changelog por
  abertura), nunca sobrescrever em silêncio;
- manter o gabarito antigo lado a lado por pelo menos uma CR;
- recalibrar `reference_score.json` **na mesma CR**, e `baseline.json`
  **somente** em CR separada e autorizada (`BENCH-BASELINE-REFRESH`);
- publicar a tabela antes/depois de §7 no PR.

## 10. Critério de aprovação humana

A CR só pode ser aprovada se o usuário confirmar, explicitamente:

1. que aceita a mudança de régua (as métricas históricas deixam de ser
   comparáveis em valor absoluto);
2. qual leitura vale para os 19 casos — **abertura estreita** ou **duas
   paredes separadas** (a evidência medida do TGD aponta para a segunda);
3. o que fazer com os casos `INCONCLUSIVE` do TP1, que não têm fonte
   medida.

## 11. Estratégia de versionamento e baseline

- `reference.json` novo entra com `schema_version` incrementado e
  changelog por abertura;
- `reference_score.json` recalibrado na mesma CR;
- `baseline.json` **não** é regravado nesta CR (fica para
  `BENCH-BASELINE-REFRESH`, que exige decisão própria);
- PR **draft**, revisão independente obrigatória, sem merge automático.
