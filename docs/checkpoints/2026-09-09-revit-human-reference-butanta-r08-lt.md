# Checkpoint reconciliado — integração #35

```json
{
  "date": "2026-09-10",
  "branch": "claude/revit-human-reference-extraction-project-2",
  "head": "f0b59dcaf85b6653db42b72ad4bc3ceb1fafdc9a",
  "base": "59c0352e4a3f66349a08b1d3f1ac5b079ce72bf9",
  "pr": "https://github.com/Arcanjog1/MeuBotao.pushbutton/pull/35",
  "objective": "Reconciliar diff próprio e integrar evidência BUTANTÃ após #33.",
  "changes": [
    "Merge de main sem force-push; seção evidencial 31→41; erratas e limites dos dados publicados."
  ],
  "tests": [
    "python -m pytest tests/test_script.py -q: 260 passed em 75.22s, exit 0; evidence/2026-09-10-pr35-tests.json.",
    "Auditoria offline: dez JSON e quatro evidências parseados, contagens e vínculos conferidos; evidence/2026-09-10-pr35-json-audit.json."
  ],
  "known_failures": [
    "Raw/intermediários e etapa de redução de clones não publicados; erratas evidenciais explicitadas."
  ],
  "physical_deltas": [
    "ZERO produção/benchmark; dados JSON originais preservados."
  ],
  "decisions_taken": [
    "Usuário autorizou especificamente integrar #35 evidencial após limpar herança de #33 e passar gates. Nenhuma norma aprovada."
  ],
  "decisions_pending": [
    "Políticas de estratégias, apoio independente de CHANNEL, catálogo e topo."
  ],
  "next_steps": [
    "Passar gates, merge normal, iniciar PR isolado de organização/arquitetura."
  ],
  "references": [
    {
      "path": "docs/revit_reference_extraction/butanta-r08-lt/REVIEW_2026-09-10.md"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-pr35-tests.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-pr35-json-audit.json"
    }
  ]
}
```

STATUS do relato abaixo: HISTORICAL. SUPERSEDED BY: revisão acima.

# Checkpoint — 2026-09-09 — Extração forense do projeto humano nº 2 (BUTANTÃ R08_LT)

```
data:      2026-09-09
tipo:      EXTRAÇÃO DE EVIDÊNCIA (somente leitura) — não é CR
escopo:    sistema de aberturas com CANALETAS (2ª referência humana)
branch:    claude/revit-human-reference-extraction-project-2
HEAD base: 51ed8c20c8c7ab903b851cfaae1432663955200a
status:    CONCLUÍDO
```

## O que foi feito

Leitura **somente leitura** do documento Revit aberto
`BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO).rvt` (Revit 2026,
build 26.3.0.37), segundo projeto humano de referência do repositório.

**Nenhuma transação foi aberta.** Nada foi criado, movido, apagado, renomeado ou
salvo no RVT. Nenhum arquivo de produção alterado (`nuvem/core/**`, benchmark,
baseline, gabarito — todos intocados). A extração do TORRE EASY em
`docs/revit_reference_extraction/` **não foi sobrescrita**: este projeto ficou em
subpasta própria `docs/revit_reference_extraction/butanta-r08-lt/`.

### Método

O servidor MCP `revit-pyrevit` (porta **48884**) não respondeu. O pyRevit Routes
desta sessão do Revit está na porta **48885**; a extração usou `POST` direto em
`http://localhost:48885/revit_mcp/execute_code/` — **mesmo endpoint** que a
ferramenta MCP usa. Verificado no fonte da extensão, antes do primeiro uso, que
o handler **não abre transação automaticamente**.

Textos com acento voltam corrompidos no corpo da resposta HTTP; contornado
gravando arquivos UTF-8 direto do lado do Revit e lendo-os localmente.

### Volume analisado

