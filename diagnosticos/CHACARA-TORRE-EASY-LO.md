# Diagnóstico — CHACARA-TORRE EASY-LO ("TROPICALE BEACH CLUB")

> Registro bruto de um **segundo projeto**, distinto de
> [TORRE_EASY-LO-R00](TORRE_EASY-LO-R00.md) (apesar do nome de arquivo parecido, o
> usuário confirmou que são projetos diferentes — ver `PADRAO_MODULACAO.md`).
> Gerado via `mcp__revit-pyrevit__execute_revit_code`, seguindo o mesmo método de
> [diagnostico_modulacao_cross_projeto.py](../diagnostico_modulacao_cross_projeto.py)
> (100% leitura — nenhuma `Transaction` foi aberta, nenhum `save_document`/
> `sync_with_central` foi chamado; documento já estava aberto pelo usuário, não foi
> aberto/fechado por esta sessão).

- **Documento**: `CHACARA-TORRE EASY-LO`, Revit 2026
- **Nome de projeto (campo do Revit)**: "TROPICALE BEACH CLUB" (número/cliente vazios
  — parecem placeholder, não confiar neles como identificador)
- **Estado do modelo**: paredes/portas/janelas nativas já **excluídas** (`Walls`=0,
  `Doors`+`Windows`=0) — mesmo padrão de fluxo já visto em TORRE_EASY-LO-R00 (paredes
  → revisão → blocos → excluir paredes).
- **22 níveis** ("00. FUN" a "21. COB"). Pé-direito: **51cm** entre "00. FUN" e
  "01. TER" (térreo elevado sobre a fundação), depois **271cm** constante em todos os
  20 pavimentos-tipo seguintes.

## Catálogo (núcleo confirmado — bate 100% com REGRAS_MODULACAO_BLOCOS.md e com
## TORRE_EASY-LO-R00)

| Peça | Família | Dimensões L×A×larg (cm) | Instâncias (soma de todos os Types) |
|---|---|---|---|
| B39 | BLOCO INTEIRO - 14x19x39 | 39×19×14 | 32.692 + 908 (Type extra) = 33.600 |
| B34 | BLOCO 34 - 14x19x34 | 34×19×14 | 19.304 + 698 = 20.002 |
| B19 | MEIO BLOCO - 14x19x19 | 19×19×14 | 4.739 + 800 = 5.539 |
| C09 | COMPENSADOR 14x19x9 | 9×19×14 | 3.631 + 48 = 3.679 |
| B54 | BLOCO 54 - 14x19x54 | 54×19×14 | 3.098 + 12 = 3.110 |
| C04 | PASTILHA - 14x19X4 | 4×19×14 | 2.985 + 96 = 3.081 |

Dimensões idênticas, nome de família idêntico, papel idêntico ao catálogo fixo já
documentado (seção 1 de `REGRAS_MODULACAO_BLOCOS.md`) — **primeira confirmação
cross-projeto real** do catálogo núcleo.

## Peças extras (mesma família de "fora do catálogo fixo" já vista no projeto 1)

