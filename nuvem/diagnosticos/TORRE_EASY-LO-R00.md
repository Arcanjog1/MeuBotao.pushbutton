# Diagnóstico — TORRE EASY-LO-R00 (JARDIM DA COSTA BEACH CLUB)

> Registro bruto de UM projeto, gerado via `mcp__revit-pyrevit__*` seguindo
> [diagnostico_modulacao_cross_projeto.py](../diagnostico_modulacao_cross_projeto.py)
> e o plano `estou-quero-fazer-isso-wild-stardust.md`. 100% leitura — nenhuma
> `Transaction` foi aberta neste documento, nenhum `save_document`/
> `sync_with_central` foi chamado. Isto é insumo bruto; nada aqui vira
> "padrão de escritório" sozinho — ver [PADRAO_MODULACAO.md](../PADRAO_MODULACAO.md).

- **Documento**: `TORRE EASY-LO-R00.rvt`, Revit 2026.3
- **Projeto**: JARDIM DA COSTA BEACH CLUB
- **Estado do modelo**: paredes/portas/janelas nativas do Revit já **excluídas**
  (Walls=0, Doors=0, Windows=0) — o modelo só tem a alvenaria em blocos,
  batendo com o fluxo final já definido (paredes → revisão → blocos →
  excluir paredes).
- **21 níveis** ("01. TER" a "21. COB"), 9 modelos vinculados (3 IFC, 6 .rvt
  de estrutura/laje — não inspecionados, não é onde a alvenaria vive).
- **67.712 instâncias** de "Modelos Genéricos", **57 Types distintos**
  (medido em 24/08/2026).

## Catálogo (núcleo já conhecido — bate 100% com REGRAS_MODULACAO_BLOCOS.md)

| Peça | Instâncias (soma de todos os Types com esse nome) | Dimensões L×A×larg (cm) | Células |
|---|---|---|---|
| BLOCO INTEIRO 39 | 27.412 | 39×19×14 | 2 simétricas, 15,75×9,0 cada |
| BLOCO 34 | 16.353 | 34×19×14 | 2 assimétricas: 10,75×9,0 (menor) / 15,75×9,0 |
| MEIO BLOCO 19 | 4.689 | 19×19×14 | 1, 14,0×9,0 |
| COMPENSADOR 9 | 2.994 | 9×19×14 | 0 (maciço) |
| BLOCO 54 | 2.496 | 54×19×14 | 3: 15,75×9,0 / **12,5×9,0 (central)** / 15,75×9,0 |
| PASTILHA 4 | 2.475 | 4×19×14 | 0 (maciço) |

Extração de célula por `EdgeLoops` da face plana horizontal de maior área
(mesmo método de `_extract_block_cells_local_from_symbol`, adaptado para
rodar sobre instância já colocada em vez de `FamilySymbol` ativado — evita
qualquer `Transaction`/`Activate()` em arquivo de terceiro).

## Peças extras (NÃO estão no catálogo fixo do script hoje)

`CANALETA INTEIRA` (2.262), `CANALETA J` (19/29cm alt., ~2.5k), `CANALETA 34`
(1.254), `MEIA CANALETA` (376), variantes **`CORTADO`** (altura 9cm em vez
de 19 — ~2,5k no total), variantes **`(deitado)`** do compensador (~450,
parece o mesmo peça física rotacionada 90°), `VERGA JANELA` (379 em 13
Types) e `CONTRAVERGA`/`CONTRAVERGA1` (~120 em 7 Types) — estas duas
últimas **sem** `Comprimento_bloco`/`Altura_bloco`/`Largura_bloco`
preenchidos, não medidas. Extração de célula das canaletas voltou vazia
(0 loops na face de maior área) — não investigado a fundo (não bloqueante).

## Regras geométricas medidas

- **Junta de assentamento = 1,0cm**: 1.856 de 2.135 pares de BLOCO 39
  adjacentes medidos (87%) — o resto é ruído do método de agrupamento
  (pega blocos não realmente contíguos). Confirma `BLOCK_JOINT_CM=1`.
- **Passo de fiada = 20cm**: delta mais comum (101 ocorrências) entre
  cotas Z distintas de blocos, em 209 cotas distintas no prédio inteiro.
  Confirma "altura do bloco (19) + junta (1)".
- **Offset da 1ª fiada = +1cm**: 19 pares de cotas Z separadas por
  exatamente 1,0cm (perto do nº de níveis do prédio, 21) — consistente
  com "1ª fiada nasce em base_z+1cm", repetido por nível.
- **Regra de dígito final da parede/pilarete**: reconstruindo 418 trechos
  reais (≥3 blocos contíguos, 6 fiadas populadas testadas) a partir do
  layout de blocos, **29% terminam em dígito "4"** — que a regra antiga
  (`0/1/6/9`) rejeitaria como não-modular, mas são trechos genuinamente
  fechados (construídos só com peças reais + juntas de 1cm medidas). Isso
  é evidência real a favor de já ter sido correto abandonar a regra de
  dígito (decisão tomada em 2026-08-21, ver `REGRAS_MODULACAO_BLOCOS.md`
  seção 1). **Ressalva metodológica**: o teste "aritmética mod 5" que rodei
  em cima disso é **tautológico** (toda peça do catálogo já é ≡4 mod 5, e
  1cm de junta preserva essa classe — qualquer trecho reconstruído SÓ com
  peças+juntas internas vai bater ≡4 mod 5 por definição, isso não valida
  nem invalida a regra de fronteira 1+1/1+0/0+0 descrita na seção 1 do
  REGRAS_MODULACAO_BLOCOS.md, que depende da junta de CONTORNO, não medida
  aqui). Não tratar o "92%" como confirmação da regra de fronteira.

## Pendências desta sessão (não bloqueantes, próxima vez que voltar aqui)

1. Célula das canaletas (CANALETA INTEIRA/J/34, MEIA CANALETA) não extraída.
2. VERGA JANELA/CONTRAVERGA/CONTRAVERGA1 sem parâmetro de dimensão
   identificado — ignorado a pedido do usuário nesta sessão.
3. Junta de contorno real (bloco↔parede/nó, não bloco↔bloco) não medida —
   precisaria localizar encontros L/T/X pelo padrão B34/B54 e medir a
   partir deles, não feito ainda.
4. Órfãos de duplicidade: vários Types com o mesmo nome de família (ex.
   VERGA JANELA em 13 Types) — não investigado se é intencional (1 tipo
   por vão) ou família duplicada entre os 9 vínculos.
