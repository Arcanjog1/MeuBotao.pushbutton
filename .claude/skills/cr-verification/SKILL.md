---
name: cr-verification
description: Verificação em múltiplos níveis, auditoria de gates, trade-offs de métricas e proteção de baselines para aprovação de CRs.
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
---

# CR-VERIFICATION — Verificação Rigorosa e Auditoria de Gates

Esta Skill define o protocolo para impedir que um CR seja declarado RESOLVIDO, APPROVED ou PRONTO PARA MERGE sem evidência atual.

## 1. Princípios Fundamentais

- **Evidência Atual Obrigatória:** Proibido aprovar com base em "o código parece correto" ou apenas "o teste principal passou".
- **Sem Auto-Ilusão em Trade-offs:** Uma melhora em uma métrica não anula uma regressão em outra.
- **Proteção de Baselines:** NUNCA atualizar baseline apenas para fazer teste passar.
- **Verificação Progressiva:** Executar testes em camadas proporcionais ao estágio de desenvolvimento.

---

## 2. A Pirâmide de Verificação

A validação de alterações deve ocorrer progressivamente:

```
[NÍVEL 6] Suíte Completa (obrigatória para entrega final / merge autorizado)
   ▲
[NÍVEL 5] Reference Corpus / Benchmarks Relevantes
   ▲
[NÍVEL 4] Regressões Relacionadas (módulos vizinhos e callers)
   ▲
[NÍVEL 3] Testes Específicos do CR
   ▲
[NÍVEL 2] Testes da Função / Módulo Modificado
   ▲
[NÍVEL 1] Teste Mínimo de Reprodução (ciclo rápido de feedback)
```

> **Diretriz:** Não rodar a suíte completa após cada pequena edição. Usar Níveis 1 a 3 durante o desenvolvimento e Níveis 4 a 6 nos marcos formais.

---

## 3. Gestão e Auditoria de Gates

Todo CR deve classificar seus gates críticos com um dos estados formais:

| Estado | Significado |
|---|---|
| `PASS` | Validado com evidência concreta e sem regressão. |
| `FAIL` | Falha verificada no teste, métrica ou critério de aceitação. |
| `BLOCKED` | Execução impedida por dependência externa ou ambiente. |
| `NOT_APPLICABLE` | Não aplicável ao escopo deste CR (com justificativa). |

### Regra de Veredito
- Se **todos** os gates críticos forem `PASS` → Veredito: **`APPROVED`** (ou `PRONTO PARA MERGE`, se autorizado).
- Se **qualquer** gate crítico for `FAIL` → Veredito máximo: **`NECESSITA AJUSTE`** (proibido aprovar).
- Se algum gate for `BLOCKED` ou inconclusivo → Veredito: **`BLOCKED`** ou **`NECESSITA VALIDAÇÃO`**.

---

## 4. Análise de Trade-off de Métricas

Se uma métrica melhorar e outra piorar: **NÃO** declarar automaticamente melhoria.

Construir obrigatoriamente a tabela de trade-off:

| MÉTRICA | ANTES | DEPOIS | DELTA | CLASSIFICAÇÃO |
|---|---|---|---|---|
| `<nome_metrica_1>` | `<v_ant>` | `<v_pos>` | `<delta>` | `MELHORIA` \| `REGRESSÃO` \| `NEUTRO` |
| `<nome_metrica_2>` | `<v_ant>` | `<v_pos>` | `<delta>` | `MELHORIA` \| `REGRESSÃO` \| `NEUTRO` |

*Classificações:* `MELHORIA`, `REGRESSÃO`, `RECLASSIFICAÇÃO`, `NEUTRO`, `INCONCLUSIVO`.

### Cenário de Referência
- `COVERAGE_MISSING_ROW`: `265` → `145` (`MELHORIA`), mas `COVERAGE_ROW_MOSTLY_EMPTY`: `+138` (`REGRESSÃO` crítica).
  - **Conclusão:** **`NECESSITA AJUSTE`** (e NÃO `APPROVED`).

---

## 5. Proteção de Baselines

NUNCA atualizar baseline apenas para fazer teste passar.

Se uma alteração for genuinamente necessária, exigir classificação e justificativa formal:
- `BENCHMARK_MEASUREMENT_FIX`: Correção no instrumento ou fórmula de medição.
- `EXPECTED_BEHAVIOR_CHANGE`: Mudança intencional de especificação aprovada.
- `HUMAN_REFERENCE_UPDATE`: Atualização de referência manual validada pelo usuário/projeto.

---

## 6. Gates de Determinismo (quando aplicável)

Para alterações em algoritmos do solver geométrico:
- Avaliar invariância por permutação de entrada (`input permutation`).
- Avaliar invariância por inversão de extremidades (`endpoint reversal`).
- Verificar consistência em execuções repetidas (`repeat runs` / `fingerprints`).
- Se o CR não afetar determinismo: marcar como `NOT_APPLICABLE`.

---

## 7. Auditoria de Diff de Produção

Antes de finalizar qualquer entrega:
1. Executar `git diff --stat` e `git status --short`.
2. Verificar: arquivos autorizados, ausência de alterações oportunistas, baselines e código de produção não relacionado.

---

## 8. Integração com Outras Skills

- **`cr-checkpoint`:** Ao concluir bateria de validação (`VALIDAÇÃO CONCLUÍDA`), registrar status dos gates e métricas no checkpoint (`.claude/checkpoints/<cr>.md`). Sem hooks automáticos.

---

## 9. Guia Rápido de Decisão (Cenários A / B / C)

| Cenário | Resultado da Verificação | Veredito Obrigatório |
|---|---|---|
| **Cenário A** | Todos os gates críticos com status `PASS` | **`APPROVED`** (apto para entrega/merge autorizado). |
| **Cenário B** | Teste principal passa, mas há regressão crítica em métrica/teste | **`NECESSITA AJUSTE`** (aprovação proibida). |
| **Cenário C** | Benchmark suspeito, instável ou inconclusivo | **`BLOCKED`** ou **`NECESSITA VALIDAÇÃO`**. |