`CANALETA INTEIRA` (2.677), `CANALETA J` (dois sub-tipos, 19/29cm alt., ~3.1k),
`CANALETA 34` (1.483), `MEIA CANALETA` (432), variantes **CORTADO** (altura 9 em vez
de 19 — B39/B34/B19/B54/compensador cortados, ~3,3k no total), variantes
**"(deitado)"** do compensador (~560, mesma peça rotacionada 90°, igual ao já visto),
e uma variante nova não vista no projeto 1: **"COMPENSADOR CORTADO"**/**"PASTILHA
CORTADA"** (compensador/pastilha cortados, altura 9) — extensão natural do padrão
CORTADO já confirmado, agora também presente nas peças pequenas de ajuste.

## Regras geométricas medidas — CONFIRMAÇÃO CROSS-PROJETO

| Regra | Medido no projeto 1 (TORRE_EASY-LO-R00) | Medido aqui (projeto 2) | Confirma? |
|---|---|---|---|
| Passo de fiada = 20cm | 101 ocorrências (delta mais comum) | Medido diretamente nas cotas Z de 20.001 instâncias de B39: sequência 612,632,652,...,832,852 — **delta constante de 20cm** em praticamente toda a amostra | ✅ **CONFIRMADO EM 2 PROJETOS DISTINTOS** |
| Offset da 1ª fiada = +1cm sobre a cota bruta do nível | 19 pares de cotas Z separadas por 1,0cm | Offset de cada instância de bloco (B39/B34/B19/C09/B54) em relação ao nível mais próximo abaixo, amostra de 15.000: **offset=1,0cm foi o mais frequente (1.482 ocorrências)**, seguido exatamente por 21,0 / 41,0 / 61,0 / 81,0 / 101,0 / 121,0 / 141,0 / 161,0 / 181,0 / 201,0 / 221,0 (progressão aritmética de passo 20, fiadas 1 a 12) | ✅ **CONFIRMADO EM 2 PROJETOS DISTINTOS** — a progressão completa 1,21,41...221 é uma prova mais forte que a do projeto 1 (que só tinha visto o par 1cm isolado) |
| Catálogo núcleo (B39/B34/B54/B19/C09/C04): mesma família, mesmas dimensões | Confirmado | Confirmado (tabela acima) | ✅ **CONFIRMADO EM 2 PROJETOS DISTINTOS** |
| Walls/Doors/Windows nativos excluídos antes da fase de blocos (fluxo "paredes→blocos→excluir paredes") | Confirmado (Walls=0, Doors=0, Windows=0) | Confirmado (Walls=0, Doors=0, Windows=0) | ✅ Padrão de fluxo de trabalho, não regra geométrica — mas confirma que os dois projetos seguem o mesmo processo operacional |

## Padrão observado, ainda não confirmado (só neste projeto)

- **Última fiada de cada pavimento não fecha em múltiplo exato de 20cm**: nos dois
  trechos de amostra medidos (fim do pavimento térreo: ...812,832,852,**863**; fim de
  outro pavimento: ...1645,1665,**1676**), a fiada mais alta de cada pavimento aparece
  a **+11cm** da última fiada "redonda" (852+11=863; 1665+11=1676), antes de saltar
  para o próximo pavimento. Consistente com o pé-direito real (271cm) não ser múltiplo
  exato de 20cm — a última fiada é comprimida/ajustada para fechar sob a laje. **Não
  investigado a fundo** (só 2 ocorrências vistas de relance, sem isolar se é sempre
  +11 ou varia por pavimento) — candidato a virar regra sobre "ajuste da fiada de topo
  antes da laje", mas precisa de mais medição antes de generalizar o valor exato.

## Pendências desta sessão (não bloqueantes)

1. Célula das canaletas/vergas/contravergas não extraída aqui (mesmo bloqueio já visto
   no projeto 1 — a extração de `EdgeLoops` da face superior via
   `mcp__revit-pyrevit__execute_revit_code` deu erro `"Multiple targets could match:
   ElementId(BuiltInParameter)..."` em 100% dos 36 tipos candidatos — parece um
   problema de resolução de overload do `DB.ElementId(...)` no ambiente de execução
   deste MCP especificamente, não visto da mesma forma no projeto 1; não bloqueante
   porque a dimensão em cm (via parâmetros `Comprimento_bloco`/`Altura_bloco`/
   `Largura_bloco`) já veio de outra fonte e bateu 100% com o catálogo conhecido).
2. Junta de assentamento (bloco↔bloco) não remedida aqui por coordenada X (o projeto 1
   já tem essa medição com boa amostra, 87% de 2.135 pares em 1,0cm — não repetido
   aqui para não gastar mais chamadas MCP com baixo retorno marginal).
3. Regra de dígito final de trecho/pilarete: não remedida aqui (já teve ressalva
   metodológica registrada no projeto 1 — teste tautológico; precisaria da junta de
   CONTORNO real, não medida em nenhum dos dois projetos ainda).
4. Orientação de B34/B54 em encontros L/T/X: não verificada geometricamente aqui
   (precisaria reconstruir a topologia de nós a partir das posições XY, não feito
   nesta sessão).
