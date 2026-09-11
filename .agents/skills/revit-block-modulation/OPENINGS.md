# Aberturas — portas, janelas, pilaretes

Fonte detalhada: REGRAS §3, §4, §10, §18.2, §18.3.

## Zona de exclusão absoluta — porta sem peitoril (REGRAS §3)

Regra **absoluta**, sem exceção: nenhum bloco, compensador ou pastilha
pode invadir o vão real de uma porta sem peitoril (peitoril ≈ 0,
`DOOR_NO_SILL_MAX_SILL_CM = 1.0`).

- `find_door_void_violations` mede a sobreposição real (OBB) entre cada
  candidato de bloco e o vão real de cada porta sem peitoril — roda como
  rede de segurança explícita e geométrica, não confia só na lógica de
  fronteiras dos trechos.
- Qualquer violação **bloqueia a criação** dos blocos (mesmo mecanismo de
  gate que colisões) — nunca ignorada ou aplicada "mesmo assim".
- Janela (peitoril > 0 de verdade) não entra nesta regra — o vão dela só
  é excluído na faixa vertical real (abaixo).

## Janela não interrompe a fiada abaixo do peitoril (REGRAS §4)

Uma janela só é vazia **na faixa vertical real do seu vão** (`sill_z_abs`
até `head_z_abs`, lidos de `Peitoril`/`Altura_abertura` da família real).
Fiadas inteiramente abaixo do peitoril ou acima da verga continuam
**sólidas**, com blocos normais.

- `_opening_active_in_course_band` testa se o vão real de uma abertura
  aparece na faixa vertical de uma fiada física.
- `_group_course_indices_by_opening_band` agrupa as fiadas físicas pelo
  conjunto de aberturas ativas.
- `solve_building_blocks_all_courses` roda uma vez por grupo;
  `create_building_blocks(..., course_candidates=...)` faz cada fiada
  usar os candidatos da própria banda.
- Porta (peitoril ≈ 0) na prática cobre quase todas as fiadas do
  pé-direito — não é afetada por esta regra.

## Critério porta vs. janela (REGRAS §10.4 — REGRA OBRIGATÓRIA, implementada)

`detect_wall_openings_from_courses` classifica pela mesma regra usada
para validar contraverga:

- **Vão toca a fiada mais baixa do trecho** → porta. Nunca existe peça
  especial abaixo (nem canaleta, nem contraverga) — fisicamente não há
  alvenaria abaixo de uma porta pra vencer.
- **Vão não toca a base** → janela. Espera-se verga E contraverga (ou a
  sequência de canaleta equivalente, ver abaixo) tanto acima quanto
  abaixo, simetricamente.
- Um validador que exigisse contraverga em toda abertura estaria errado —
  a ausência só é erro quando o vão **não** toca a base.

## Vergas, contravergas e canaletas — dois sistemas, nunca misturados

**Status de implementação**: 10.1/10.4/10.5 implementados (leitura/
diagnóstico); 10.2/10.3/10.6/10.7 continuam só documentados — **não
implementar geração de geometria nova para eles sem primeiro reconfirmar
com mais projetos** (regra do próprio REGRAS: nada entra no script sem
estar documentado e confirmado antes).

- **Sistema 1 (convencional)**: famílias `VERGA JANELA` (acima do vão) e
  `CONTRAVERGA`/`CONTRAVERGA1` (abaixo).
- **Sistema 2 (canaleta)**: o vão é fechado por sequência de fiadas
  especiais em bloco-canaleta, sem nenhuma instância de verga/contraverga
  dedicada.
- **REGRA OBRIGATÓRIA**: nunca aplicar os dois sistemas no mesmo
  trecho/nível automaticamente — a escolha é config explícita (por nível
  ou projeto), nunca inferida silenciosamente peça a peça. Um projeto
  pode ter os dois, mas segregados (ex.: térreo = Sistema 1, tipos =
  Sistema 2).
