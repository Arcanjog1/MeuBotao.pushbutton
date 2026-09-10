# BUTANTÃ R08_LT — referência humana nº 2 (sistema de CANALETAS)

> **EVIDÊNCIA, NÃO NORMA.** Extração somente leitura de 2026-09-09.
> Nada aqui é regra do solver. Nenhum arquivo de produção foi tocado.

Segunda referência humana do repositório, escolhida por resolver as aberturas
com **canaletas** em vez de verga/contraverga — ao contrário do
[projeto A, TORRE EASY](../REPORT_HUMAN_REVIT_MODULATION.md).

**Leia primeiro:** [`REPORT_HUMAN_REVIT_MODULATION.md`](REPORT_HUMAN_REVIT_MODULATION.md)

## Resumo em uma tela

| | |
|---|---|
| Documento | `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO).rvt` |
| Revit | 2026 (26.3.0.37), unidades em cm |
| Peças de alvenaria | **65.747** (Modelos genéricos) |
| Grupos de parede `(Parede, nível)` | **340** (~34 eixos) |
| Aberturas | **142** — 47 PORTA · 61 JANELA · 34 ABERTURA |
| Canaletas | **8.931** |
| Blocos cortados | **286** |
| **Canaleta acima do vão** | **PORTA 47/47 (100%)** · JANELA 58/61 (95,1%) |
| **Canaleta abaixo do peitoril** | **89/89 (100%)** |
| Offset peça↔vão | **0,00 cm** (135/136 acima · 88/89 abaixo) |
| Vergas/contravergas instanciadas | **0** (69 tipos carregados e não usados) |
| Cobertura do catálogo do solver | **85,12%** das peças · 6/21 tipos |

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| [`01_family_catalog.json`](01_family_catalog.json) | 21 pares família/tipo: sólido, bbox, parâmetros, status no catálogo do solver |
| [`02_openings.json`](02_openings.json) | as 142 aberturas com identidade física, cotas e classificação |
| [`03_above_openings.json`](03_above_openings.json) | o que existe acima de cada vão: famílias, cota, apoios, continuidade |
| [`04_below_windows.json`](04_below_windows.json) | o que existe abaixo de cada peitoril (89 aberturas) |
| [`05_channels.json`](05_channels.json) | inventário de canaletas com papel classificado (`TOP_BOND_BEAM`, `ABOVE_DOOR`, …) |
| [`06_cut_blocks.json`](06_cut_blocks.json) | blocos cortados: modo de corte, dimensões reais, contexto |
| [`07_special_blocks.json`](07_special_blocks.json) | compensadores, pastilhas e a mecânica da peça de 9 cm |
| [`08_piece_opening_wall_relations.json`](08_piece_opening_wall_relations.json) | relação peça ↔ abertura ↔ parede (3.625 registros) |
| [`09_observed_patterns.json`](09_observed_patterns.json) | 18 padrões quantificados, apoios, largura×solução, exceções |
| [`10_torre_easy_comparison.json`](10_torre_easy_comparison.json) | comparação fato a fato com o projeto A |
| [`_scripts/`](_scripts/README.md) | scripts de extração (lado Revit) e de análise (lado local) |
| [`evidence/`](evidence/verga_search.json) | saídas brutas: sólidos, busca de vergas, cobertura, contagem por família |

## Convenções dos dados

- **Sufixos de proveniência**: `_MEDIDO` (lido do Revit), `_CALCULADO`
  (derivado de medições), `_INFERIDO` (dedução justificada no relatório).
- **`_bbox` × `_solid`**: a BoundingBox das famílias tem **+1 cm por face** no
  comprimento (junta). Apoios são publicados nas duas formas; `_solid` é o apoio
  real de alvenaria.
- **Identidade física**: `wall_physical_key = "<Parede>|<nível>|ax=<X|Y>|perp=<coord>"`.
  `element_id` é identidade **local**; `unique_id` é o identificador estável.
- **Clones de pavimento**: os pav. 3º–8º são cópias geométricas exatas do 2º
  (0 diferenças em 6.727 peças). Os arquivos `03`–`06` trazem registros
  detalhados apenas dos níveis únicos, com as contagens do modelo inteiro em
  `totals_all_levels`. Registros propagados carregam `propagated_from_opening_id`.

## Reproduzir

O servidor pyRevit Routes desta máquina responde em **48885** (a config do MCP
aponta para 48884). Com o RVT aberto:

```bash
py _scripts/rmcp.py _scripts/s07_dump_pieces.py
```

Os scripts `s*.py` rodam **dentro** do Revit (IronPython 2) e gravam JSON/JSONL
em disco; os `an*.py` e `emit*.py` rodam localmente em Python 3 sobre esses
arquivos.

## O que este projeto NÃO responde

- amarração em encontros L/T/X (fora do escopo desta missão);
- vínculo peça-a-peça entre canaleta e graute;
- 760 canaletas (8,51%) ficaram sem contexto atribuído.

[Revisão de integração e erratas](REVIEW_2026-09-10.md): limites de reprodução, classificação e apoios.
