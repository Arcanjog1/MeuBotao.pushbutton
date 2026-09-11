---
name: repo-research
description: Executa pesquisas aprofundadas no repositório em contexto isolado (via fork de contexto e subagente built-in Explore), retornando apenas uma síntese estruturada ao contexto principal para economia de tokens.
context: fork
agent: Explore
allowed-tools:
  - Read
  - Grep
  - Glob
---

# REPO-RESEARCH — Pesquisa Isolada no Repositório

Esta Skill realiza investigações de código, rastreamento de símbolos, callers e localização de regras em contexto isolado via subagente built-in `Explore`, devolvendo apenas um resumo estruturado ao contexto principal.

## 1. Princípios de Operação

- **Isolamento de Contexto (`context: fork` / `agent: Explore`):** Toda a varredura e leitura de arquivos intermediários ocorre no contexto isolado do Explore. O contexto principal recebe exclusivamente o resultado sintetizado.
- **Estritamente Read-Only:** Nenhuma escrita, commit, alteração de baseline ou modificação de arquivos de código de produção.
- **Correção > Economia de Tokens:** A economia de tokens nunca pode justificar respostas superficiais ou falsos negativos. Caso uma busca inicial seja inconclusiva, o Explore deve seguir o protocolo de fallback.

---

## 2. Protocolo de Busca em Camadas (Fallback Obrigatório)

O agente `Explore` deve executar progressivamente:

1. **Termo Exato:** Busca literal por símbolo ou string (`Grep`);
2. **Sinônimos e Variantes:** Variações conceituais do termo;
3. **Bilinguismo (pt-BR / EN):** Termos em português (ex.: `amarração`, `fiada`, `encontro`) vs. inglês (`bonding`, `course`, `intersection`);
4. **Conceito Relacionado:** Módulos e funções adjacentes (ex.: `wall_pairing` ao investigar nós de interseção);
5. **Headings de Documentação:** Seções em `nuvem/REGRAS_MODULACAO_BLOCOS.md` ou documentação do projeto;
6. **Símbolo / Chamadores (Callers):** Onde funções/variáveis são instanciadas, passadas e consumidas;
7. **Leitura Localizada:** `Read` focado no bloco/função específica;
8. **Leitura Ampliada:** Expansão progressiva somente quando a busca em camadas anterior for inconclusiva.

> **Regra Fundamental:** Nunca concluir que uma regra, função ou símbolo "não existe" após apenas uma tentativa sem resultado.

---

## 3. Formato Obrigatório de Retorno ao Contexto Principal

A resposta retornada ao contexto principal deve conter estritamente:

### CONCLUSÃO
<Resposta direta, clara e precisa para a pergunta formulada>

### EVIDÊNCIAS
- <Evidência 1 com contexto mínimo necessário>
- <Evidência 2 com contexto mínimo necessário>

### ARQUIVOS / FUNÇÕES IMPORTANTES
- `<caminho/arquivo.py>`: `funcao_ou_classe()` — papel na arquitetura

### SÍMBOLOS / LINHAS RELEVANTES
- `<caminho/arquivo.py:L123-L145>`: `simbolo` — papel e uso específico

### INCERTEZAS
- <Dúvidas remanescentes, restrições da busca ou premissas a confirmar (ou "Nenhuma")>

### PRÓXIMO PASSO
<Ação recomendada para o contexto principal, se houver>
