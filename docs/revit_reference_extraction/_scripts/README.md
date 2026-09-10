# Scripts históricos — TORRE EASY
STATUS: HISTORICAL. Evidência da análise, não pipeline autossuficiente.

Os geradores Python foram lidos estaticamente nesta missão, sem execução.
Dependem de raw/*.ndjson, ausente do Git; gen2.py também depende de pre.py,
ausente. gen.py contém destino absoluto do ambiente original.
gen3/gen5/gen6/val executam outros geradores e gravam JSON: não importar como biblioteca.
lib.py faz leitura de arquivos, não acessa o Revit. Estes sete arquivos não
contêm o coletor original MCP, portanto não provam sozinhos a ausência de
transações na sessão histórica. A leitura read-only é proveniência relatada.

Não executar para validar o acervo. A validação offline lê os JSON publicados.
Recuperar raw e pre.py com sua proveniência antes de prometer regeneração integral.
