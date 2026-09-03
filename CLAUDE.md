# Modulacao Automatica (pyRevit) - instrucoes para o Claude Code

## Idioma

Sempre responder ao usuario em portugues do Brasil (pt-BR), em toda
sessao futura deste projeto - independente do idioma usado na pergunta.

## Merge na main

REVOGADO (2026-09-03) o "ok" permanente que existia aqui: NUNCA fazer
merge na `main` sem autorizacao explicita do usuario PARA AQUELE MERGE
especifico. Commit e push na branch de trabalho continuam permitidos
quando a tarefa autorizar.

Quando o usuario autorizar um merge especifico:
- `git fetch origin main` + garantir que a branch local `main` esta'
  atualizada (`git pull`/fast-forward) antes do merge.
- Rodar a suite de testes (`python3 -m pytest tests/test_script.py -q`,
  instalando `pytest` se necessario) e so' empurrar se os testes
  passarem.
- Resolver qualquer conflito de merge antes de dar push; se o conflito
  for em logica (nao so' trivial), avisar o usuario antes de decidir.

## Check-ins e monitoramento automatico

NUNCA criar por iniciativa propria: check-in horario, monitoramento de
PR, polling, tarefa recorrente ou rechecagem agendada. So' fazer isso se
o usuario pedir explicitamente. Nunca re-armar um monitoramento por
conta propria.

## Recuperacao progressiva de contexto

Carregar somente o contexto necessario para a tarefa atual, mas ECONOMIA
DE CONTEXTO NUNCA TEM PRIORIDADE SOBRE CORRECAO: havendo duvida razoavel
sobre a existencia de uma regra/contrato/decisao relevante, ampliar a
busca antes de concluir que ela nao existe.

Fluxo padrao: entender o problema -> identificar conceitos relevantes ->
buscar (termo exato, depois sinonimos/pt-BR-EN, depois entidades
relacionadas, depois headings `rg "^#"`, depois simbolo de codigo `git
grep`) -> localizar arquivo/secao -> ler o trecho minimo suficiente
(assinatura + entradas/saidas + chamadas relacionadas, nao so' uma linha
isolada) -> ampliar (secao vizinha, depois arquivo completo) somente se
a busca em camadas anterior ficou inconclusiva ou o assunto e' critico
(amarracao, prisma, L/T/X, aberturas, B34/B54, compensadores,
pilaretes, validacao final) -> so' entao registrar "regra nao
localizada", sem nunca inventar uma regra.

Antes de declarar uma regra ausente: nunca concluir isso apos uma unica
busca sem resultado — o termo pode estar em outro idioma, sinonimo,
nome antigo ou descrito por consequencia. Testar termo original + pelo
menos um sinonimo/conceito relacionado antes de desistir.

`nuvem/REGRAS_MODULACAO_BLOCOS.md` continua sendo a fonte oficial das
regras de modulacao (autoridade preservada) — nao e' preciso ler o
arquivo inteiro para toda alteracao pequena; localizar a secao pelo
heading/ID/termo primeiro, e so' ler o arquivo completo quando a busca
em camadas ficar inconclusiva ou o risco de erro for alto.

Ao alterar codigo: preferir busca por simbolo (`git grep`/`rg`) antes de
abrir arquivos grandes; localizar callers e testes relacionados quando o
contrato de uma estrutura estiver em duvida (nao e' obrigatorio para
toda tarefa). Evitar reler o mesmo conteudo na mesma sessao sem motivo
concreto. Rodar suites de teste de forma progressiva durante o
diagnostico (reproducao minima -> modulo -> CR especifico -> suite
completa) e so' rodar a suite completa antes da entrega final ou de um
merge autorizado — isso nao dispensa os gates finais de determinismo.
Nao pesquisar na web por padrao, exceto quando a informacao local for
insuficiente ou o usuario pedir (a obrigacao de consultar o
RevitApiDocs abaixo continua valendo sempre que houver uso real da
API).

## Documentacao da API RevitAPI

Sempre que precisar consultar a API do Revit (classes, metodos, propriedades,
namespaces do RevitAPI), pesquisar no site https://www.revitapidocs.com/2027/
antes de responder ou implementar.

## Atualizacao obrigatoria das regras de modulacao

Sempre que o usuario fizer uma correcao, um ajuste, uma observacao ou
definir uma nova regra relacionada a' modulacao dos blocos, essa
informacao e' considerada uma ATUALIZACAO OFICIAL das regras do projeto.

Depois de implementar ou analisar a correcao pedida, a regra
correspondente DEVE ser adicionada ou atualizada no arquivo:

`nuvem/REGRAS_MODULACAO_BLOCOS.md`

### Procedimento obrigatorio

1. Identificar toda correcao ou nova orientacao do usuario relacionada
   a' modulacao.
2. Verificar se essa regra ja' existe no `nuvem/REGRAS_MODULACAO_BLOCOS.md`.
3. Se nao existir, adicionar a nova regra de forma clara e objetiva.
4. Se ja' existir, atualizar a regra existente para refletir corretamente
   a orientacao mais recente do usuario.
5. Evitar regras duplicadas ou contraditorias.
6. Em caso de conflito com uma regra anterior, a orientacao mais recente
   do usuario tem prioridade.
7. Antes de qualquer alteracao futura na logica de modulacao, consultar
   o `nuvem/REGRAS_MODULACAO_BLOCOS.md` e garantir que todas as regras e
   correcoes ja' definidas sejam respeitadas.

### Regra fundamental

Nenhuma correcao feita pelo usuario sobre a modulacao dos blocos pode
ficar apenas na conversa ou apenas no codigo. Toda correcao relevante
deve ser registrada permanentemente no `nuvem/REGRAS_MODULACAO_BLOCOS.md`,
para que nao seja esquecida nem perdida em alteracoes futuras do sistema.

## TODO conhecimento de AMARRACAO deve ser guardado

Pedido explicito do usuario (2026-08-28). A amarracao e' o nucleo do
sistema: e' o que diferencia uma parede de alvenaria ESTRUTURAL de um
empilhamento de blocos. Por isso, qualquer conhecimento novo sobre
amarracao - venha de onde vier - e' registro OBRIGATORIO em
`nuvem/REGRAS_MODULACAO_BLOCOS.md`, antes ou junto da implementacao,
nunca depois nem "quando sobrar tempo".

Conta como conhecimento de amarracao:

- Encontros em L, T e X (quando usar B54/B34, onde encostar, como
  degradar quando falta espaco);
- Posicao do VAO MENOR das pecas assimetricas (B34/B54) e o alinhamento
  dele entre fiadas;
- Junta vertical entre fiadas: o que e' proibido, o que e' excecao;
- Continuidade e repeticao entre fiadas (padrao das fiadas impares x
  pares);
- Transicao entre pecas de tamanhos diferentes ao longo da altura;
- Sobreposicao de volume: qual e' amarracao legitima e qual e' colisao;
- Bonecas, pilaretes e trechos curtos perto de encontros;
- Qualquer medicao feita no Revit real (via MCP) que confirme, refute ou
  detalhe uma dessas regras.

### Como registrar

1. Escrever a regra em `nuvem/REGRAS_MODULACAO_BLOCOS.md` com o rotulo de
   confianca que ela merece (REGRA OBRIGATORIA / PREFERENCIAL / EXCECAO
   PERMITIDA / PADRAO OBSERVADO AINDA NAO CONFIRMADO / CONFLITO).
2. Registrar COMO aquilo foi descoberto: medicao no Revit, print do
   usuario, teste, ou deducao - e o numero medido, quando houver.
3. Se a regra ainda nao esta' implementada, marcar `DOCUMENTADO -
   pendencia de codigo aberta` em vez de deixar implicito que ja' funciona.
4. Nunca apagar uma regra anterior em silencio: se a nova contradiz a
   antiga, registrar o conflito e qual delas vale agora (a orientacao mais
   recente do usuario tem prioridade).

Um erro de amarracao que volta a acontecer porque a regra nao foi escrita
e' considerado falha do processo, nao do solver.
