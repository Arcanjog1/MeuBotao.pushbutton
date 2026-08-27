# Loader do GitHub — configuração do token

> Este documento explica como configurar a autenticação usada pelo
> [`Script.py`](Script.py), que agora é apenas um **loader**: ele baixa a
> versão mais recente do motor real — hoje um **pacote** inteiro
> (`core/`, não mais um único arquivo — ver
> [`ARQUITETURA_INTERATIVA.md`](ARQUITETURA_INTERATIVA.md)) — direto do
> repositório no GitHub a cada execução, em vez de rodar uma cópia local
> fixa. Isso permite manter o repositório **privado** e atualizar todos
> os computadores automaticamente com um único `git push`.

## Por que isso existe

- **Antes:** `Script.py` continha o código inteiro. Para atualizar um PC,
  alguém precisava dar `git pull` (ou copiar o arquivo) manualmente ali.
- **Agora:** `Script.py` é um loader pequeno. O código real mora no pacote
  `core/` (todos os `.py` dentro dele, recursivamente), no GitHub. Toda
  vez que o botão é clicado, o loader lista a árvore de arquivos via API
  do Git, baixa cada um, e só então executa `core/wall_modeling.py`. Um
  `git push` no repositório atualiza instantaneamente qualquer PC que
  clicar no botão depois — sem sincronização manual, e sem precisar tocar
  no loader quando um arquivo novo é adicionado dentro de `core/`.
- Como o repositório pode ficar **privado**, é exigido um token de
  acesso (PAT) para o download funcionar.
- **Engine CPython:** a primeira linha de `Script.py` é `#! python3` — o
  botão roda no engine CPython do pyRevit (não mais o IronPython padrão).
  A UI interativa em PySide6 que motivou essa troca foi **removida**
  (2026-08-26) — toda a interface hoje usa só WinForms, que roda em
  qualquer engine, sem nenhuma instalação extra. Isso não muda nada deste
  guia — autenticação/DPAPI funcionam igual nos dois engines.

## Passo a passo — gerar o token (uma vez por computador/usuário)

1. Acesse, logado como `Arcanjog1`:
   <https://github.com/settings/personal-access-tokens/new>
   (token **fine-grained**, não o clássico).
2. **Token name:** algo como `pyrevit-loader`.
3. **Expiration:** escolha um prazo (ex.: 90 dias) ou "No expiration".
   Prazos mais curtos são mais seguros, mas exigem gerar um token novo
   periodicamente.
4. **Resource owner:** `Arcanjog1`.
5. **Repository access:** "Only select repositories" → selecione
   `MeuBotao.pushbutton` **e** `AbrirModeladorExterno.pushbutton`.

   > Cada botão tem seu próprio repositório desde 2026-08-27 (o antigo
   > `ModulacaoAutomatica`, que reunia os dois, foi desativado). Um único
   > token com leitura nos **dois** atende os dois botões — mas cada um
   > guarda sua própria cópia dele (ver abaixo), então o mesmo valor é
   > colado duas vezes, uma por botão.
6. **Permissions → Repository permissions → Contents:** defina como
   **Read-only**. Nenhuma outra permissão é necessária — não marque
   nada além disso.
7. Clique em **Generate token** e copie o valor (começa com
   `github_pat_...`). **Ele só aparece uma vez** — se perder, é preciso
   gerar outro.
8. **Nunca** cole esse token em um chat, e-mail ou qualquer lugar fora
   da própria caixa de diálogo do Revit/pyRevit. Cole-o **somente** na
   janela que o botão abre pedindo o token.

## O que acontece depois de colar o token

