# Catálogo de blocos

Fonte detalhada: `nuvem/REGRAS_MODULACAO_BLOCOS.md` §1, §2 (REGRAS §1/§2).
Implementação: `BLOCK_FAMILY_CATALOG_DEFINITIONS` / `load_fixed_block_
catalog` em `core/wall_modeling.py`.

## Regra de identificação

Família única "14x19", 6 peças, identificadas **automaticamente por
família+tipo exatos** — **nunca por comprimento deduzido**. Ao ler um
projeto novo via MCP, confirmar que essas famílias/tipos existem no
projeto antes de modular; nunca inventar peça equivalente.

## As 6 peças

| Código | Peça real (família/tipo) | Comprimento | Papel |
|---|---|---|---|
| B39 | BLOCO INTEIRO - 14x19x39 | 39cm | Peça padrão do preenchimento comum — sempre a primeira prioridade |
| B34 | BLOCO 34 - 14x19x34 | 34cm | Amarração especial (canto L, encontro T degradado) **e** preenchimento comum de meio de parede |
| B54 | BLOCO 54 - 14x19x54 | 54cm | Amarração especial (T verdadeiro, X) |
| B19 | MEIO BLOCO - 14x19x19 | 19cm | Meio-bloco — **último recurso**, só em ponta aberta |
| C09 | COMPENSADOR 14x19x9 | 9cm | Compensador — só quando necessário, nunca em sequência |
| C04 | PASTILHA - 14x19x4 | 4cm | Pastilha — mesma regra do compensador |

Todas as peças: largura 14cm, altura 19cm, origem local (0,0) = centro
geométrico do bloco.

- **B39 e B19**: célula simétrica.
- **B34 e B54**: célula **assimétrica** — têm um "vão menor" que precisa
  ficar posicionado/alinhado conforme a amarração (ver BONDING.md). Nunca
  tratar B34/B54 como peça simétrica.
- **C09 e C04**: maciços (sem célula), mas têm **orientação** (lado
  aberto / lado fechado) — ver BONDING.md, regra do compensador.

## Constantes geométricas

- `BLOCK_JOINT_CM = 1` — junta de assentamento entre blocos, e entre
  bloco e parede.
- `BLOCK_OPENING_JOINT_CM = 0` — junta entre bloco e abertura, ou entre
  bloco e ponta livre de parede sem amarração.
- `PIER_MODULE_CM = 5` — mdc de bloco+junta de todas as peças. Um trecho
  só fecha em blocos se seu comprimento (descontadas as juntas de
  contorno) for múltiplo de 5cm.
- Passo de fiada = `COURSE_JOINT_CM + altura do bloco` = **20cm** (19cm
  de bloco + 1cm de junta).
- Fiada 1 nasce em `base_z_abs + FIRST_COURSE_Z_OFFSET_CM` = **+1cm**
  acima da cota bruta do nível — **nunca em 0cm**. Fiada 2 → 21cm, Fiada 3
  → 41cm, etc. [REGRAS §8 — já inverteu 2x numa mesma sessão antiga; não
  alterar esta fórmula sem reconfirmar no Revit real primeiro].
- `course_index` na criação é a fiada **física** (par=A, ímpar=B) — cada
  índice só recebe candidatos da letra correspondente.

## Prioridade de preenchimento comum (trechos livres — meio de parede)

Implementada em `_pier_ordered_layout`. Ordem de tentativa, **a menor
alteração possível primeiro**, cada tier só tentado se o anterior não
fechar [REGRAS §2]:

1. Só B39.
2. 1 único B19 numa **ponta aberta** (abertura, ou extremidade de parede
   sem amarração) + resto em B39. Tenta a ponta de entrada primeiro,
   depois a de saída.
3. B39 + B34 (sem B19, sem compensador) — o B34 pode cair em qualquer
   posição do trecho, inclusive no meio.
4. 1 único B19 numa ponta aberta + resto em B39+B34.
5. 1 único B19 mesmo sem ponta aberta (ainda fecha com zero
   compensadores — prioridade maior que compensador).
6. B39(+B34) + no máximo 1 compensador/pastilha (`MAX_COMPENSATORS_
   PER_TRECHO = 1`).
7. Compensador acima do teto, só se for a única solução existente.
8. Último recurso irrestrito — nunca reporta "não modular" quando existe
   qualquer solução, mesmo feia.

> Nota de prioridade (2026-08-25): para trecho com as duas pontas
> fechadas (sem onde B19 encostar de verdade), o solver tenta
> compensador **antes** de B19 sem ponta aberta (inverteu a ordem antiga
> — ver ERROR_HISTORY.md). B19 sem ponta aberta é **últimíssimo** recurso.

## Regra do meio-bloco (B19) — resumo

- **Nunca no meio de um trecho**, em hipótese alguma — mesmo quando as
  duas pontas do trecho estão abertas. Só é solução de **fechamento**,
  nunca peça de preenchimento comum.
- Só pode encostar numa **ponta aberta de verdade**: vão de abertura, ou
  extremidade de parede sem amarração. Uma boneca/pilar de encontro
  (L/T/X) **não conta como ponta aberta**, mesmo degradada — ali a regra
  do B34 tem prioridade (ver BONDING.md).
- Rede de segurança independente na validação (`HALF_BLOCK_NEAR_TIE`) —
  ver VALIDATION.md.

## Regra dos compensadores/pastilhas (C09/C04) — resumo

- **Proibido usar 2 ou mais em sequência** no mesmo trecho.
- `MAX_COMPENSATORS_PER_TRECHO = 1`.
- São o último recurso por construção — nunca substituem B39/B34 quando
  eles fecham sozinhos.
- **Orientação obrigatória** (regra #3): o lado fechado do compensador
  tem que ficar voltado para a abertura, quando ele encosta numa de
  verdade — ver BONDING.md.

## Nunca fazer

- Nunca deduzir uma peça pelo comprimento (usar sempre família+tipo).
- Nunca usar peça especial (B19/C09/C04) como solução padrão para
  qualquer sobra.
- Nunca colocar B19 no meio de um trecho, mesmo com as duas pontas
  abertas.
- Nunca empilhar 2+ compensadores em sequência.
- Nunca alterar a fórmula de cota Z (fiada 1 / passo de 20cm) sem
  reconfirmar contra o Revit real primeiro.
