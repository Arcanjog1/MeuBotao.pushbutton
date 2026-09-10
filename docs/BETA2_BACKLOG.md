# Backlog do solver para o Beta 2
Base de código oficial: main 6c00f7e (produção igual à aa58d70).
Classificação por evidências existentes; sem varredura cega ou novo benchmark.

A — corrigir antes do Beta 2; B — verificar durante o Beta 2;
C — decisão do usuário; D — dívida posterior; E — suficientemente verificado
no escopo declarado. A aplica-se ao recorte que será lançado: defeito fora
dele não autoriza ampliar escopo. Contenção evita escrita, não corrige solver.

Fontes: [auditoria anterior](AUDITORIA_BETA_2026-09-09.md);
[estado/SHAs e fontes candidatas](GITHUB_STATE_2026-09-10.md);
[referências humanas](../reference_projects/COMPARISON.md).
Os números abaixo são execuções históricas inspecionadas, não reexecução nesta missão.

| Item | Classe | Evidência e justificativa | Critério de saída / ação |
|---|---|---|---|
| Pareamento | B | CR-2F-A/E/D estabilizaram simetria; extração real ainda precisa conferência, eixo espúrio histórico de 43,9m | Comparar CAD→eixos por identidade no recorte; reabrir só com contraexemplo |
| Fechamento aritmético modular | E | C04 #20 e controles em tests/test_script.py; 260 controles passaram nesta missão | Manter tolerância vigente; E não cobre parede com reservas/nós incompatíveis |
| Espessuras | B | UI limitada e casos de eixos paralelos com espaço menor que 14 cm em #31 | Conferir dimensão/eixo reais antes de criar cada recorte |
| Paredes ausentes | A | Omissão silenciosa é bloqueador; auditoria não prova completude universal CAD→resultado | Rastrear cada entrada até peça ou retenção com motivo; teste permanente do contraexemplo |
| Paredes vazias/parciais | A | 197,943 cm vazia; 99,754 cm depende de ponta/midspan; retenção parcial 09b6ea0 é candidata | Retenção explícita e nenhuma exclusão de referência; não ampliar recorte até tratar |
| Segmentos negativos | A | Relato de -2,586 cm entre reservas em parede de 99,754 cm | Rejeitar domínio inválido antes de compor; reproduzir mínimo sem clamp silencioso |
| L/T/X | A | #31: T139/162 com C04/C04 ainda sobrepõe 3,2464 cm; bancada #34 só cobre L sem aberturas | Corrigir conflito no recorte e verificar física por fiada; N1 não está liberada |
| Nós ambíguos | A | Hipóteses locais L163/L185 rejeitadas; geometria sobreposta pode vir de entrada | Disposição explícita da ambiguidade; sem escolha silenciosa de nó |
| Amarração e vão menor | A | TP1 W019 quatro juntas contínuas; referências novas não medem células/LTX completos | Garantir vínculos reais em todas as fiadas do recorte; recuperar orientação quando faltar |
| Juntas same-band | A | Parede 40 duas faixas C09 repetidas; trocar T95/138 não resolve | Teste físico com coordenadas/cotas; não somar variantes como fiadas reais |
| Juntas cross-band | A | G12 integrado reduz coincidências, mas duas identidades residuais históricas | Revalidar transições efetivas do recorte, incluindo futura meia-altura |
| Compensadores (contrato) | C | N1e intercala, não aprova teto; TGD 52→66 paredes na candidata | [Decidir teto/adjacência](decisions/DECISION-COMPENSATOR-LIMIT.md); manter regra atual |
| C2/G16 | C | +23 em ROW_MOSTLY_EMPTY depende de unidade; C1 resolve só MISSING_ROW | [Decisão específica](decisions/DECISION-C2-G16.md), sem recalibração automática |
| CR-B oficial | C | #28 é preparação; migração/G18/G20 e D1–D5 pendentes; D6 resolvida | [Decisão CR-B](decisions/DECISION-CR-B.md) + gates por versão antes de escrever |
| ARM SAFE REPAIR — fidelidade do contrato | E | #12/#18 integrados; identidade course_index e crédito físico de nó documentados/testados | Manter hard gates em cada rebuild; E não significa reparo completo de todas as arestas |
| ARM SAFE REPAIR — resíduos/otimização | D | Arestas isoladas residuais e custo de reconstruções; não ampliar política por saldo global | CR própria depois do beta, salvo defeito crítico no recorte (então A) |
| Determinismo | B | Provas locais e cache diferem de permutação global; repetir mesma entrada não prova invariância | Fixar input/config/hash, comparar cache on/off e permutações na versão selecionada |
| Performance/analyze síncrono | B | N1f 127s é histórico offline; branch a5081d8 não localizada; Revit final pendente | Medir host real, tempo por etapa, responsividade/recuperação; sem Beta 1 PASS antecipado |
| Aberturas: invasões atuais | A | #31 preflight final TGD 692 invasões/784 colisões; TP1 500/0, ambos bloqueados | Zero invasão no recorte; preservar propriedade/fiada ao atribuir volume |
| Aberturas: reforço A/B futuro | C | Duas referências sustentam proposta; ainda sem política estrutural aprovada | [Decisão](decisions/DECISION-OPENING-REINFORCEMENT.md), depois pacote separado |
| Cobertura | A | C1 corrige expectativa, não omissões; vazio contido continua vazio real | Entrada→resultado completo e auditar união de volumes; sem dupla contagem |
| Top course/canaletas | C | §10.7 aberto; 71,43%/73,82% não universal | [Política separada](decisions/DECISION-TOP-BOND-BEAM.md) |
| Blocos cortados | C | HEIGHT_CUT e LENGTH_CUT observados, representação incompleta atual | Aprovar tipos/limites/células no [catálogo](decisions/DECISION-CATALOG-SCOPE.md) |
| Fora do módulo (nova solução) | C | Recusa vigente não autoriza floor/tolerância maior | [Decisão](decisions/DECISION-WALL-OUTSIDE-MODULE.md); retenção é A independente |

## Ordem de execução

1. Recuperar SHA/evidência da branch de desempenho Beta 1 e fechar validação
   síncrona em missão Revit especificamente autorizada. Não declarar PASS aqui.
2. Escolher recorte e versão; cumprir itens A pertinentes, sem transportar N1
   inteira nem adotar decisões C para “fazer passar”.
3. Aprovar contratos A/B, catálogo e políticas numéricas necessárias.
4. Executar [pacote de implementação](architecture/beta2-implementation-package.md).
5. Verificações B no beta fixado; D fora do recorte fica explícito.

Suítes históricas não equivalentes: #31 em 09b6ea0 = 1112 passed/2 failed;
#34 em 8cdd33f = 1027 passed/2 failed. Logs preservados nas candidatas;
não representam main ou aprovação no Revit. 260 testes desta entrega
validam regressão do plugin, não substituem a suíte física completa.