| Item | Quantidade |
|---|---:|
| Elementos não-tipo no documento | 203.173 |
| Peças de alvenaria (Modelos genéricos) | **65.747** |
| Pares família/tipo inventariados | **21** |
| Aberturas | **142** (47 PORTA · 61 JANELA · 34 ABERTURA) |
| Níveis com modulação | 12 |
| Grupos de parede `(Parede, nível)` | **340** (~34 eixos) |
| Canaletas | **8.931** |
| Blocos cortados | **286** |
| Relações peça↔abertura↔parede | **3.625** |
| Padrões quantificados | **18** |

## Achado central

**A hipótese do usuário está confirmada: este projeto resolve as aberturas com
CANALETAS, não com verga/contraverga.** Três provas independentes:

1. **Ausência** — `VERGA PORTA`, `VERGA JANELA`, `VERGA JANELA 3 FUROS` e
   `CONTRAVERGA` estão **carregadas** (69 tipos) com **0 instâncias**. O
   parâmetro `Lintel` está zerado em 65.747/65.747 peças.
2. **Presença** — canaleta apoiada no topo do vão em **47/47 portas (100%)** e
   **58/61 janelas (95,1%)**; canaleta sob o peitoril em **89/89 (100%)**.
3. **Cota** — offset **0,00 cm** entre a peça e a borda do vão: 135/136 acima,
   88/89 abaixo.

**Diferença de fundo para o TORRE EASY**: lá a peça de reforço tem **9 cm** e é
um elemento sobreposto (verga); aqui é uma **fiada inteira de 19 cm** de
canaleta, integrada à grade modular.

## Outros achados que mudam o entendimento do domínio

1. **Pavimentos 3º a 8º são clones geométricos exatos do 2º** — assinatura
   `(família, bbox relativa ao datum)` idêntica em **6.727/6.727 peças, 0
   diferenças, nos 6 pavimentos**. As 43 aberturas do 2º valem para os 3º–8º
   (marcado como INFERIDO nos dados).
2. **A chave `Parede` embute a faixa de pavimento** neste projeto
   (`PAR10 - 2º PAVIMENTO AO 8º PAVIMENTO (TIPO)`), diferente do TORRE EASY
   (`PAR1`…`PAR117`). Um agrupamento por `Parede` sozinho junta 7 pavimentos.
3. **Topo do vão na cota 221 cm em 134/142 (94,4%)** — o vão termina numa linha
   da grade de 20 cm, nunca numa cota livre.
4. **A canaleta acima do vão não é peça única**: é uma sequência de
   `CANALETA INTEIRA` (39) + `CANALETA 34` + eventualmente `MEIA CANALETA`,
   montada como uma fiada normal.
5. **Não existe segunda fiada de canaleta abaixo do peitoril** (0/89). Acima,
   80,3% têm 2ª fiada canaletada — mas é a **cinta de topo**, não verga dupla.
6. **Apoio lateral não é regra dura aqui.** Mínimo medido **4 cm** acima e
   **−1 cm** abaixo (a corrida termina 1 cm dentro da jamba), contra ≥ 9 cm em
   784/784 no TORRE EASY. Coerente com a canaleta ser fiada, não peça apoiada.
7. **Cortado inverte a proporção**: corte em **altura** 43,4% aqui contra 93,5%
   no TORRE EASY; a maioria dos cortes é **no comprimento**, e 67 de 162 são em
   peças de canaleta.
8. **Cinta de topo converge entre os dois projetos**: 73,82% (251/340) aqui
   contra 71,43% (465/651) lá — mas **continua não sendo universal**, então o
   CONFLITO 10.7 de `REGRAS_MODULACAO_BLOCOS.md` **segue aberto**.
9. **Categoria *Vegetação* espelha a alvenaria 1:1** (65.747 instâncias `Cor …`)
   — representação gráfica, não alvenaria. Quem contar "Modelos genéricos +
   Vegetação" dobra o modelo.
10. **Armadilhas de API confirmadas no Revit 2026**: `ElementId.IntegerValue`
    não existe (usar `.Value`); `Element.Name` falha no IronPython para
    `FamilySymbol`; bbox tem **+1 cm por face** no comprimento; `BLOCO 54
    CORTADO` tem bbox inflada em Z (19 cm contra 9 cm no sólido).