- **Sistema 2, sequência observada** (PADRÃO OBSERVADO, só 2 exemplos —
  não tratar a proporção exata como travada até medir mais casos):
  1. Fiada fina 9cm (`CORTADO`) só nas duas jambas.
  2. Fiada fina 9cm (`CORTADO`) cheia, jamba a jamba.
  3. Fiada de canaleta (`CANALETA J`/`CANALETA 34`/`CANALETA INTEIRA`/
     `MEIA CANALETA`, conforme largura restante), também cheia — a verga
     estrutural.
  Um bloco `CORTADO` achado assim perto de um vão **não é erro de
  modulação** — é apoio de verga correto.
- **Comprimento de apoio** (PADRÃO OBSERVADO, 1 exemplo): a canaleta se
  estende além das duas jambas, apoiando na alvenaria sólida adjacente —
  não cortar o trecho de canaleta exatamente na largura do vão.
- **CONFLITO ABERTO (10.7)**: "toda parede tem canaleta na última fiada do
  topo" — só 39,4% (87/221) das linhas medidas confirmam; há contraexemplo
  grande (51 peças, zero canaleta). **Não implementar nenhum dos dois
  lados** até investigar (ver ERROR_HISTORY.md).

## Blocos cortados perto de aberturas não são erro por padrão (REGRAS §10.5, implementada)

65% dos blocos `CORTADO` amostrados ficam a menos de 60cm de uma jamba de
vão (40% encostam, <25cm) — concentração real, não aleatória. Antes de
reportar um bloco cortado como suspeito, verificar se está perto de uma
jamba de abertura (ou de um encontro L/T/X) — só reportar como erro
genuíno quando não houver justificativa geométrica próxima
(`is_cut_block_justified_by_opening`).

## Alinhamento obrigatório de faces (REGRAS §18.3)

**REGRA OBRIGATÓRIA**: as faces dos blocos devem coincidir exatamente com
(1) a face lateral das aberturas, (2) o fim das paredes, (3) as faces
definidas pelos encontros. Proibido bloco ultrapassando a face do vão,
terminando antes dela, ou com desalinhamento pequeno na extremidade — a
modulação junto de abertura parte sempre dos limites geométricos exatos
dela.

## Pilaretes — tratamento independente (REGRAS §18.2)

**Status: pendência de código aberta.** O trecho entre duas aberturas tem
que ser resolvido **por si**, não como sobra do prisma geral da parede:

1. Tentar modular o pilarete como está primeiro (ex.: B39 + C09 com as
   juntas).
2. Só se faltar pouco, considerar deslocar uma das aberturas adjacentes
   dentro da tolerância (ex.: ~1cm) para viabilizar a modulação.
3. Nunca deixar o pilarete sem modulação só porque a posição original da
   abertura não fecha.

`plan_axis_opening_fix` (RULES.md/VALIDATION.md, ajuste geométrico) já
sabe deslocar abertura, mas hoje só é acionado quando o eixo inteiro
falha — não a partir do pilarete individual. Ao implementar essa
pendência, reaproveitar a mesma hierarquia boneca→shift→trim→widen já
existente, nunca inventar uma nova.

## Nunca fazer

- Nunca gerar bloco dentro do vão real de uma porta sem peitoril — bloqueio
  absoluto, sem exceção.
- Nunca misturar Sistema 1 e Sistema 2 de verga/contraverga/canaleta no
  mesmo trecho ou nível.
- Nunca implementar 10.2/10.3/10.6/10.7 (sequência exata, comprimento de
  apoio, valor de desencontro, canaleta no topo) como se já fossem regra
  confirmada — checar ERROR_HISTORY.md primeiro.
- Nunca reportar bloco `CORTADO` como erro sem checar proximidade de
  abertura/encontro.
- Nunca deixar pilarete sem modulação por não ter tentado a combinação
  local antes de desistir.
