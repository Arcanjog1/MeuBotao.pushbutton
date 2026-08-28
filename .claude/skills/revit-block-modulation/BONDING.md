# Amarração — o núcleo do sistema

> Pedido explícito do usuário (`CLAUDE.md`, 2026-08-28): a amarração é o
> que diferencia uma parede de alvenaria **estrutural** de um empilhamento
> de blocos. Todo conhecimento novo sobre amarração é registro
> obrigatório em `nuvem/REGRAS_MODULACAO_BLOCOS.md` (REGRAS), antes ou
> junto da implementação — nunca depois.

Fonte detalhada: REGRAS §5 (encontros L/T/X), §6 (limitações), §11
(alinhamento vertical, regra #1), §12 (orientação de compensador, regra
#3), §18.1/§18.5/§18.6/§18.7/§18.9 (revisão geral 2026-08-28).

## Tipos de encontro

Identificados no grafo de encontros do projeto: `L_CORNER`, `T_
INTERSECTION`, `X_INTERSECTION`, `FREE_END` (ponta livre), `STRAIGHT_
CONTINUATION` (continuação reta — não é amarração especial, sem reserva
de espaço), `AMBIGUOUS` (3+ pontas no mesmo ponto — comum quando peitoril
e verga da mesma parede ocupam o mesmo eixo em planta em faixas de altura
diferentes; **continua reservando espaço**, porque ali existe peça de
verdade na outra faixa — REGRAS §11.9, §15.2).

## L_CORNER (`solve_l_corner`)

- **Sempre B34** nas duas fiadas, um por parede, com a ponta do **vão
  menor** encostada no nó.
- Ponto de contato = `arm_point`: a ponta da parede estendida até a face
  oposta da parede perpendicular — **nunca** o centro geométrico do nó
  (deixaria meia espessura do canto vazia).
- **Prova geométrica obrigatória** (`validate_l_corner`): os vãos MENORES
  das duas fiadas devem ficar **sobrepostos em projeção XY** — é isso que
  trava o canto de verdade.

## T_INTERSECTION (`solve_t_intersection`) — 3 níveis, nunca força a peça errada

**Nunca força B54/B34 só porque o nó foi identificado como T** — primeiro
verifica se há espaço físico real:

- `T_INTERSECTION_B54_HALF_ROOM_FT` = 27cm (metade do B54), necessário
  **dos dois lados** do nó na parede principal, sem invadir abertura.
- `CORNER_B34_ROOM_FT` = 34cm, necessário na boneca (parede que chega),
  no sentido que se afasta do nó.

**Nível 1 — T verdadeiro**: cabe → B54 centrado no nó (parede principal) +
B34 na boneca, célula central do B54 alinhada com o vão menor do B34.

**Nível 2 — degrada para L com boneca**: não cabe o T, mas a boneca tem
34cm **e** a parede principal tem 34cm em pelo menos um dos dois sentidos
→ vira canto em L na prática: B34 na parede principal (esticando só para
o lado com espaço) + B34 na boneca. **Amarração em L usa sempre o bloco
de 34** — nunca peça menor quando o B34 cabe. Mesma prova geométrica do
L_CORNER.

**Nível 3 — 1 único elemento na boneca**: nem o B34 cabe na boneca → 1
único compensador ou pastilha fecha a boneca sozinho (**nunca B19** — a
boneca continua sendo amarração, não ponta livre), **sem peça na parede
principal** (o preenchimento comum dela cuida do resto, reservando só
meia espessura da parede mais larga do nó).

**Sem solução**: nem o C04 (4cm) cabe → nó reportado em `intersection_
failures`, nunca inventa peça. Precisa de ajuste de geometria.

**T sem espaço = reinterpretação em L, não degradação** (REGRAS §18.9,
pedido explícito do usuário 2026-08-28): quando a boneca de um T não tem
comprimento pro B54, a leitura correta é "isso é um L usando C09/C04",
não "T degradado". Nunca forçar B54, nunca sobrepor, nunca deixar sem
modulação.

## X_INTERSECTION (`solve_x_intersection`)

Dois B54 a 90°, ambos centrados no ponto do nó, **células centrais
alinhadas** (`validate_x_intersection`). Cobre cruzamento no meio de duas
paredes contínuas e o caso raro de 4 pontas coincidindo. Não pode existir
peça adicional ocupando o mesmo volume (REGRAS §18.1/§18.7).

## Regra #1 — alinhamento vertical obrigatório entre fiadas

> Pedido explícito do usuário: "a junta vertical de uma fiada não pode
> coincidir com a junta vertical da fiada imediatamente acima ou abaixo,
> em hipótese alguma... tem prioridade sobre qualquer tentativa de
> simplesmente preencher o comprimento da parede... não pode ser
> flexibilizada."

- Obrigatória e **bloqueante** — `validate_wall_modulation` reprova
  (`sem_alinhamento_vertical`) e dispara ajuste geométrico automático
  (Etapa 3B) quando uma composição não consegue desencontrar a junta.
- Critério de busca: `(coincidência_de_junta, -alinhamento_de_vazio)` —
  coincidência de junta é o critério **primário/absoluto**; alinhamento
  de vazio só desempata entre candidatos que já têm zero coincidência.
- **Prova de que sempre existe alternativa** para um trecho fechado dos
  dois lados que fecha como múltiplo exato de B39: 1 B34 no início + resto
  em B39 sempre sobra exatamente 5cm = 1 C04 — fecha para qualquer
  comprimento ≥40cm com 1 B34 + 1 C04, dentro do teto de 1 compensador.
- **EXCEÇÃO PERMITIDA (11.8, 2026-08-28)**: a junta que separa uma
  **pastilha (C04)**, **compensador (C09)** ou **meio-bloco (B19)** do seu
  vizinho **pode coincidir** entre Fiada A e Fiada B **quando essa peça
  encosta num vão** (borda de abertura deste eixo, ou ponta do próprio
  eixo). Motivo: são peças de ajuste do fechamento contra o vão, não do
  corpo da parede — a junta corrida que a regra #1 combate é a do corpo.
  **A exceção vale só na validação, nunca na busca** — o solver continua
  preferindo desencontrar de verdade quando existe alternativa; a exceção
  só evita reprovar quando não existe.
- **Limitação conhecida**: B34 de meio-de-parede (preenchimento comum
  fora de L/T/X) ainda **não** alinha o vão menor entre Fiada A e Fiada B
  — orientação fixa, não otimizada por alinhamento cruzado (diferente do
  L_CORNER/T degradado, onde o alinhamento É garantido e validado).

## Regra #2 — meio-bloco nunca perto de amarração

Duas redes de segurança independentes:

1. Na geração: `_merge_adjacent_compensator_pairs` só funde um par de
   compensadores em B19 quando o par está numa das duas PONTAS do trecho
   **e** aquele lado é ponta aberta de verdade — nunca no meio, mesmo com
   as duas pontas do trecho abertas.
2. Na validação: `audit_wall_bond_quality` confere de novo, a partir da
   posição REAL de cada B19 já lançado, se ele está perto de uma
   amarração (nó L/T/X, ponta ou meio de parede) — bloqueia a criação se
   estiver (`HALF_BLOCK_NEAR_TIE`).

**Regra #2 tem prioridade sobre o desencontro de junta** (REGRAS §16):
o `_score` da busca de desencontro é `(excesso_de_compensadores_em_
sequência, coincidência_de_junta, -alinhamento_de_vazio)` — nunca trocar
uma junta coincidente (que só escala para ajuste geométrico) por uma
parede reprovada por compensadores em sequência.

## Regra #3 — orientação dos compensadores

> Pedido explícito: "o compensador possui um lado aberto e um lado
> fechado... o lado fechado deve estar sempre voltado para a
> abertura... a orientação deve ser determinada automaticamente... o
> algoritmo também deve validar e corrigir automaticamente qualquer um
> que esteja invertido."

- `orient_compensator_candidates` roda **depois** de todo o preenchimento
  comum, como passo dedicado de validação+correção — sempre recalcula do
  zero se o compensador encosta numa abertura de verdade e em qual lado,
  e corrige `mirrored` mesmo que já tivesse valor de rodada anterior.
- Só compensador **encostado de verdade** numa abertura (sem junta de
  argamassa) recebe orientação exigida; longe de abertura fica
  `mirrored=False`.
- ⚠️ Premissa física (`COMPENSATOR_CLOSED_SIDE_IS_PLUS_X_WHEN_UNMIRRORED`)
  **não confirmada contra a família real** — se a orientação sair
  invertida num projeto real, é uma constante a trocar, não um redesenho.

## Padronização entre fiadas (REGRAS §18.4)

Fiada 1 ≡ Fiada 3 ≡ Fiada 5…, Fiada 2 ≡ Fiada 4 ≡ Fiada 6… — dois padrões
alternados (A e B), repetidos até o topo. **Orientação mais recente do
usuário tem prioridade** sobre a tentativa antiga de variar entre fiadas
de mesma paridade (`PIER_LAYOUT_VARIANTS_PER_COURSE`) — o padrão deve
repetir, não inventar uma solução diferente por fiada sem uma razão
geométrica (abertura naquela faixa vertical).

## Transição B34 → B39 exige olhar a fiada seguinte (REGRAS §18.6)

**Pendência de código aberta.** A troca de B34 para B39 só pode acontecer
quando a fiada seguinte tiver vão suficiente pro B39 encaixar mantendo a
continuidade do prisma: ler posição do B34 na fiada atual → analisar a
fiada seguinte → verificar o vão → só então permitir a transição.

## Colisão entre blocos (REGRAS §18.7)

**Regra obrigatória**: nenhum bloco pode ser inserido dentro do volume de
outro. A única sobreposição legítima é a prevista pelas regras de
amarração (peças de fiadas diferentes). Medir sempre com **OBB (SAT)**,
nunca bounding box alinhado aos eixos (AABB superestima muito em parede
diagonal/rotacionada — chegou a acusar 10.319 pares falsos contra ~9
reais por fiada).

## Nunca fazer

- Nunca amarração incompleta ou blocos só encostados visualmente.
- Nunca forçar B54 quando a boneca não tem espaço — reinterpretar como L.
- Nunca deixar peça de amarração sobreposta a outra peça no mesmo volume.
- Nunca alterar apenas parte da parede numa correção — a parede é um
  sistema completo: se um trecho desloca, encontros e fiadas vizinhas
  recalculam junto.
- Nunca inventar orientação de compensador sem checar se ele encosta
  numa abertura de verdade.
