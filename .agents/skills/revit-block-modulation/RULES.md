# Fluxo de execução e princípios permanentes

Fonte detalhada: `nuvem/REGRAS_MODULACAO_BLOCOS.md` (REGRAS) — seções
citadas entre colchetes. Este arquivo é o resumo operacional: "o que
fazer, em que ordem, e o que nunca fazer", não a explicação completa de
cada regra (isso está em BONDING.md/OPENINGS.md/VALIDATION.md).

## Princípios permanentes (nunca flexibilizar sem pedido explícito do usuário)

1. **Paramétrico, nunca hardcoded.** Nenhuma regra desta Skill depende de
   coordenadas fixas de um projeto. O sistema sempre analisa o projeto
   atual (paredes, comprimentos, direções, interseções, aberturas,
   pilaretes, níveis) e resolve a modulação a partir dessa geometria real
   [REGRAS §14.3 — hoje a criação de parede via CAD não é
   modulation-aware ainda; a modulação em si sempre foi paramétrica].
2. **Catálogo fechado.** Nunca inventar bloco ou dimensão — usar
   exclusivamente as peças definidas em BLOCKS.md / `BLOCK_FAMILY_
   CATALOG_DEFINITIONS`, identificadas por família+tipo exatos, nunca por
   comprimento deduzido [REGRAS §1].
3. **Amarração nunca é sacrificada por preenchimento.** Ordem de
   prioridade definida pelo usuário quando a situação é difícil
   [REGRAS §18.10]:
   1. Manter as amarrações corretas.
   2. Garantir a modulação completa (toda parede/pilarete/boneca/trecho).
   3. Manter o padrão entre fiadas (ímpares entre si, pares entre si).
   4. Alinhar faces (portas, aberturas, finais de parede, encontros).
   5. Ajustar aberturas quando permitido, dentro da tolerância.
   6. Evitar soluções improvisadas — nunca bloco aleatório só pra fechar
      um vão pequeno.
4. **Peças especiais são último recurso**, nunca solução padrão para
   qualquer sobra — ver BLOCKS.md/BONDING.md (regra do meio-bloco e dos
   compensadores) [REGRAS §2].
5. **Nunca modular sobre uma abertura** — ver OPENINGS.md [REGRAS §3, §4].
6. **Nenhum ajuste geométrico aumenta o comprimento total de um eixo** —
   a prioridade é sempre preservar a geometria/comprimento vindos do CAD;
   ajuste é sempre o menor possível e em cascata (boneca → shift → trim →
   widen), nunca aplicado sem que o solver real confirme que fecha
   [REGRAS §7].
7. **Nenhuma correção fica só no exemplo específico.** Todo erro apontado
   pelo usuário vira regra geral + validação automática, nunca só um
   "conserto visual" daquele caso — ver SKILL.md "Como esta Skill
   aprende" e ERROR_HISTORY.md [REGRAS §18, preâmbulo].
8. **Nenhuma parede fica sem modulação sem motivo registrado** — todo
   trecho recebe um de três estados (modulado / precisa ajuste
   geométrico / não modulável com motivo exato) [REGRAS §18.8].

## Fluxo obrigatório — 6 etapas

### Etapa 1 — Carregar a Skill

Antes de qualquer modelagem, carregar (ler) o que for relevante ao
pedido:

- RULES.md (este arquivo) — sempre.
- BLOCKS.md — catálogo de blocos.
- BONDING.md — regras de amarração (sempre que houver encontro L/T/X, ou
  preenchimento comum de meio de parede).
- OPENINGS.md — sempre que houver porta/janela/pilarete envolvido.
- VALIDATION.md — sempre, antes de considerar qualquer modulação
  concluída.
- ERROR_HISTORY.md — para não repetir um bug/conflito já mapeado.

### Etapa 2 — Ler o projeto no Revit (MCP + pyRevit)

Via `mcp__revit-pyrevit__*` (ou equivalente disponível na sessão):

- identificar paredes, níveis, aberturas, interseções;
- identificar a geometria real do projeto (comprimentos, direções,
  ângulos dos encontros);
- identificar as famílias de blocos disponíveis **no projeto real** —
  nunca assumir que o catálogo fixo de BLOCKS.md está presente sem
  confirmar; se divergir, registrar a divergência (não modular com peça
  inexistente).
- **Não assumir que o novo projeto tem a mesma arquitetura do anterior.**

### Etapa 3 — Analisar antes de modelar

Antes de criar qualquer bloco:

- classificar as paredes e seus encontros (L/T/X, ponta livre,
  continuação reta, ambíguo — ver BONDING.md);
- identificar regiões críticas: pilaretes, bonecas, trechos curtos perto
  de encontros, aberturas;
- calcular possibilidades de modulação (prioridade de preenchimento —
  BLOCKS.md/BONDING.md);
- resolver amarrações e aberturas **antes** de gerar geometria;
- definir a estratégia de cada parede/trecho.

Nunca começar simplesmente colocando blocos sequencialmente sem essa
análise prévia.

### Etapa 4 — Gerar a modulação

Só depois da solução geométrica validada logicamente:

- gerar os blocos, posicionando corretamente cada família;
- respeitar níveis e cota Z (fiada 1 = `base_z_abs + 1cm`; passo de fiada
  = 20cm — ver BLOCKS.md) [REGRAS §8];
- respeitar a alternância de fiadas físicas (par=A, ímpar=B — cada índice
  só recebe candidatos da própria letra) [REGRAS §8];
- respeitar aberturas (nunca bloco dentro do vão real — OPENINGS.md);
- aplicar amarrações (BONDING.md).

"Lançar Blocos - criar" deve ser idempotente: cada execução substitui
atomicamente o lote anterior daquele conjunto de paredes, nunca soma um
segundo lote por cima [REGRAS §13.4 — bug real já corrigido, não
reintroduzir].

### Etapa 5 — Validação automática

Rodar a auditoria completa descrita em VALIDATION.md. Nenhuma modulação é
considerada concluída só porque os blocos foram posicionados.

### Etapa 6 — Corrigir automaticamente e revalidar

Se a validação encontrar erro:

1. identificar a causa (não só reposicionar o bloco isolado — ver
   princípio "alinhamento global" em VALIDATION.md: mover blocos isolados
   para resolver um problema pontual é proibido);
2. recalcular a solução para a parede/trecho inteiro (nunca só a peça que
   falhou);
3. corrigir;
4. rodar a validação de novo.

O processo só termina quando a solução atende a todas as regras — ou
quando a parede é marcada explicitamente como não modulável, com o motivo
exato [REGRAS §18.8], nunca por omissão silenciosa.

### Modelador externo — mesma entrada do solver [REGRAS §21]

Para uma captura de Walls no modelador externo, a calculadora deve chamar o
mesmo `solve_building_blocks` do `core.engine.wall_stepper`; ela não pode
reimplementar uma regra de preenchimento, amarração ou validação na UI. A
edição descobre a componente L/T/X e recalcula somente as faixas de
`(nível, base_z)` atingidas, preservando resultados independentes. A prévia
durante arraste é descartável; ao soltar, o solve e a validação canônicos são
executados novamente antes de aplicar qualquer bloco.

## Testes

Antes de considerar qualquer alteração de lógica de modulação pronta,
rodar `python3 -m pytest tests/test_script.py -q` (regra de merge direto
já definida em `CLAUDE.md`). `tests/run_tests.py` cobre as regras
puramente geométricas/aritméticas fora do Revit; comportamento que só
existe ao vivo no Revit (criação real de instância, `MirrorElement`, etc.)
só é verificável via MCP [REGRAS §9].
