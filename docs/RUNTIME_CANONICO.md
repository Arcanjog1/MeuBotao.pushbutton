# Runtime canônico: um comportamento, dois canais, um SHA comprovável

Estado a partir de 2026-09-23 (main é a fonte canônica; PR #49 mesclado).

## 1. Uma regra, dois modos de carregamento

| | BETA_OFFLINE | ONLINE |
|---|---|---|
| origem do código | pasta do botão (`core/`, `Script.py`, `beta_package.py`, `beta-package.json`) | `%LOCALAPPDATA%\MeuBotaoPushbutton\pkg_cache\` sincronizado do GitHub |
| prova do SHA | `beta-package.json` (`head` = SHA completo) + sha256 de cada arquivo, verificados pelo `beta_package.py` **antes** de importar qualquer módulo | commit resolvido pela API (`commits/main`), árvore baixada **pinada no SHA**, `manifest.json` com sha256 de cada arquivo |
| regra 48 | **a mesma**: `_materialization_gate` → laudo → FATAL bloqueia a RUN → plano peça a peça → conferência do que fica | **a mesma** |
| Finalizar | `finalize_allowed` (laudo sem erro fatal + conjunto conferido; parede com peça pulada fica retida) | **o mesmo** |
| diferença | grupo transacional externo que restaura o lote anterior se qualquer passo falhar | criação em transações simples |

Contrato (idêntico nos dois canais, testado uma vez por canal em
`tests/test_materializacao_e_estado_da_run.py`, `CANAIS`):

- peça com sobreposição real > 0,1 cm com abertura (planta **e** altura) → **não é criada**;
- se era amarração real (razão de encontro do solver **e** B34/B54) → **amarração NÃO resolvida**
  (`BOND_UNRESOLVED`: parede, nó, fiada, `rule_id`, sobreposição, revisão humana obrigatória);
- B34/B54 sem papel, compensador 76.1 e canaleta **nunca** são amarração;
- demais peças válidas continuam sendo materializadas; só `FATAL_RUN_ERROR` bloqueia a RUN inteira;
- planejadas = criadas + puladas + falhas.

## 2. O que o botão imprime no início (banner de proveniência)

```
MODULAÇÃO AUTOMÁTICA
canal=ONLINE
branch=main
commit=<SHA COMPLETO>
cache=VALIDATED | MISS | OFFLINE_FALLBACK
CHANNEL=ONLINE
SOURCE_BRANCH=main
RESOLVED_COMMIT=<SHA COMPLETO>
PACKAGE_SHA=<sha256 do conjunto core/>
CACHE_STATUS=...
LOADER_PATH=<caminho do Script.py>
CORE_PATH=<caminho do core/wall_modeling.py carregado>
```

```
MODULAÇÃO AUTOMÁTICA
canal=BETA_OFFLINE
commit=<SHA COMPLETO>
package_verified=true
CHANNEL=BETA_OFFLINE ... CACHE_STATUS=VERIFIED_OFFLINE ...
```

A mesma informação aparece na linha `Versão:` do relatório da modulação e no
cabeçalho do log do solver. **Dois computadores rodam o mesmo código quando
mostram o mesmo `RESOLVED_COMMIT`** (e, para o mesmo commit, o mesmo
`PACKAGE_SHA`, que cobre só `core/` e é calculado igual nos dois canais).

Cache nunca é silencioso: `VALIDATED` = commit atual da branch e hashes
conferidos; `MISS` = ressincronizado agora; `OFFLINE_FALLBACK` = sem rede, cache
verificado, **commit informado é o do cache** (pode estar desatualizado). Cache
sem manifest ou com hash divergente não roda.

## 3. Gerar o pacote canônico (a partir da main)

```powershell
git -C C:\int42 fetch origin
$SHA = git -C C:\int42 rev-parse origin/main
python C:\int42\tools\beta\build_package.py --head $SHA --output C:\BetaRevit\modulacao-main-$($SHA.Substring(0,7)) --branch main --zip
python -B -c "import sys; sys.path.insert(0, r'C:\int42'); from beta_package import verify_beta_package; print(verify_beta_package(r'C:\BetaRevit\modulacao-main-<sha7>'))"
```

Nome: `modulacao-main-<sha7>.zip` (o manifest traz `head`, `branch`,
`package_name`). O pacote antigo `pacote_pr49.zip` (HEAD `09cfdd0`) está
**OBSOLETO**: contém a política de materialização errada do `aa70d0d`.

## 4. Instalar/atualizar em cada computador

O caminho da pasta do botão pode ser diferente em cada máquina; o que tem de
ser igual é o `commit=` do banner.

**PC CIVIX** — botão conhecido:
`C:\Users\CIVIX\OneDrive\Área de Trabalho\Scripts.extension\MinhaAba.tab\MeuPainel.panel\MeuBotao_PR49.pushbutton`

1. Feche o Revit (ou garanta que nenhuma janela da modulação está aberta).
2. Dentro da pasta do botão apague `core\`, `Script.py`, `beta_package.py`,
   `beta-package.json` e qualquer `__pycache__`. Não deixe arquivo antigo: o
   verificador recusa `.py` extra em `core\`.
3. Extraia o conteúdo do `modulacao-main-<sha7>.zip` **direto** na pasta do
   botão (o zip não tem pasta raiz: `Script.py` fica ao lado do `icon.png`).
4. pyRevit → Reload (ou reinicie o Revit).
5. Clique no botão e confira, na janela de saída, `canal=BETA_OFFLINE` e
   `commit=<SHA da main>`. Se aparecer erro de manifest/hash: **pare**, não
   caia em cache nem em download.

(Opcional: renomear a pasta para `MeuBotao_main.pushbutton` — o pyRevit usa o
nome da pasta como nome do botão; o conteúdo é o mesmo.)

**PC twitc** — botões de desenvolvimento (caminhos podem variar; o de teste
usado nesta sessão é
`C:\Users\twitc\Desktop\Scripts.extension\MinhaAba.tab\MeuPainel.panel\teste-perf.pushbutton`):
mesmos passos 1–5. Verificação sem abrir o Revit:

```powershell
python -B -c "import sys; sys.path.insert(0, r'<pasta do botão>'); from beta_package import verify_beta_package; print(verify_beta_package(r'<pasta do botão>'))"
```

**Modo ONLINE** (qualquer PC, botão sem pacote offline): basta o `Script.py`
atual na pasta do botão; o banner mostra `canal=ONLINE commit=<SHA>`. Dois PCs
online no mesmo instante mostram o mesmo commit se a main não mudou entre os
cliques — o banner é a prova, não a suposição.

## 5. Antes de um clique humano

- Documento de teste: **cópia**, nunca os três RVTs de referência
  (`butanta testes`, `TESTE PR49`, `BUTANTÃ - R08_LT ...`).
- Conferir no banner o `commit=`; na Etapa 1, avançar e voltar mantém a
  configuração; a criação fica disponível sem `FATAL_RUN_ERROR`; o relatório
  mostra "Peças que NÃO serão criadas", "Amarrações NÃO resolvidas" e
  "Contabilidade fecha: sim"; "Canaleta exercendo amarração" = 0.
