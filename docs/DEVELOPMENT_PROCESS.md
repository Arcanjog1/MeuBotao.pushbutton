# DEVELOPMENT PROCESS

Manual operacional curto para agentes (Claude/Codex/Antigravity ou humanos)
que forem trabalhar neste repositório. Não duplica regras de domínio nem
histórico de CRs - só o processo.

## Onboarding

Nova sessão? Comece por `docs/START_HERE.md` (roteador por domínio).

## Fonte de verdade

- regras de domínio (modulação de blocos):
  `nuvem/REGRAS_MODULACAO_BLOCOS.md`
- estado do projeto (atual):
  `docs/PROJECT_STATUS.md`
- histórico de CRs e log cronológico:
  `docs/PROJECT_STATUS_LOG.md`
- corpus de referência (benchmark atual):
  `docs/REFERENCE_CORPUS.md`
- snapshot legível do último estado medido oficialmente:
  `docs/CURRENT_REFERENCE_SNAPSHOT.md`
- instruções de sessão/governança:
  `CLAUDE.md` (raiz)

## Fluxo padrão de CR

```
OBJETIVO
  -> REPRODUZIR
  -> PRIMEIRA DIVERGÊNCIA
  -> CAUSA PROVADA
  -> FIX MÍNIMO
  -> TESTES FOCADOS
  -> REFERENCE CORPUS
  -> SUÍTE
  -> INTEGRAÇÃO LIMPA
  -> AUTORIZAÇÃO HUMANA
  -> MERGE
```

Cada seta é um gate: não pular etapa para economizar tempo. "Causa
provada" significa causa raiz demonstrada (reprodução mínima), não
suposição plausível.

## Regras

- não inventar causa; se a causa não está provada, registrar como
  hipótese, não como fato;
- `UNKNOWN` continua `UNKNOWN` - não forçar um veredito quando a
  evidência não sustenta;
- não esconder regressão, mesmo que pequena ou fora do escopo do CR;
- não atualizar baseline/reference para mascarar regressão;
- benchmark bug (erro na medição) e solver bug (erro no motor) são CRs
  separados - não misturar o fix dos dois;
- usar branch (ou worktree, quando aplicável) separado por CR;
- não alterar branch ativa de outro agente/CR sem coordenação explícita;
- não resetar trabalho não commitado - `git status` antes de qualquer
  operação destrutiva;
- integração de um CR antigo deve ser reproduzida sobre a `main` atual,
  não assumida como ainda válida;
- PR de auditoria (read-only, sem tocar produção) não significa código
  de produção aprovado - são responsabilidades distintas;
- merge na `main` exige autorização humana explícita, específica para
  aquele merge - nunca autorização permanente (ver `CLAUDE.md`);
- correção tem prioridade sobre economia de tokens/contexto - na dúvida
  razoável sobre uma regra existir, ampliar a busca antes de concluir
  que não existe;
- usar busca progressiva (termo exato -> sinônimo -> headings -> símbolo
  de código) antes de ler arquivos inteiros;
- evitar ler arquivos gigantes sem necessidade concreta;
- fazer checkpoint (ex.: skill `cr-checkpoint`) quando o contexto
  estiver perto do limite, para não perder estado de um CR em andamento;
- não misturar fixes independentes no mesmo CR sem justificativa
  explícita registrada no CR.

## Entrega documental verificavel

Estado corrente fica em [PROJECT_STATUS.md](PROJECT_STATUS.md). Separar
explicitamente OFICIAL (ancestral da main observada), CANDIDATO (SHA de
branch/PR), DECISOES PENDENTES e DIVIDAS. Atualizar o status e um checkpoint
de entrega relevante no mesmo PR. O checkpoint pode ser o proprio relatorio
se contiver a evidencia; nao copiar o mesmo relato para varios arquivos.
O log historico recebe apenas um indice para o checkpoint, preservando entradas.

Antes de publicar: `git fetch origin main`; comparar a main observada no
status com `git rev-parse origin/main`. Se avancou, ler seu diff e reconciliar
o estado e os fatos de outras sessoes. Nao substituir status pelo arquivo
inteiro de uma branch antiga nem usar resolucao automatica ours/theirs.
Usar checkpoint de nome unico por entrega, nunca editar o de outra sessao.
Git detecta conflitos textuais, nao contradicoes de significado.

1. Commitar o trabalho avaliado (codigo, quando autorizado).
2. Executar os checks necessarios uma vez e preservar comando, ambiente,
   SHA/tree, saida, exit code e duracao. Falhas incluem nome e assercao,
   nao apenas a quantidade. Interrupcao nao e PASS. Medicao de outra
   arvore so pode ser reaproveitada demonstrando equivalencia do escopo.
3. Criar `docs/checkpoints/YYYY-MM-DD-<cr>-<sessao>.md` com bloco JSON
   abaixo. `head` e o HEAD AVALIADO, anterior ao commit documental que o
   registra: evita a impossibilidade de um commit gravar seu proprio SHA.
   Depois desse HEAD, somente documentacao/infra documental pode mudar;
   alteracao de producao/teste de dominio exige novo HEAD avaliado.
