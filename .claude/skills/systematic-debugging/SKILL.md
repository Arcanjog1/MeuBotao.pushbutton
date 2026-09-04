---
name: systematic-debugging
description: Diagnóstico sistemático de causa-raiz para investigar bugs, testar hipóteses e localizar a primeira divergência antes de qualquer alteração de código.
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
---

# SYSTEMATIC-DEBUGGING — Diagnóstico Sistemático e Causa-Raiz

Esta Skill define o protocolo para impedir correções precipitadas baseadas apenas em sintomas visuais ou suposições sem comprovação factual.

## 1. Princípios Fundamentais

- **Correção > Economia de Tokens:** Investigar com evidências objetivas e reprodutíveis.
- **Buscar → Localizar → Provar → Corrigir → Verificar:** Nenhuma linha de produção é alterada antes da causa-raiz estar comprovada.
- **Proibido Fix Prematuro:** "Parecer correto" não autoriza alteração de código.
- **Fix Mínimo e Cirúrgico:** Corrigir a causa no ponto exato, sem refactors oportunistas nem hardcodes.

---

## 2. Fluxo Obrigatório de Diagnóstico

O fluxo de diagnóstico segue estritamente a sequência:

```
REPRODUZIR
   ↓
LOCALIZAR PRIMEIRA DIVERGÊNCIA
   ↓
FORMAR HIPÓTESES (lista curta: A, B, C)
   ↓
TESTAR HIPÓTESES (experimentos discriminantes)
   ↓
PROVAR CAUSA (evidência factual)
   ↓
SÓ ENTÃO IMPLEMENTAR (fix mínimo)
```

Antes de qualquer alteração de código, registrar explicitamente:
1. **Reprodução do problema:** comando, teste ou cenário determinístico.
2. **Comportamento esperado:** o que a regra/especificação define.
3. **Comportamento real:** o que foi medido/observado.
4. **Primeiro ponto de divergência:** onde o estado correto vira incorreto.
5. **Causa-raiz:** mecanismo exato gerador do erro.
6. **Hipóteses descartadas:** o que foi testado e refutado.
7. **Evidência que prova a causa:** log, medição ou teste de isolamento.

---

## 3. Protocolo de Proibição de Fix Prematuro

Antes de editar qualquer arquivo de produção, responder obrigatoriamente:

```markdown
CAUSA PROVADA:
<Mecanismo causal exato comprovado por dados>

EVIDÊNCIA:
<Dado objetivo: valor de variável, log de execução ou teste unitário isolado>
```

> **Regra de Bloqueio:** Se a causa ainda for hipótese (mesmo provável), o fix está **PROIBIDO**. Continue a investigação.

---

## 4. Gestão e Teste de Hipóteses

Manter uma lista curta de hipóteses concorrentes (máximo 2 a 4). Evitar dezenas de hipóteses dispersas.

Para cada hipótese registrar:
- **HIPÓTESE [A/B/C]:** Mecanismo causal proposto.
- **TESTE:** Ação discriminante que isola a hipótese.
- **RESULTADO:** Dado observado.
- **CLASSIFICAÇÃO:** `CONFIRMADA` | `REFUTADA` | `INCONCLUSIVA`.

Havendo hipóteses concorrentes, formular um **experimento discriminante** cujo resultado confirme uma e refute a outra.

---

## 5. Localização da Primeira Divergência

Em pipelines com múltiplas etapas sequenciais, não focar apenas no erro final visível na ponta.

Localizar o **primeiro ponto da cadeia onde o resultado correto vira incorreto**:

```
[Etapa 1: wall graph]    → CORRETO
[Etapa 2: arms / nós]    → CORRETO
[Etapa 3: course role]   → INCORRETO  <-- [PRIMEIRA DIVERGÊNCIA: Corrigir aqui!]
[Etapa 4: fill / peças]  → INCORRETO (efeito colateral)
[Etapa 5: coverage]      → RUIM (sintoma final)
```

> **Diretriz:** Corrigir preferencialmente o primeiro ponto semanticamente incorreto. Evitar compensar erros em etapas posteriores.

---

## 6. Critérios para o Fix Mínimo

Com a causa provada e a primeira divergência localizada:
- Implementar o menor fix suficiente para resolver a causa.
- **Proibido:**
  - Hardcode por projeto, nível ou wall ID.
  - Mudanças oportunistas ou refatorações fora do escopo do bug.
  - Silenciar sintomas sem tratar a lógica geradora.

---

## 7. Integração com Outras Skills

- **`cr-checkpoint`:** Ao atingir os marcos `CAUSA PROVADA` ou `HIPÓTESE DESCARTADA`, atualizar o checkpoint da sessão. Sem hooks automáticos.
- **`repo-research`:** Quando houver pesquisa ampla de símbolos, callers ou regras no repositório, delegar à Skill `repo-research` (contexto isolado), sem duplicar buscas no contexto principal.

---

## 8. Guia Rápido de Decisão (Cenários A / B / C)

| Cenário | Estado da Investigação | Ação Permitida |
|---|---|---|
| **Cenário A** | Sintoma conhecido, causa não provada | **NÃO** alterar código. Formar hipóteses e isolar primeira divergência. |
| **Cenário B** | Causa comprovada com evidência objetiva | **PERMITIDO** implementar o fix mínimo e avançar para verificação. |
| **Cenário C** | Duas ou mais hipóteses concorrentes abertas | **NÃO** alterar código. Executar experimento discriminante. |
