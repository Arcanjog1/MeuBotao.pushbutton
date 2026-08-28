# Loader do GitHub — senha de acesso e token cifrado

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
- Como os repositórios são **privados**, o download exige um token de
  acesso (PAT) do GitHub. Só que **o usuário não digita token nenhum**:
  ele digita apenas uma **senha**, que abre o token já embutido
  (cifrado) no loader — ver a seção seguinte.
- **Engine CPython:** a primeira linha de `Script.py` é `#! python3` — o
  botão roda no engine CPython do pyRevit (não mais o IronPython padrão).
  A UI interativa em PySide6 que motivou essa troca foi **removida**
  (2026-08-26) — toda a interface hoje usa só WinForms, que roda em
  qualquer engine, sem nenhuma instalação extra. Isso não muda nada deste
  guia — autenticação/DPAPI funcionam igual nos dois engines.

## Como funciona a senha (2026-08-28)

Antes, cada pessoa precisava gerar um PAT no GitHub e colá-lo na janela do
botão. Agora:

1. **Você (mantenedor)** gera **um** token fine-grained de leitura e o
   cifra com uma senha escolhida por você — uma vez só, ver abaixo.
2. A linha cifrada (`MB1$...`) vai para dentro do loader, na constante
   `TOKEN_CIFRADO` (ou no arquivo `token_cifrado.dat`, ao lado do
   `Script.py`, que tem prioridade sobre a constante).
3. **O usuário** só digita a **senha**, uma vez por computador. O loader
   decifra o token em memória, baixa o `core/` e salva o token decifrado
   com DPAPI — nas próximas execuções nada é perguntado.

> **Limite honesto desta abordagem.** Quem tiver o arquivo do loader **e**
> souber a senha consegue extrair o token — a senha é um cadeado, não um
> cofre. É por isso que o PAT usado aqui precisa ser **fine-grained**, com
> **apenas** `Contents: Read-only`, **apenas** nos dois repositórios dos
> botões. Mesmo vazando, ele não escreve nada e não alcança mais nada.
> Sem a senha, o token não é legível: PBKDF2-HMAC-SHA256 com 200 000
> iterações + HMAC de integridade (ver `ferramentas/cripto_token.py`).
>
> A senha aparece **visível** enquanto é digitada: a caixa usada
> (`Interaction.InputBox`) não tem máscara, e montar um campo de senha de
> verdade exigiria `Form.Controls.Add`, que está quebrado no engine
> CPython desta instalação do pyRevit (ver `_patch_pyrevit_forms_for_cpython`
> no `Script.py`).

## Passo 1 — gerar o token no GitHub (uma vez, só o mantenedor)

1. Acesse, logado como `Arcanjog1`:
   <https://github.com/settings/personal-access-tokens/new>
   (token **fine-grained**, não o clássico).
2. **Token name:** algo como `pyrevit-loader`.
3. **Expiration:** escolha o prazo. **Atenção:** quando o token expirar,
   todos os computadores param de baixar atualizações (caem no cache) até
   o blob ser regerado e o loader redistribuído — prazos longos dão menos
   trabalho, prazos curtos são mais seguros.
4. **Resource owner:** `Arcanjog1`.
5. **Repository access:** "Only select repositories" → selecione
   `MeuBotao.pushbutton` **e** `AbrirModeladorExterno.pushbutton`
   (um único token atende os dois botões).
6. **Permissions → Repository permissions → Contents:** **Read-only**.
   Nada além disso.
7. **Generate token** e copie o valor (`github_pat_...`). Ele só aparece
   uma vez.

## Passo 2 — cifrar o token com a senha

Na sua máquina (nunca na do usuário final), dentro do repositório:

```bash
python3 ferramentas/gerar_token_cifrado.py
```

Ele pergunta o PAT e a senha (as duas digitadas ocultas) e imprime uma
linha assim:

