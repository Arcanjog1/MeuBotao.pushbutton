# Comparação solver × projeto humano BUTANTÃ R08_LT (1º PAV) via MCP

```json
{
  "date": "2026-09-10",
  "scope": "historical",
  "branch": "claude/revit-scale-autofix",
  "base": "41086e43b6b56102ce736b816debad04749fa4bf",
  "main_observada": "21576ee3d0826f362bce1038131603bd2ccf5dc1",
  "pr": "not-created",
  "status": "EVIDÊNCIA MEDIDA AO VIVO + 4 CORREÇÕES GERAIS (ProjectElevation, T com vizinho, CAD mm->cm, fileira de B34); regras candidatas restantes listadas",
  "objective": "Com o projeto humano PRONTO aberto ao lado do projeto de teste (mesma planta, mesmo CAD, mesmos níveis), rodar o solver do repositório sobre os mesmos eixos e comparar bloco a bloco, nó a nó, para validar ou derrubar as regras 11.10/11.11 (respostas rápidas do usuário, que ele mesmo pôs em dúvida) e extrair regras novas com prova.",
  "documentos": [
    "REFERÊNCIA (somente leitura, nenhuma Transaction): 'BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO) (1)' - 65.747 blocos livres (0 Walls), 13 níveis. 1º PAVIMENTO: 6.634 blocos, 14 fiadas (z = 1..261 cm), 44 aberturas (21 portas, 23 janelas).",
    "ALVO DE TESTE (gravável): 'butanta testes' - 46 Walls 'Parede 14cm' no 1º PAVIMENTO, 0 blocos, 5 imports de CAD. Único documento tocado."
  ],
  "correcoes_gerais_desta_rodada": [
    "BUG REAL - regra 8a.1: `base_z_abs = selected_level.Elevation` lia a cota relativa à Base de elevação do nível (aqui: Ponto de Levantamento = 72.665 cm) enquanto Walls e blocos vivem no referencial interno (ProjectElevation = 0). A modulação nasceria 726 m acima das paredes. Corrigido com `_level_internal_elevation_ft` (ProjectElevation, fallback .Elevation), 9 usos, teste com guarda de fonte. A regra 8a (origem = NÍVEL) não muda.",
    "REGRA 11.10 REVISADA pela evidência humana: T sem espaço DEGRADA para B34|B34 (a degradação para L que solve_t_intersection já tinha) e só fica sem modular se nem assim couber. Causa de o T não degradar sozinho: o teste de espaço na parede principal só parava nos nós das PONTAS; dois T de meio de vão na mesma parede nunca se enxergavam. Fix: `_clip_range_by_midspan_neighbours`. `_reject_overlapping_node_ties` vira rede de segurança. Caso mínimo da Torre [21,19,44]: 2 nós 'não cabe' -> PASS com os dois T degradados.",
    "ERRO DO CAD (doc de teste): o import '1 PAV' estava com 'Importar unidades = milímetro' para um DWG em CENTÍMETROS - tudo 10x menor e 34.786 linhas degeneradas (ARQ-STR-BLOCO tinha peça máxima de 5,4 cm = B54/10). Corrigido no doc de teste: fator de escala do TIPO = 10 (`IMPORT_SCALE` do tipo; o da instância é read-only) + reposição por alinhamento; 93% dos eixos longos de A-WALL a <=2 cm do layer 'Paredes', A-WALL 3.729 -> 4.700 linhas. Transformação registrada em evidence/2026-09-10-butanta-cad-fix.json."
  ],
  "metodo": [
    "Blocos humanos exportados com bbox/rotação/tipo (ref-1pav-blocks.json); atribuídos aos eixos das 46 Walls por distância lateral <= 7,5 cm e orientação pela ROTAÇÃO (o bbox engana em peças mais curtas que a espessura - primeira versão classificou C04/C09 como transversais e foi corrigida).",
    "12 das 46 Walls do layer 'Paredes' NÃO são alvenaria no projeto humano (0-12 blocos, só amarrações de paredes que as cruzam). Excluídas: criavam 11 nós T FALSOS. As 34 restantes cobrem 100% dos 527 blocos humanos da 1ª fiada.",
    "Aberturas: `span_along_axis_cm` do 02_openings.json (vão REAL na alvenaria). `x_cm/y_cm ± largura/2` é o ponto de inserção da família e fica ~15 cm deslocado - a primeira rodada com ele produziu '23 invasões / 391 não modulares' e 15 'juntas corridas' humanas que eram todas artefato. RETRATADO.",
    "Solver rodado offline (CPython 3, dublês) sobre os MESMOS 34 eixos, 14 fiadas, base_z 0, com as mesmas aberturas. O auditor do repositório (`audit_all_walls_bond_quality`) foi aplicado TAMBÉM à modulação humana, com as mesmas aberturas e o mesmo grafo."
  ],
  "resultados": [
    "ENCONTROS EM L (13): humano e solver IDÊNTICOS - B34 nas duas fiadas, alternando a parede que atravessa.",
    "ENCONTROS EM T (37 reais): 30 com espaço -> humano B54 na principal + B34 na que chega (paridade alternada) = exatamente o solver; 4 com espaço -> B34|B34; 3 SEM espaço (vizinho a 50 cm) -> humano B34|B34 (B34 na principal cobrindo o nó + B34 na que chega), solver produzia C09|C09 (compensador no nó). Esses 3 são parede de 99 cm com canto nas duas pontas + T no meio: a reserva fixa de 34 cm por ponta (`_wall_reserved_range_ft`, pior caso) não deixa os 34 cm que a degradação exige - o humano usa a fiada em que o canto pertence à OUTRA parede. Pendente (per-fiada), registrado abaixo.",
    "AUDITOR DO REPO SOBRE O HUMANO (aberturas reais): 34 paredes, 2 reprovadas, 3 problemas, todos HALF_BLOCK_NEAR_TIE (B19 encostado na amarração de canto) - que a exceção CR-BLOCK-B19-RESIDUAL-FILL já prevê (não marcada porque os candidatos humanos não carregam placement_reason). ZERO junta corrida, ZERO faixa de compensador. O auditor CONCORDA com o projeto pronto.",
    "AUDITOR DO REPO SOBRE O SOLVER (mesma geometria, mesmas aberturas): 12 paredes reprovadas = 7 REPEATED_VERTICAL_COMPENSATOR_STRIP (C09 no mesmo X em 11-14 fiadas, nas sete paredes idênticas de 494 cm sem abertura, 8079833-41 - o humano fecha as mesmas paredes sem faixa nenhuma) + 9 CONTINUOUS_VERTICAL_JOINT em 5 paredes, TODAS na fronteira preenchimento|amarração (8079818 x~999,5 em 14 fiadas; 8079838 x~454,5/464,5; as três de 99 cm em x~49,5/64,5 em 14 fiadas). Humano sob o mesmo auditor: zero de cada tipo. APÓS a reordenação do tier (fileira de B34 antes de compensadores empilhados): 5 paredes reprovadas, só as 9 juntas na fronteira preenchimento|amarração; histograma do solver passa a B39 3880 / B34 1557 / B19 272 / B54 201 / C09 467 / C04 302 (6.679).",
    "PREFLIGHT do solver com aberturas reais: ok, 0 colisões, 0 invasões, 0 vãos de porta invadidos, 0 intersection_failures, 78 trechos não modulares.",
    "HISTOGRAMA (34 paredes, fiadas 0..12): humano B39 3059 / B34 1615 / B19 324 / B54 170 / C09 242 / C04 245 (5.655); solver 4357 / 846 / 386 / 201 / 739 / 455 (6.984). Parte do excesso de B39 do solver é onde o humano põe CANALETA (979 peças pulados: fora de escopo). O que resta é estratégia: o humano fecha comprimento com CORRIDAS DE B34 (545 corridas de 1, 315 de 2, 89 de 3, 33 de 4+), o solver com compensador.",
    "COINCIDÊNCIA DE JUNTAS c0/c1 (melhor paridade): média 0,29; >= 0,5 em 10/34. Melhores: 8079818 (0,71), 8079838 (0,68), 8079801 (0,66)."
  ],
  "regras_confirmadas_pela_evidencia": [
    "T = B54 na principal + B34 na que chega, alternando fiada (30/34 nós). Nada a mudar.",
    "L = B34|B34 (13/13). Nada a mudar.",
    "11.8 (peça pequena de fechamento encostada no vão pode alinhar): o humano põe PASTILHA C04 (ou C09) na jamba em TODA fiada; a junta bloco|pastilha coincide em todas e é legítima. Confirmada - e sensível à borda: a isenção usa tolerância de 2 cm, então a borda passada ao solver tem de ser o vão REAL na alvenaria.",
    "CR-BLOCK-B19-RESIDUAL-FILL: o humano fecha trecho residual com B19 encostado no B34 de canto (3 casos). Confirmada.",
    "Decisão do usuário 'manter reprovando' a junta corrida na fronteira preenchimento|amarração: COERENTE com o humano, que não produz nenhuma sob o mesmo auditor. O trabalho é no layout do solver perto dos nós, não no auditor."
  ],
  "regras_novas_candidatas_para_confirmacao": [
    "11.10 REVISADA (já implementada, evidência: 3/3 nós sem espaço): T sem espaço degrada para B34|B34; só fica sem modular se nem assim couber.",
    "RESERVA DE CANTO POR FIADA (pendente): numa parede curta com canto nas duas pontas, na fiada em que o B34 do canto pertence à OUTRA parede, a reserva desta parede é só a espessura da outra (14 cm), não 34 cm. É isso que permite ao humano pôr B34 no T de uma parede de 99 cm. Hoje `_wall_reserved_range_ft` reserva 34 cm nas duas fiadas (pior caso) e força compensador.",
    "B34 COMO PEÇA CORRENTE - RESOLVIDO COMO BUG DE IMPLEMENTAÇÃO (não regra nova): a seção 2 já mandava preferir B34 a compensadores empilhados; `_pier_ordered_layout` devolvia o fallback irrestrito de compensadores ANTES da fileira de B34 acima do teto. Reordenado (ver seção 2 das regras). Efeito: reprovações do solver 12 -> 5, B34 846 -> 1557 (humano 1615), C09 739 -> 467; as 7 faixas de compensador das paredes de 494 cm desaparecem e a composição passa a ser a do humano (9xB39 + 3xB34). Bancada da Torre: 154 peças, igual ao Revit real.",
    "LAYER 'Paredes' DO CAD ARQUITETÔNICO CONTÉM PAREDES NÃO ESTRUTURAIS (12/46 aqui): o fluxo CAD -> Walls precisa de um filtro (layer estrutural, ou marcação do usuário) - senão nascem nós T falsos e amarrações onde o humano não põe bloco nenhum."
  ],
  "nao_conclusivo": [
    "Trecho curto ponta-livre -> T (defeito 1): as 4 'pontas livres' medidas não têm bloco nenhum nos primeiros 40-55 cm nas duas fiadas - são pilares de concreto (layer Estrutura), não pontas de alvenaria. Sem a geometria dos pilares no doc de teste, não dá para julgar o escalonamento do trecho curto pelo humano.",
    "11.11 (boneca absorvida): o humano não tem boneca atravessando parede neste pavimento; regra não testada por esta evidência."
  ],
  "limites": [
    "PARIDADE Revit x offline: o motor da branch carregado DENTRO do Revit (IronPython 2.7, shim de math.isfinite) com as 44 aberturas detectadas pelo PRÓPRIO plugin (collect_opening_instances('auto') sobre as famílias de Mobiliário do doc de teste) resolve as mesmas 34 paredes em 21,5 s com 7.257 peças, preflight ok, 0 colisões, 0 invasões, ifail 0, nmod 78, bond 5 - idêntico ao offline CPython (7.257; histograma difere em poucas peças por spans do acervo x detecção automática). A divisão inteira do IronPython não alterou o resultado neste corpus.",
    "Só o 1º PAVIMENTO; 3º-8º são clones do 2º segundo o README do acervo.",
    "Canaletas (979 peças do 1º PAV) fora do escopo por instrução - o solver as substitui por bloco comum, o que infla B39.",
    "A extração humana usa bbox com 1 cm de junta por face (as erratas do acervo avisam); juntas medidas no ponto médio entre faces."
  ],
  "reproducao": [
    "py -3 docs/checkpoints/evidence/_scripts/human_seq.py",
    "py -3 docs/checkpoints/evidence/_scripts/with_openings.py   (B auditor no humano, D solver x humano, E reprovacoes do solver)",
    "py -3 docs/checkpoints/evidence/_scripts/masonry34.py       (nos T com orientacao, 34 paredes)",
    "py -3 docs/checkpoints/evidence/_scripts/tnodes.py          (contexto dos nos T, 46 paredes)"
  ],
  "references": [
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-ref-1pav-blocks.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-test-walls.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-human-sequences.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-solver-vs-human.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-cad-fix.json"
    },
    {
      "path": "docs/checkpoints/evidence/2026-09-10-butanta-awall-axes.json"
    },
    {
      "path": "docs/revit_reference_extraction/butanta-r08-lt/02_openings.json"
    },
    {
      "path": "nuvem/REGRAS_MODULACAO_BLOCOS.md"
    }
  ],
  "head": "308554d06c90dfdef992be5705ae9b32076ce714",
  "changes": [
    "wall_modeling.py: _level_internal_elevation_ft (regra 8a.1, ProjectElevation) em 9 usos.",
    "wall_stepper.py: _clip_range_by_midspan_neighbours (11.10 revisada: T sem espaco degrada para B34|B34); fileira de B34 antes de compensadores empilhados em _pier_ordered_layout (secao 2).",
    "Doc de teste 'butanta testes': import '1 PAV' corrigido (fator de escala do tipo x10 + reposicao).",
    "REGRAS: 8a.1, 11.10 revisada, correcao de implementacao na secao 2.",
    "Evidencia e scripts em docs/checkpoints/evidence/."
  ],
  "tests": [
    "tests/test_level_internal_elevation.py (3), tests/test_scale_autofix_rules.py (12, reescrito para a semantica com evidencia), tests/test_fill_prefers_b34_row_over_stacked_compensators.py (4): todos passando; focados 130 passed.",
    "Paridade Revit x offline no solve das 34 paredes: 7.257 pecas nos dois, preflight ok, ifail 0, nmod 78, bond 5."
  ],
  "known_failures": [
    "Solver ainda reprova 5 paredes de Butanta (9 juntas corridas na fronteira preenchimento|amarracao); humano 0.",
    "3 nos T em parede de 99cm com canto nas duas pontas ainda saem C09|C09 (humano B34|B34) - reserva de canto por fiada pendente.",
    "Criacao fisica dos 7.257 blocos disparada via _execute_create: MCP estourou timeout; estado registrado no checkpoint final."
  ],
  "physical_deltas": [
    "Doc de teste: import 1 PAV reescalado/reposicionado; criacao de blocos em andamento no momento deste checkpoint (ver checkpoint final)."
  ],
  "decisions_taken": [
    "Projeto humano prevalece sobre as respostas rapidas do usuario (instrucao explicita dele).",
    "Nao mudar o auditor: ele concorda com o humano; corrigir o gerador."
  ],
  "decisions_pending": [
    "Reserva de canto por fiada; filtro de paredes nao estruturais no fluxo CAD->Walls; B19 no trecho curto (inconclusivo); 11.11 nao testada pelo humano."
  ],
  "next_steps": [
    "Checkpoint final com a regressao consolidada e o resultado fisico da criacao."
  ]
}
```

## O que a comparação respondeu

| Pergunta aberta | Resposta rápida do usuário | O que o projeto pronto faz | Ação |
|---|---|---|---|
| Dois T a menos de 54 cm (defeito 2) | deixar sem modular | **B34\|B34** (3/3 nós) | 11.10 revisada e implementada |
| Junta corrida na fronteira preenchimento\|amarração (defeito 1) | manter reprovando | não produz nenhuma sob o mesmo auditor | mantida; corrigir o layout do solver, não o auditor |
| B19 no trecho curto | B19 numa paridade | pontas medidas são pilares, não alvenaria | não conclusivo |
| Boneca atravessando (11.11) | absorvida | caso não ocorre no pavimento | não testada |

## Retratações desta rodada (registradas para não voltarem)

1. "O humano quase não usa compensador" — falso; classificação por bbox errava peças < 14 cm. Humano: 242 C09 + 245 C04.
2. "Solver invade 23 vãos e gera 391 não modulares" — artefato do mapeamento de abertura pelo ponto de inserção; com o vão real: 0 invasões, 78 não modulares.
3. "15 juntas corridas humanas" — todas pastilha de jamba, isentas pela 11.8 com a borda certa.