- O loader salva o token **criptografado** (Windows DPAPI, ligado à
  conta do Windows do usuário) em:
  ```
  %LOCALAPPDATA%\MeuBotaoPushbutton\token.dat
  ```
  (o botão **Abrir Modelador Externo** usa a pasta irmã
  `%LOCALAPPDATA%\AbrirModeladorExternoPushbutton\` — são cofres separados,
  um por botão, e por isso o token é pedido uma vez em cada.)
  Ele não é salvo em texto puro e não fica dentro da pasta do
  repositório/extensão — não há risco de ser commitado por engano.
- Nas próximas execuções, o loader reusa esse token automaticamente e
  não pergunta de novo — a menos que o token seja revogado/expire (aí
  ele detecta o erro 401 e pede um novo).
- Uma cópia espelhada de todo o pacote `core/` baixado com sucesso fica em
  cache local:
  ```
  %LOCALAPPDATA%\MeuBotaoPushbutton\pkg_cache\core\...
  ```
  Se a internet cair ou o GitHub estiver fora do ar, o loader roda essa
  cópia em cache (avisando que pode estar desatualizada) em vez de
  travar o botão. A sincronização só troca o cache antigo pelo novo
  depois que **todos** os arquivos baixarem com sucesso — nunca fica pela
  metade.

## Cada computador/usuário precisa do seu próprio token

O token fica salvo por usuário do Windows, então cada pessoa que for
usar o botão em cada máquina precisa gerar (ou receber com cautela) um
token próprio com acesso de leitura ao repositório. Adicionar alguém
como colaborador do repositório no GitHub e pedir que gere seu próprio
fine-grained PAT é a forma recomendada — evita compartilhar o mesmo
token entre pessoas.

## Revogar / trocar o token

- **No GitHub:** Settings → Developer settings → Personal access
  tokens → Fine-grained tokens → localizar o token → "Delete"
  (revoga imediatamente).
- **No computador:** apague o arquivo
  `%LOCALAPPDATA%\ModulacaoAutomatica\token.dat` — o loader vai pedir um
  token novo na próxima execução.

## Solução de problemas

| Sintoma | Causa provável |
| --- | --- |
| "Token invalido ou expirado (HTTP 401)" | Token errado, expirado ou revogado. O loader já tenta pedir um novo automaticamente. |
| "Acesso negado ... (HTTP 403)" | Token sem permissão de `Contents: Read` neste repositório, ou repositório errado no PAT. |
| "... nao encontrado no repositorio (HTTP 404)" | Caminho/branch mudou no GitHub e não foi atualizado nas constantes `GITHUB_OWNER`/`GITHUB_REPO`/`GITHUB_BRANCH` no topo do [`Script.py`](Script.py). |
| "A API do GitHub truncou a listagem da arvore..." | O pacote `core/` cresceu além do limite de uma chamada `recursive=1` da API do Git (muito raro) — avise o mantenedor. |
| Roda uma versão claramente desatualizada, sem erro nenhum | Provavelmente caiu no cache local (sem internet/GitHub fora do ar) — a mensagem de alerta do loader informa isso. |
| `IronPython Traceback` / `ImportError: No module named core.engine.geometry` (ou qualquer outro `core.xxx`) | O `Script.py` **local** (na pasta do botão dentro da extensão do pyRevit nesse computador) está desatualizado e ainda não tem `#! python3` como primeira linha — o botão continua rodando no engine **IronPython** padrão em vez do CPython. Diferente do pacote `core/`, o `Script.py` **não é baixado automaticamente** pelo loader (ver "Por que um loader?" acima) — ele precisa ser atualizado manualmente nessa máquina sempre que mudar no GitHub. Copie o [`Script.py`](Script.py) atual do repositório para a pasta `MeuBotao.pushbutton` da extensão instalada e clique em **Reload** no pyRevit (ou reinicie o Revit) para o pyRevit reler a primeira linha e trocar de engine. A mensagem de erro no formato `ImportError: No module named X` (sem aspas no nome do módulo) é a assinatura do IronPython/Python 2 — se o CPython estivesse rodando, o erro seria `ModuleNotFoundError: No module named 'X'` (com aspas). |
| Clicar em **Reload** do pyRevit (não o botão do painel) dá `IronPython Traceback` terminando em `StandardError: Exception has been thrown by the target of an invocation.`, com um `Script Executor Traceback` apontando para `System.PlatformNotSupportedException: BinaryFormatter serialization and deserialization have been removed`, dentro de `PythonEngine.Shutdown()` / `RuntimeData.Stash()` / `CPythonEngine.Shutdown()` (`sessionmgr.py` → `_clear_running_engines`) | Isso **não é um erro do `Script.py` nem do pacote `core/`** — é uma falha interna do pyRevit ao desligar o engine CPython (pythonnet) para recarregar. Depois que o botão roda pelo menos uma vez com `#! python3`, o pyRevit mantém esse engine CPython carregado; ao clicar **Reload**, ele tenta salvar o estado do engine via `BinaryFormatter`, API que a Microsoft **removeu** do .NET (a partir do .NET 8/9, sem flag de compatibilidade que reative — ver [pythonnet#2469](https://github.com/pythonnet/pythonnet/issues/2469) e [dotnet/runtime#119631](https://github.com/dotnet/runtime/issues/119631)). É uma incompatibilidade entre a versão do pythonnet embutida no pyRevit instalado e a versão do .NET/host que o Revit está usando nessa máquina. **Contorno confiável (o único sob nosso controle):** em vez de clicar em Reload depois de já ter rodado o botão, **feche e reabra o Revit** — isso recria os engines do zero (processo novo) e evita passar pelo caminho de shutdown problemático. Atualizar o pyRevit **não é garantia**: o `BinaryFormatter` que quebra está compilado dentro do binário do pyRevit (`Python.Runtime.dll`, do pythonnet, embutido em `PyRevitLabs.PyRevit.Runtime.dll`), então só ajudaria se/quando os mantenedores do pyRevit publicarem uma build já linkada contra uma versão do pythonnet sem esse `Stash()` via `BinaryFormatter` — não há confirmação de que isso já foi lançado, nem existe hoje uma flag/variável de ambiente pública para desligar esse `Stash()` (há um pedido aberto sem solução em [pythonnet#2622](https://github.com/pythonnet/pythonnet/issues/2622)). E em .NET 9 a própria Microsoft removeu qualquer flag de compatibilidade do `BinaryFormatter` — não tem "reativar" por configuração. Não há nada a mudar neste repositório para evitar isso: o problema é do ambiente pyRevit/.NET instalado no PC, não do loader ou do `core/`. |
