# Checkpoint — 2026-09-09 — Extração forense do projeto humano no Revit

```
data:      2026-09-09
tipo:      EXTRAÇÃO DE EVIDÊNCIA (somente leitura) — não é CR
escopo:    vergas, contravergas, canaletas, blocos especiais e blocos cortados
branch:    claude/revit-human-reference-extraction
status:    CONCLUÍDO
```

## O que foi feito

Leitura **somente leitura** do documento Revit aberto
`TORRE EASY-LO-R00_desanexado_joaoC9CL7.rvt` (Revit 2026), o
HUMAN_REFERENCE do benchmark, via `mcp__revit-pyrevit__execute_revit_code`.

**Nenhuma transação foi aberta.** Nada foi criado, movido, apagado,
renomeado ou salvo no RVT. Nenhum arquivo de produção foi alterado
(`nuvem/core/**`, benchmark, baseline, testes — todos intocados).

### Volume analisado

| Item | Quantidade |
|---|---:|
| Elementos não-tipo no documento | 182.677 |
| Peças de alvenaria analisadas | **67.712** |
| Pares família/tipo inventariados | **57** |
| Aberturas (portas/janelas/vãos) | **484** |
| Furos de tubulação | 200 |
| Níveis com modulação | 9 |
| Paredes (parâmetro `Parede`) | 651 |
| Vergas (por uso) | **392** |
| Contravergas (por uso) | **147** |
| Canaletas | **6.584** |
| Blocos cortados | **3.887** |
| Relações peça↔abertura↔parede | **539** |
| Padrões quantificados | 20 |

## Achados que mudam o entendimento do domínio

1. **"CORTADO" é corte em ALTURA (19 → 9 cm), não em comprimento** —
   93,5% das peças cortadas. `9 + 1 + 9 = 19`: duas peças cortadas
   empilhadas reconstroem uma fiada normal.
2. **A grade vertical da `REGRAS §8` está confirmada** contra o projeto
   humano real: 1ª fiada em `base + 1 cm`, passo de 20 cm, 13 fiadas
   (99,35% de aderência), verificado em dois níveis independentes.
3. **Verga nasce exatamente no topo do vão (392/392) e contraverga
   termina exatamente no peitoril (147/147)** — offset 0,00 cm, sem
   exceção. Apoio ≥ 9 cm de cada lado em 1.078/1.078 apoios.
4. **Toda porta tem verga; nenhuma porta tem contraverga** (248/248) —
   confirma independentemente o critério de `REGRAS §10.4`.
5. **25 peças da família `VERGA JANELA` são usadas como contraverga** —
   classificar pelo nome da família erra 4,6% dos casos.
6. **Canaleta é predominantemente cinta de topo de parede** (91% na
   última fiada), não sistema de verga.
7. **CONFLITO 10.7 remedido**: 71,4% (era 39,4%), com mecanismo
   alternativo identificado. **Continua aberto.**
8. **Catálogo do solver cobre 80,19%** das peças (6 de 57 tipos); 2.121
   peças usam família conhecida com tipo desconhecido (`VEDAÇÃO`).
9. **Sete armadilhas de leitura do Revit** medidas e registradas
   (`Level.Elevation` deslocado 15 m, bbox com folga de +1 cm por ponta,
   `LookupParameter` acentuado retornando `None`, vergas sem nível, etc.).

## Onde ficou

- Dados estruturados: `docs/revit_reference_extraction/01..09_*.json`
- Relatório: `docs/revit_reference_extraction/REPORT_HUMAN_REVIT_MODULATION.md`
- Scripts reprodutíveis: `docs/revit_reference_extraction/_scripts/`
- Registro nas regras: `nuvem/REGRAS_MODULACAO_BLOCOS.md` **seção 30**
  (mais referência cruzada acrescentada em 10.7)

## O que NÃO foi feito (deliberadamente)

- Nenhuma regra do solver foi criada, alterada ou implementada.
- Nenhum threshold, baseline ou benchmark foi tocado.
- Encontros L/T/X não foram classificados (exige reconstruir o grafo de
  paredes a partir das peças — não há `Wall` no documento).
- Amarração fiada par/ímpar não foi analisada (os dados de
  `07_special_blocks.json` já permitem fazê-la depois).
- Os 102 vãos rotulados `ABERTURA` não foram cruzados com a categoria
  `Quadro estrutural` (819 elementos) — 76% deles não têm nenhuma peça
  especial associada, e a hipótese de estarem resolvidos por estrutura
  ficou **não verificada**.

## Próximo passo sugerido

Decisão do usuário sobre os 4 pontos de política listados em `K.2` do
relatório (canaleta de topo, comprimento de verga, simetria de apoio,
vãos `ABERTURA`) e sobre o escopo da alvenaria de **vedação** no catálogo.
Só depois disso faz sentido abrir CR de implementação.
