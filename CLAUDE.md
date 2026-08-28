# Modulacao Automatica (pyRevit) - instrucoes para o Claude Code

## Idioma

Sempre responder ao usuario em portugues do Brasil (pt-BR), em toda
sessao futura deste projeto - independente do idioma usado na pergunta.

## Merge direto na main

O usuario autorizou (2026-08-26): correcoes/commits feitos em branches
`claude/...` podem ser mesclados DIRETO na `main` (merge commit local +
`git push origin main`), sem precisar abrir Pull Request nem esperar
aprovacao. Isso vale para toda sessao futura deste projeto, nao so' a
que recebeu o pedido.

Antes de mesclar:
- `git fetch origin main` + garantir que a branch local `main` esta'
  atualizada (`git pull`/fast-forward) antes do merge.
- Rodar a suite de testes (`python3 -m pytest tests/test_script.py -q`,
  instalando `pytest` se necessario) e so' empurrar se os testes
  passarem.
- Resolver qualquer conflito de merge antes de dar push; se o conflito
  for em logica (nao so' trivial), avisar o usuario antes de decidir.

So' NAO mesclar direto (voltar a pedir/abrir PR) se o usuario disser
explicitamente o contrario numa sessao futura.

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
