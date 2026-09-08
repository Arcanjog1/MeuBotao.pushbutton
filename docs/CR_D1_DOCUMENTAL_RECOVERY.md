# CR-D1 — recuperação documental de duas revisões independentes

> **Só documentação.** Nenhum arquivo de produção, de teste, de gabarito
> ou de benchmark é tocado. Nenhuma decisão técnica é reaberta: os dois
> relatórios entram **exatamente** como foram escritos, com o veredito e
> as condições originais.

## O problema, medido

`docs/PROJECT_STATUS.md` da `main` (`91258dd`) cita dois relatórios que
**não existem na `main`** — duas referências quebradas, verificadas por
`git cat-file -e`:

| documento citado no `PROJECT_STATUS.md` | existe na `main`? |
|---|---|
| `docs/BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` | **não** |
| `docs/C04_INDEPENDENT_FINAL_REVIEW.md` | **não** |

## Onde eles estavam

Os dois **existem e estão commitados** — a dívida é de **merge**, nunca de
existência. Esta é a correção que a reconciliação da CR-B registrou em
**D6** ("a conclusão do candidato está errada: os dois relatórios existem").

| documento | commit de origem | branch | autor / data originais |
|---|---|---|---|
| `BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md` | `d8933cde710ddfd72d62b918c69be8719fb7075d` | `claude/opening-detector-review-cr-a-q8bhuk` | Claude, 2026-09-07 06:15:35 +0000 |
| `C04_INDEPENDENT_FINAL_REVIEW.md` | `418fba1e8a756555ecec5bdeab1e84db1551cf06` | `claude/c04-review-next-cr-prep-wc77d7` | Claude, 2026-09-07 02:16:36 +0000 |

## Fidelidade — conferida, não presumida

`sha256` do conteúdo no commit de origem × do arquivo recuperado:

```
BENCH_OPENING_RECONSTRUCTION_A_INDEPENDENT_REVIEW.md
  9634ef8beba9c2977111292106029952953462fe937865ff469192be0c18adb4  (idêntico)
C04_INDEPENDENT_FINAL_REVIEW.md
  431f587b3603cc6cc133c6926c60a09278c5a455929ba801a33308fa372ef0c6  (idêntico)
```

## O que NÃO foi trazido, de propósito

O commit `418fba1` tem **11 arquivos**. Só os **dois relatórios de
revisão** foram recuperados. Ficaram de fora, por serem escopo diferente
e não corresponderem a referência quebrada nenhuma:

- `docs/FUTURE_BLOCK_CR_PREPARATION.md`, `docs/FUTURE_BLOCK_CR_PROMPTS.md`;
- `nuvem/benchmark/future_cr_preparation/**` (7 scripts de diagnóstico).

**Nenhuma branch foi cherry-picada inteira**, e nenhuma alteração de outra
autoria entrou junto.

## O que esta CR não faz

- Não reabre, não reescreve e não reinterpreta nenhum veredito.
- Não altera `PROJECT_STATUS.md` (as referências passam a resolver
  sozinhas assim que os arquivos existirem na `main`).
- Não mescla nada. **PR draft; merge só com autorização explícita.**
