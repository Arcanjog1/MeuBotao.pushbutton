# Evidência Revit real — estratégia CHANNEL (2026-09-14)

Revit 2026 (26.4.10.51), MCP pyRevit Routes porta 48884 (IronPython 2.7).
Documentos: HUMANO `BUTANTÃ - R08_LT (TODOS OS PAVIMENTOS PARA ENVIO) (1).rvt`
(somente leitura; `IsModified=false` antes e depois de toda execução) e
TARGET `butanta testes.rvt` (bancada; 44 aberturas no 2º PAVIMENTO, iguais às
do 1º PAV humano em posição/largura/altura/peitoril).

- `q01..q06`: identificação dos documentos, inventário de famílias, geometria das
  famílias de canaleta no humano, aberturas e níveis do TARGET, sólido da KV de 4 cm.
- `r_case*.json`: casos A (porta), B (janela sup+inf), D (T com travessia), F
  (passagem livre); A com duas execuções (idempotência).
- `r_ladder_{1,3,5,10,20,34}.json`: escada de escala com criação e releitura;
  `r_ladder_34_run2.json`: sessão nova sem limpeza (idempotência 7.229 → 7.229).
- `_harness/`: scripts enviados ao MCP (`run.sh` concatena `rvlib_head.py` +
  script; `r_channel.py` lê `r_cfg.json`). Caminhos absolutos da máquina de teste.

Os blocos criados pela bancada levam o carimbo
`MODULACAO_AUTOMATICA|parede=CHANNELBENCH-<eixo>|lote=...` (sem Walls no TARGET;
o dono é a chave física do eixo). O TARGET não foi salvo.