4. Adicionar arquivos ao indice, conferir `git ls-files docs/checkpoints`
   e rodar `python tools/documentation/validate.py --base <merge-base>
   --main origin/main --require-current-main`.
5. Commit e push na branch autorizada. Criar PR draft; preencher sua URL
   no checkpoint em um commit documental posterior e validar novamente.
   `not-created` e permitido somente antes da criacao; ao concluir, URL
   real e check do PR fazem parte da entrega. Merge exige autorizacao.

Modelo de metadados (substituir os valores; nao e arquivo validavel):

```json
{
  "date": "YYYY-MM-DD",
  "branch": "codex/nome-da-entrega",
  "head": "SHA completo da revisao avaliada",
  "base": "SHA completo da base ancestral",
  "pr": "not-created",
  "objective": "Objetivo concreto",
  "changes": ["Arquivos e comportamento alterados"],
  "tests": ["Comando, resultado e referencia do log; ou nao executado e motivo"],
  "known_failures": ["Nome e assercao; ou nenhuma observada no escopo"],
  "physical_deltas": ["Chave fisica, unidades, ganhos/custos; ou nao aplicavel"],
  "decisions_taken": ["Decisao e evidencia da autorizacao; ou nenhuma"],
  "decisions_pending": ["Opcoes e consequencias; ou nenhuma"],
  "next_steps": ["Proxima acao limitada"],
  "references": [{"path": "docs/PROJECT_STATUS.md"}]
}
```

Referencia historica pode incluir `commit` (SHA completo), validada via
`git cat-file commit:path`. Referencia sem commit deve existir e estar
versionada no checkout. Links de Markdown locais sao verificados nos
documentos alterados; URLs externas, ancoras e nomes em crases nao sao
checados. O inventario de auditoria registra revisoes e caminhos em outras
branches sem copiar esses documentos para a main.

`tools/documentation/capture_validation.py` captura uma validacao com PID,
timeout, SHA/tree e hash SHA-256 do log, em destino explicito. Nunca
sobrescreve resultado anterior. Usar para comandos de teste sem servicos
persistentes; nao e gerenciador de arvores de subprocessos. O comando
`audit_inventory.py` captura metadados Git/GitHub sob demanda (requer `gh`);
nao publica nem altera regras. Resultados curtos ficam em
`docs/checkpoints/evidence/`; dados grandes exigem artefato acessivel e hash.
Nao publicar credenciais, tokens, projetos RVT ou dados privados desnecessarios.

## Validacao automatica e limites

O workflow existente agora testa o validador e verifica a ENTREGA completa
desde o merge-base nos PRs e branches `claude/**`/`codex/**`. Um push
documental posterior nao oculta omissao anterior do mesmo PR. Na main,
compara o push recebido e permite que o status registre a main anterior
ao proprio merge. O summary do Actions publica HEAD, base, main observada
e resultado verificavel; usa apenas `contents: read`, sem commits automaticos.

Isso e validacao/publicacao automatica de evidencia estrutural, NAO geracao
automatica de relato tecnico. Texto, selecao de testes, decisoes humanas,
veracidade das alegacoes e reconciliacao semantica continuam manuais.
Nao valida todo link historico nem impede omissoes no texto. A main estava
sem protecao na auditoria: um check vermelho nao impede merge por si.
Tornar este check obrigatorio e uma configuracao administrativa separada,
nao realizada nesta entrega. Nenhum mecanismo pode aprovar regra normativa,
reescrever gabarito ou promover um candidato apenas pelo titulo do PR.

## Recuperacao de sessao

Ler START_HERE, status, checkpoint pertinente e referencias ali indicadas.
Conferir estado sujo, HEAD, base, PR e main por fetch; diferenciar rascunho,
integrado e candidato. Verificar SHA/tree dos logs antes de reaproveitar
testes. Se processo ainda roda, usar PID/comando/log registrados, sem
relancar porque um monitor falhou. Checkpoint apenas local deve ser
recuperado e versionado antes da entrega. Retomar o proximo passo exato;
uma causa registrada e evidencia a conferir quando houver contradicao,
nao autoridade superior ao codigo ou ao usuario.


## Evidência e propostas (2026-09-10)

reference_projects contém portais; primários em docs/revit_reference_extraction
com inventário/hash/limites. rules/ e benchmark/ não são fontes concorrentes.
docs/decisions mantém STATUS/autorização. Nenhuma promoção normativa automática.

Ao alterar portais/acervo, executar também
python tools/documentation/verify_reference_inventory.py --protected-base <SHA>
e registrar resultado. Não executar coletores históricos para validar navegação.
Workflow #32 e validador permanecem governança única.
Snapshot guarda SHA observado anterior ao commit/merge que o publica; obter
merge posterior por URL do PR e fetch, sem autorreferência.
