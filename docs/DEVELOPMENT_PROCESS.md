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
