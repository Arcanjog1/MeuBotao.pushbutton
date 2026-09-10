# Benchmark — caminhos oficiais preservados

Este diretório é um índice. O pacote importável continua em nuvem/benchmark,
sem mover dados, regenerar input ou mudar baseline.

- [Contrato](../docs/REFERENCE_CORPUS.md)
- [Manual e comandos](../nuvem/benchmark/README.md)
- [Manifesto](../nuvem/benchmark/golden/manifest.json)
- [Snapshot medido, histórico](../docs/CURRENT_REFERENCE_SNAPSHOT.md)
- [Oficiais](official/README.md), [validadores](validators/README.md),
  [reprodutores](reproducers/README.md), [diagnósticos](diagnostics/README.md)

Oficial significa integrado, não perfeito/GOLDEN.
--save-baseline e --calibrate escrevem oficiais: exigem autorização específica,
não são onboarding. Preferir write_files=False quando suportado.
Não executar regressão longa para reorganizar Markdown.
