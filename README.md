# MeuBotao.pushbutton

Repositorio independente do botao `MeuBotao.pushbutton` para pyRevit.

Esta raiz ja contem tudo que o botao precisa para funcionar sem depender de
`ModulacaoAutomatica` nem de `AbrirModeladorExterno.pushbutton`:

- `Script.py`: loader CPython do pyRevit.
- `core/`: motor real de modulacao e dependencias internas.
- `tests/`: suite offline com stubs de Revit/pyRevit.
- documentos de arquitetura e regras da modulacao.

O loader baixa atualizacoes do pacote `core/` deste proprio repositorio
GitHub (`Arcanjog1/MeuBotao.pushbutton`) e usa cache local em
`%LOCALAPPDATA%\MeuBotaoPushbutton`.

## Testes

```powershell
py -m pytest tests -q
```

ou:

```powershell
py tests\run_tests.py
```