```
MB1$200000$Q2hh...$c2Fs...$Y2lm...$dGFn...
```

Para conferir depois que já existe um blob:

```bash
python3 ferramentas/gerar_token_cifrado.py --verificar
```

## Passo 3 — colocar a linha nos dois loaders

Duas formas (a primeira é a recomendada):

- **No código:** cole em `TOKEN_CIFRADO = "..."` no `Script.py` (deste
  repositório) **e** no `script.py` do `AbrirModeladorExterno.pushbutton`.
  Commite e distribua os loaders atualizados para os PCs (o loader é o
  único arquivo que **não** se atualiza sozinho — ver "Solução de
  problemas").
- **Fora do código:** salve a linha num arquivo `token_cifrado.dat` ao
  lado do loader, em cada PC. Ele tem prioridade sobre a constante e
  permite trocar o token sem mexer no `Script.py`.

Enquanto `TOKEN_CIFRADO` estiver **vazio** e não houver `token_cifrado.dat`,
o loader se comporta como antes (tenta baixar sem autenticação e só pede um
PAT digitado se levar 401/403) — nada quebra antes de o blob existir.

## Passo 4 — passar a senha para as pessoas

Diga a senha **por um canal direto** (pessoalmente, ligação, mensagem
privada) — não a coloque no repositório, no README nem em comentário de
código. Ela é pedida uma única vez por computador.

## O que acontece depois de digitar a senha

- O loader decifra o token e o salva **criptografado** (Windows DPAPI,
  ligado à conta do Windows do usuário) em:
  ```
  %LOCALAPPDATA%\MeuBotaoPushbutton\token.dat
  ```
  (o botão **Abrir Modelador Externo** usa a pasta irmã
  `%LOCALAPPDATA%\AbrirModeladorExternoPushbutton\` — são cofres separados,
  um por botão, e por isso a senha é pedida uma vez em cada.)
  O token nunca é escrito em texto puro, nem dentro da pasta do
  repositório/extensão.
- Nas próximas execuções o loader reusa esse token e não pergunta nada —
  a menos que ele seja revogado/expire (aí detecta o 401/403, apaga o
  token salvo e pede a senha de novo).
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

## Trocar a senha ou o token

- **Trocar a senha:** rode `gerar_token_cifrado.py` de novo com o mesmo
  token e a senha nova, substitua o blob nos loaders e redistribua. Quem
  já tiver o token salvo em DPAPI **não** será perguntado de novo (só
  quem instalar do zero, ou depois que o token expirar).
- **Revogar o token:** GitHub → Settings → Developer settings → Personal
  access tokens → Fine-grained tokens → "Delete". Gere outro, cifre e
  redistribua os loaders.
- **Forçar um PC a pedir a senha de novo:** apague
  `%LOCALAPPDATA%\MeuBotaoPushbutton\token.dat` (e o equivalente do outro
  botão).

## Solução de problemas

| Sintoma | Causa provável |
| --- | --- |
| "Senha incorreta" | A senha digitada não abre o token cifrado deste loader — confira com o responsável (o loader dá 3 tentativas). |
| "O token cifrado deste botao esta invalido ou corrompido" | A linha `MB1$...` foi colada pela metade/alterada. Gere de novo com `ferramentas/gerar_token_cifrado.py`. |
| "Token invalido ou expirado (HTTP 401)" | O token embutido expirou ou foi revogado no GitHub — gere um novo, cifre e redistribua os loaders. |
| "Acesso negado ... (HTTP 403)" | O token embutido não tem `Contents: Read` neste repositório (ou o repositório não foi marcado no PAT). |
| "... nao encontrado no repositorio (HTTP 404)" | Caminho/branch mudou no GitHub e não foi atualizado nas constantes `GITHUB_OWNER`/`GITHUB_REPO`/`GITHUB_BRANCH` no topo do [`Script.py`](Script.py). |
| "A API do GitHub truncou a listagem da arvore..." | O pacote `core/` cresceu além do limite de uma chamada `recursive=1` da API do Git (muito raro) — avise o mantenedor. |
| Roda uma versão claramente desatualizada, sem erro nenhum | Provavelmente caiu no cache local (sem internet/GitHub fora do ar) — a mensagem de alerta do loader informa isso. |
| `IronPython Traceback` / `ImportError: No module named core.engine.geometry` (ou qualquer outro `core.xxx`) | O `Script.py` **local** (na pasta do botão dentro da extensão do pyRevit nesse computador) está desatualizado e ainda não tem `#! python3` como primeira linha — o botão continua rodando no engine **IronPython** padrão em vez do CPython. Diferente do pacote `core/`, o `Script.py` **não é baixado automaticamente** pelo loader (ver "Por que um loader?" acima) — ele precisa ser atualizado manualmente nessa máquina sempre que mudar no GitHub. Copie o [`Script.py`](Script.py) atual do repositório para a pasta `MeuBotao.pushbutton` da extensão instalada e clique em **Reload** no pyRevit (ou reinicie o Revit) para o pyRevit reler a primeira linha e trocar de engine. A mensagem de erro no formato `ImportError: No module named X` (sem aspas no nome do módulo) é a assinatura do IronPython/Python 2 — se o CPython estivesse rodando, o erro seria `ModuleNotFoundError: No module named 'X'` (com aspas). |
| Clicar em **Reload** do pyRevit (não o botão do painel) dá `IronPython Traceback` terminando em `StandardError: Exception has been thrown by the target of an invocation.`, com um `Script Executor Traceback` apontando para `System.PlatformNotSupportedException: BinaryFormatter serialization and deserialization have been removed`, dentro de `PythonEngine.Shutdown()` / `RuntimeData.Stash()` / `CPythonEngine.Shutdown()` (`sessionmgr.py` → `_clear_running_engines`) | Isso **não é um erro do `Script.py` nem do pacote `core/`** — é uma falha interna do pyRevit ao desligar o engine CPython (pythonnet) para recarregar. Depois que o botão roda pelo menos uma vez com `#! python3`, o pyRevit mantém esse engine CPython carregado; ao clicar **Reload**, ele tenta salvar o estado do engine via `BinaryFormatter`, API que a Microsoft **removeu** do .NET (a partir do .NET 8/9, sem flag de compatibilidade que reative — ver [pythonnet#2469](https://github.com/pythonnet/pythonnet/issues/2469) e [dotnet/runtime#119631](https://github.com/dotnet/runtime/issues/119631)). É uma incompatibilidade entre a versão do pythonnet embutida no pyRevit instalado e a versão do .NET/host que o Revit está usando nessa máquina. **Contorno confiável (o único sob nosso controle):** em vez de clicar em Reload depois de já ter rodado o botão, **feche e reabra o Revit** — isso recria os engines do zero (processo novo) e evita passar pelo caminho de shutdown problemático. Atualizar o pyRevit **não é garantia**: o `BinaryFormatter` que quebra está compilado dentro do binário do pyRevit (`Python.Runtime.dll`, do pythonnet, embutido em `PyRevitLabs.PyRevit.Runtime.dll`), então só ajudaria se/quando os mantenedores do pyRevit publicarem uma build já linkada contra uma versão do pythonnet sem esse `Stash()` via `BinaryFormatter` — não há confirmação de que isso já foi lançado, nem existe hoje uma flag/variável de ambiente pública para desligar esse `Stash()` (há um pedido aberto sem solução em [pythonnet#2622](https://github.com/pythonnet/pythonnet/issues/2622)). E em .NET 9 a própria Microsoft removeu qualquer flag de compatibilidade do `BinaryFormatter` — não tem "reativar" por configuração. Não há nada a mudar neste repositório para evitar isso: o problema é do ambiente pyRevit/.NET instalado no PC, não do loader ou do `core/`. |