## Exceções (12 de 142 aberturas)

- **6 vãos livres até o topo** (`PAR28`, 156 × 221): a alvenaria termina nas
  jambas, não há fiada sobre o vão. Confiança ALTA.
- **6 vãos pequenos** (61–66 cm) resolvidos com `COMPENSADOR 14x19x9 (deitado)`
  em vez de canaleta — mas **com** canaleta sob o peitoril. Confiança MÉDIA.

## Validação

ElementIds duplicados: 0 · UniqueIds duplicados: 0 · peças sem `Parede`: 0 ·
sem posição: 0 · sem bbox: 0 · sem nível: 0 · largura ≠ 14 cm: 0 · rotação não
múltipla de 90°: 0 · aberturas com peitoril sem solução abaixo: 0.
Duas aberturas têm rótulo `Parede` de outro nível (`7720857`, `7722851`) —
casadas geometricamente, não pelo rótulo.

Reconstruídas manualmente fiada a fiada: 2 portas (`6616539`, `6616547`),
2 janelas (`6588577`, `6589819`) e 1 exceção (`7719511`).

## Cobertura do catálogo atual do solver

**55.963 de 65.747 peças = 85,12%** (TORRE EASY: 80,19%) · **6 de 21 tipos =
28,57%**. A lacuna é inteiramente canaleta (13,58%), compensador deitado (0,96%)
e cortado (0,44%).

## Arquivos gerados

`docs/revit_reference_extraction/butanta-r08-lt/`

```
README.md
REPORT_HUMAN_REVIT_MODULATION.md
01_family_catalog.json … 10_torre_easy_comparison.json
_scripts/   (17 scripts: extração no Revit + análise local)
evidence/   (sólidos, busca de vergas, cobertura, contagem por família)
```

## Limitações

1. Aberturas dos pav. 3º–8º são **INFERIDAS** (justificadas pela identidade
   geométrica exata, marcadas com `propagated_from_opening_id`).
2. Vínculo canaleta ↔ graute **NÃO VERIFICADO** (885 `GRAUTE HORIZONTAL`
   existem, mas o pareamento não foi medido).
3. **760 canaletas (8,51%) sem contexto atribuído** — 522 são penúltima fiada
   de cinta dupla; 238 não explicadas.
4. Encontros **L/T/X não analisados** (fora do escopo desta missão).
5. Apoios medidos sobre a corrida contínua de canaleta; quando duas aberturas
   compartilham a faixa, o valor não é decisão isolada de projeto
   (filtrar por `run_reaches_wall_*`).

## Comparação com o TORRE EASY

Tabela completa na seção P do relatório e em `10_torre_easy_comparison.json`.
O RVT do TORRE EASY **não foi reaberto** — só foram usados fatos já versionados.

**O invariante**: apesar de sistemas de abertura opostos, os dois projetos
concordam em ausência de `Wall`/`Door`/`Window` nativos, `Parede` como chave,
`Título_abertura` como rótulo, offset 0,00 cm entre reforço e borda do vão,
grade de 20 cm, peça de 9 cm em meia fiada, 14 cm de espessura, ortogonalidade
total, bbox +2 cm e cinta de topo em ~72–74% das paredes.

> **A variável é o sistema de abertura; a gramática da modulação é a mesma.**
> Isso sustenta a arquitetura A/B pedida: não são dois motores, são **duas
> estratégias de preenchimento da fiada nas bordas do vão**.

## Próximos passos (nenhum autorizado ainda)

1. O Astra comparar os dois projetos e definir a arquitetura A/B do solver.
2. Decidir se `CANALETA*` entra no `BLOCK_FAMILY_CATALOG_DEFINITIONS`.
3. Decidir a política de apoio lateral (os dois projetos discordam).
4. Resolver o CONFLITO 10.7 (cinta de topo), agora com duas medições
   independentes convergindo em ~72–74% — predominante, não universal.

**Nada disso foi implementado. Esta missão é só extrair, medir, classificar,
comparar, validar e versionar.**
