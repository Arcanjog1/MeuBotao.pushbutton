---
name: cr-checkpoint
description: Salva e retoma a memória operacional de um CR (Change Request) para permitir continuação rápida em novas sessões ou após estouro de contexto, sem poluição de tokens.
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
---

# CR-CHECKPOINT — Memória Operacional de CR

Esta Skill gerencia checkpoints operacionais de trabalho para continuidade de sessões do Claude Code.

## 1. Princípios Fundamentais

- **Memória Operacional, Não Documentação Permanente:** Checkpoints servem exclusivamente para transferência e retomada de contexto de trabalho.
- **Não Substitui Fontes Canônicas:** Nunca substitui código, testes, `nuvem/REGRAS_MODULACAO_BLOCOS.md`, `CLAUDE.md` ou documentação do repositório.
- **Enxuto e Direto ao Ponto:** Sem dumps de prompts, sem logs gigantescos, sem cópia integral de arquivos ou históricos de git.
- **Não Automatizado por Ação:** NUNCA criar hooks agressivos para salvar a cada passo. Usar apenas em marcos relevantes.

---

## 2. Quando Criar ou Atualizar Checkpoint

Criar ou atualizar checkpoint exclusivamente nos seguintes marcos:
1. **Causa-raiz comprovada** (diagnóstico concluído);
2. **Hipótese importante descartada** (evita retrabalho investigativo);
3. **Candidato de fix implementado** (código modificado, pré-teste);
4. **Bateria de testes ou benchmark concluída** (métricas apuradas);
5. **Contexto atingindo níveis elevados** (preparação preventiva para nova sessão);
6. **Troca de sessão / conta / interrupção iminente**;
7. **Solicitação explícita do usuário**.

---

## 3. Local de Armazenamento

- **Caminho:** `.claude/checkpoints/<nome-do-cr>.md` (ex.: `.claude/checkpoints/cr-t-intersection-fix.md`)
- **Git:** Esta pasta é desversionada via `.gitignore` (`.claude/*`), garantindo que rascunhos operacionais locais não poluam o histórico do repositório.

---

## 4. Estrutura Padrão do Arquivo de Checkpoint

Todo checkpoint deve seguir rigorosamente a estrutura abaixo:

```markdown
# CHECKPOINT — <NOME_DO_CR>

## Metadados
- **CR:** <identificador-do-cr>
- **Data/Hora:** <YYYY-MM-DD HH:MM>
- **Branch:** <branch-atual>
- **Base SHA:** <sha-base>
- **Head SHA:** <sha-atual>

## Objetivo
<1 a 2 frases explicando o objetivo exato do CR>

## Estado Atual
<Diagnóstico | Implementação | Validação | Pronto para Entrega>

## Causa Provada
<Explicação concisa da causa-raiz comprovada>

## Hipóteses Descartadas
- <Hipótese descartada e teste/evidência que a refutou>

## Alterações Realizadas
- `<caminho/arquivo.py>`: <resumo da alteração pontual>

## Arquivos Importantes Já Analisados
- `<caminho/arquivo.py>`: <conclusão/relação extraída>

## Testes Executados
- `<comando/teste>`: PASS | FAIL (<detalhe essencial>)

## Métricas Importantes
- <Métricas relevantes de benchmark/auditoria, se aplicável>

## Gates
- [x] G1: Diagnóstico / Reprodução
- [ ] G2: Fix e Testes Unitários
- [ ] G3: Regressão / Benchmark
- [ ] G4: Auditoria de Diff Zero em Código Não-Alvo

## Pendências
- <Item pendente 1>
- <Item pendente 2>

## Próximo Passo Exato
<Ação precisa e imediata para a próxima sessão executar>

## Não Fazer
- <Armadilhas identificadas, caminhos inválidos ou instruções de contenção>
```

---

## 5. Fluxo de Retomada de um CR em Nova Sessão

Ao iniciar uma sessão com intenção de continuar um CR existente:

1. **Localizar e ler o checkpoint:** Ler `.claude/checkpoints/<nome-do-cr>.md`.
2. **Validar o ambiente Git:**
   - Executar `git status --short` e `git rev-parse HEAD`.
   - Confirmar branch atual e se o SHA da HEAD corresponde ao checkpoint.
   - Preservar eventuais alterações pendentes na worktree.
3. **Não reinvestigar:**
   - Respeitar a "Causa Provada" e as "Hipóteses Descartadas".
   - Não reler o repositório inteiro nem refazer investigações já concluídas.
   - Caso uma informação crítica pontual suscite dúvida, consultar cirurgicamente a fonte original.
4. **Executar o "Próximo Passo Exato":**
   - Continuar a execução imediatamente a partir da próxima ação indicada no checkpoint.
5. **Atualizar o checkpoint:**
   - Ao atingir o próximo marco, atualizar o arquivo em `.claude/checkpoints/`.
