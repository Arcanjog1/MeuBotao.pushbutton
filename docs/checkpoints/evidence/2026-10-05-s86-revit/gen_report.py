# -*- coding: utf-8 -*-
"""Relatorio visual (HTML) da aproximacao do humano: elevacoes de TODAS as paredes, motor x humano, fiada a fiada,
com as pecas iguais ao humano marcadas. Uso: py -3 gen_report.py CANDIDATO_rows.json META.json OUT.html
META: {"steps": [[rotulo, f1, pecas, quebrados, septos, pastilhas], ...], "rules": [[id, texto, estado], ...],
       "pending": [texto, ...], "notes": [texto, ...], "date": "..."}"""
import json, sys, os, html
sys.path.insert(0, "C:/Users/CIVIX/AppData/Local/Temp/s85r4")
import r2_eval as E

cand = json.load(open(sys.argv[1]))
meta = json.load(open(sys.argv[2], encoding="utf-8"))
hum = json.load(open("C:/Users/CIVIX/AppData/Local/Temp/s85r4/human_rows_unpad.json"))
OUT = sys.argv[3]


def walls(d):
    out = {}
    for k, v in d["rows"].items():
        w, c = [int(x) for x in k.split(":")]
        out.setdefault(w, {})[c] = sorted(v)
    return out


C, H = walls(cand), walls(hum)


def norm(code):
    return code.split("_H9")[0]


def side(it):
    if it[2].startswith("B34") and it[3]:
        sm = min(it[3], key=lambda c: c[1] - c[0])
        return 1 if (sm[0] + sm[1]) / 2.0 > (it[0] + it[1]) / 2.0 else -1
    return 0


def match(hs, cs):
    """indices casados (1:1, mesmo codigo e lado, centro +-2 cm) -> (set humano, set candidato)"""
    used, mh = set(), set()
    for i, it in enumerate(hs):
        ctr = (it[0] + it[1]) / 2.0
        best = None
        for j, x in enumerate(cs):
            if j in used or norm(x[2]) != norm(it[2]) or side(x) != side(it):
                continue
            d = abs((x[0] + x[1]) / 2.0 - ctr)
            if d <= 2.0 and (best is None or d < best[0]):
                best = (d, j)
        if best:
            used.add(best[1])
            mh.add(i)
    return mh, used


def kind(code):
    if code.startswith("CHANNEL"):
        return "u"
    if code in ("C04", "C09") or code.startswith("C0"):
        return "c"
    if code == "B19":
        return "h"
    if code == "B54":
        return "n"
    if code == "B34":
        return "s"
    return "b"


def label(it):
    code = it[2].replace("CHANNEL_U_", "U")
    if code == "B34":
        code += "›" if side(it) > 0 else "‹"
    return code


COURSE_H = 20.0
NC = 13
CHUNK = 820.0


def svg_rows(rows, matched, openings, lo, hi, title):
    w = hi - lo
    hh = NC * COURSE_H
    parts = ['<svg class="el" viewBox="%.1f %.1f %.1f %.1f" role="img" aria-label="%s">'
             % (lo - 6, -4, w + 12, hh + 22, html.escape(title))]
    for o in openings:
        a, b, sill, top = o[0], o[1], o[2], o[3]
        if b < lo or a > hi:
            continue
        y0 = hh - min(top, hh)
        parts.append('<rect class="op" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                     % (a, y0, b - a, min(top, hh) - sill))
    for c in range(NC):
        y = hh - (c + 1) * COURSE_H
        for k, it in enumerate(rows.get(c, [])):
            if it[1] < lo or it[0] > hi:
                continue
            ok = (c, k) in matched
            cls = kind(it[2]) + (" m" if ok else " x")
            parts.append('<g class="%s"><title>f%d %s [%g–%g]%s</title><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                         % (cls, c, label(it), round(it[0]), round(it[1]), " igual ao humano" if ok else "",
                            it[0] + 0.4, y + 0.6, it[1] - it[0] - 0.8, COURSE_H - 1.2))
            for cl in it[3] or []:
                parts.append('<rect class="cv" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                             % (cl[0], y + 4.5, max(cl[1] - cl[0], 0.5), COURSE_H - 9))
            if it[1] - it[0] >= 18:
                parts.append('<text x="%.1f" y="%.1f">%s</text>' % ((it[0] + it[1]) / 2.0, y + 13.2, html.escape(label(it))))
            parts.append('</g>')
    parts.append('<line class="gr" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (lo, hi, hh, hh))
    for t in range(int(lo // 100) * 100, int(hi) + 1, 100):
        if t < lo - 1:
            continue
        parts.append('<text class="tk" x="%d" y="%.1f">%d</text>' % (t, hh + 14, t))
    parts.append("</svg>")
    return "".join(parts)


# ---------- metricas por parede
per = []
tot_m = tot_h = tot_c = 0
blocks = []
for w in sorted(set(C) | set(H)):
    cr, hr = C.get(w, {}), H.get(w, {})
    mc, mh_ = set(), set()
    nm = nh = nc = 0
    for c in range(NC + 1):
        hs, cs = hr.get(c, []), cr.get(c, [])
        a, b = match(hs, cs)
        nm += len(a)
        nh += len(hs)
        nc += len(cs)
        mh_.update((c, i) for i in a)
        mc.update((c, j) for j in b)
    tot_m += nm
    tot_h += nh
    tot_c += nc
    L = max([it[1] for v in list(cr.values()) + list(hr.values()) for it in v] or [0])
    per.append((w, nm, nh, nc, L))
    ops = cand["openings"][w] if w < len(cand["openings"]) else []
    hops = hum["openings"][w] if w < len(hum["openings"]) else []
    chunks = []
    t = 0.0
    n_chunks = max(1, int((L + 0.5) // CHUNK) + (1 if (L % CHUNK) > 0.5 else 0))
    size = L / n_chunks if n_chunks else L
    for i in range(n_chunks):
        lo, hi = i * size, min(L, (i + 1) * size)
        chunks.append((lo, hi))
    body = []
    for lo, hi in chunks:
        rng = "" if len(chunks) == 1 else '<span class="rng">trecho %d–%d cm</span>' % (lo, hi)
        body.append('<div class="pair">%s<div class="lab">Motor</div>%s<div class="lab">Humano</div>%s</div>'
                    % (rng, svg_rows(cr, mc, ops, lo, hi, "W%d motor" % w), svg_rows(hr, mh_, hops, lo, hi, "W%d humano" % w)))
    pct = 100.0 * nm / nh if nh else 0
    blocks.append('<section class="wall" id="w%d"><header><h3>W%d</h3><span class="len">%d cm</span>'
                  '<span class="score %s">%d%% igual · %d de %d peças</span></header>%s</section>'
                  % (w, w, round(L), "hi" if pct >= 75 else ("md" if pct >= 40 else "lo"), round(pct), nm, nh, "".join(body)))

P = tot_m / float(tot_c) if tot_c else 0
R = tot_m / float(tot_h) if tot_h else 0
F = 2 * P * R / (P + R) if P + R else 0

# ---------- HTML
steps_rows = "".join('<tr%s><td>%s</td><td class="num">%s</td><td class="num">%s</td><td class="num">%s</td>'
                     '<td class="num">%s</td><td class="num">%s</td></tr>'
                     % tuple([' class="ref"' if s[1] is None else (' class="fin"' if s is meta["steps"][-2] else ''),
                              html.escape(s[0]), "—" if s[1] is None else "%.1f%%" % s[1]] + list(s[2:]))
                     for s in meta["steps"])
bars = "".join('<div class="bar"><span class="bl">%s</span><span class="bt"><i style="width:%.1f%%"></i></span>'
               '<span class="bv">%.1f%%</span></div>' % (html.escape(s[0]), 100.0 * s[1] / 100.0, s[1]) for s in meta["steps"] if s[1] is not None)
rules = "".join('<li><span class="rid">%s</span><span class="rtx">%s</span><span class="st st-%s">%s</span></li>'
                % (html.escape(r[0]), html.escape(r[1]), r[3] if len(r) > 3 else "ok", html.escape(r[2])) for r in meta["rules"])
pend = "".join("<li>%s</li>" % html.escape(p) for p in meta["pending"])
notes = "".join("<li>%s</li>" % html.escape(p) for p in meta.get("notes", []))
chips = "".join('<a class="chip %s" href="#w%d">W%d <b>%d%%</b></a>'
                % ("hi" if (100.0 * nm / nh if nh else 0) >= 75 else ("md" if (100.0 * nm / nh if nh else 0) >= 40 else "lo"),
                   w, w, round(100.0 * nm / nh) if nh else 0) for w, nm, nh, nc, L in per)

CSS = """
:root{
  /* Layout: relatorio de prancha - resumo no topo, depois as 34 elevacoes empilhadas (motor sobre humano) */
  --bg:#f3f5f6; --panel:#ffffff; --ink:#1d2428; --mute:#5d6970; --line:#d5dbde;
  --accent:#1f6f78; --accent-soft:#d7eaec;
  --blk:#c9ced1; --b34:#dfe3e5; --b19:#b9c9d6; --b54:#a9b1b6; --cmp:#e6c37a; --ch:#8fb3c9;
  --cell:#f3f5f6; --miss:#c2412d; --ok:#2f7d4f; --mid:#b07a1f; --op:#ffffff;
  --display:"Archivo","Arial Narrow",Arial,sans-serif; --body:"Public Sans","Segoe UI",Arial,sans-serif;
  --mono:"JetBrains Mono",Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#12171a; --panel:#1a2125; --ink:#e3e8ea; --mute:#9aa6ac; --line:#2c363b;
  --accent:#5fb7c0; --accent-soft:#1d3a3e;
  --blk:#5a6368; --b34:#6c767b; --b19:#4f6676; --b54:#7d878c; --cmp:#9c7c35; --ch:#456b82;
  --cell:#12171a; --miss:#ff7a62; --ok:#6cc48f; --mid:#e0ad52; --op:#1a2125; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#12171a; --panel:#1a2125; --ink:#e3e8ea; --mute:#9aa6ac; --line:#2c363b;
  --accent:#5fb7c0; --accent-soft:#1d3a3e;
  --blk:#5a6368; --b34:#6c767b; --b19:#4f6676; --b54:#7d878c; --cmp:#9c7c35; --ch:#456b82;
  --cell:#12171a; --miss:#ff7a62; --ok:#6cc48f; --mid:#e0ad52; --op:#1a2125; color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:15px/1.55 var(--body);}
.wrap{max-width:1180px;margin:0 auto;padding-inline:20px;padding-block:28px 64px;display:flex;flex-direction:column;gap:28px}
h1,h2,h3{font-family:var(--display);text-wrap:balance;margin:0;letter-spacing:.01em}
h1{font-size:2.1rem;font-weight:700}
h2{font-size:1.25rem;font-weight:700;margin-bottom:12px}
h3{font-size:1.05rem}
.lede{color:var(--mute);max-width:68ch;margin:6px 0 0}
.eyebrow{font:600 .72rem/1 var(--mono);text-transform:uppercase;letter-spacing:.12em;color:var(--accent)}
.grid2{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:20px}
@media (max-width:820px){.grid2{grid-template-columns:minmax(0,1fr)}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px 20px;min-width:0}
.big{display:flex;gap:28px;flex-wrap:wrap;align-items:baseline}
.big div{display:flex;flex-direction:column}
.big b{font:700 2.4rem/1 var(--display);color:var(--accent);font-variant-numeric:tabular-nums}
.big span{color:var(--mute);font-size:.85rem}
.bar{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr) 4rem;gap:10px;align-items:center;font-size:.85rem;margin-top:6px}
.bt{height:12px;background:var(--accent-soft);border-radius:2px;overflow:hidden}
.bt i{display:block;height:100%;background:var(--accent)}
.bv{font:600 .85rem var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}
th{font:600 .72rem var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
td.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
tr.fin td{font-weight:600;color:var(--accent)} tr.ref td{color:var(--mute)}
ul.rules{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px}
ul.rules li{display:grid;grid-template-columns:3.2rem minmax(0,1fr) auto;gap:10px;align-items:start}
.rid{font:700 .8rem var(--mono);color:var(--accent)}
.st{font:600 .7rem var(--mono);padding:2px 8px;border-radius:99px;border:1px solid currentColor;white-space:nowrap}
.st-ok{color:var(--ok)} .st-pend{color:var(--mid)} .st-no{color:var(--miss)}
ul.plain{margin:0;padding-left:1.1rem;display:flex;flex-direction:column;gap:6px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:.8rem;color:var(--mute)}
.legend i{display:inline-block;width:18px;height:11px;border-radius:2px;vertical-align:-1px;margin-right:5px;border:1px solid var(--line)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:600 .75rem var(--mono);text-decoration:none;color:var(--ink);border:1px solid var(--line);background:var(--panel);
  padding:3px 8px;border-radius:4px;display:inline-flex;gap:6px}
.chip b{font-variant-numeric:tabular-nums}
.chip.hi b{color:var(--ok)} .chip.md b{color:var(--mid)} .chip.lo b{color:var(--miss)}
.chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wall{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px;min-width:0;scroll-margin-top:12px}
.wall header{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;margin-bottom:8px}
.len{font:.8rem var(--mono);color:var(--mute)}
.score{font:600 .8rem var(--mono);margin-left:auto}
.score.hi{color:var(--ok)} .score.md{color:var(--mid)} .score.lo{color:var(--miss)}
.pair{display:flex;flex-direction:column;gap:2px;margin-top:8px;overflow-x:auto}
.rng{font:.75rem var(--mono);color:var(--mute)}
.lab{font:600 .7rem var(--mono);text-transform:uppercase;letter-spacing:.1em;color:var(--mute);margin-top:4px}
svg.el{width:100%;min-width:560px;height:auto;display:block}
svg.el rect{stroke-width:.7}
svg.el g.b rect:first-of-type{fill:var(--blk)} svg.el g.s rect:first-of-type{fill:var(--b34)}
svg.el g.h rect:first-of-type{fill:var(--b19)} svg.el g.n rect:first-of-type{fill:var(--b54)}
svg.el g.c rect:first-of-type{fill:var(--cmp)} svg.el g.u rect:first-of-type{fill:var(--ch)}
svg.el g.m rect:first-of-type{stroke:var(--ink);stroke-opacity:.35}
svg.el g.x rect:first-of-type{stroke:var(--miss);stroke-width:1.6}
svg.el rect.cv{fill:var(--cell);stroke:none;opacity:.75}
svg.el rect.op{fill:var(--op);stroke:var(--mute);stroke-dasharray:3 2;stroke-width:.8}
svg.el text{font:5.2px var(--mono);fill:var(--ink);text-anchor:middle;pointer-events:none}
svg.el text.tk{font-size:7px;fill:var(--mute)}
svg.el line.gr{stroke:var(--mute);stroke-width:.6}
footer{color:var(--mute);font-size:.8rem}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
html{scroll-behavior:smooth}
"""

page = """<title>Butantã × Humano</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=JetBrains+Mono:wght@400;600;700&family=Public+Sans:wght@400;600&display=swap">
<style>%s</style>
<div class="wrap">
<header>
  <div class="eyebrow">Modulação automática · 1º pavimento · %s</div>
  <h1>Butantã × Humano</h1>
  <p class="lede">Comparação do cálculo do motor com o projeto humano BUTANTÃ R08_LT, peça a peça e fiada a fiada.
  Uma peça conta como igual quando tem o mesmo código, o mesmo lado do vazado menor (B34) e o centro a até 2 cm.
  Nenhuma peça foi copiada: o motor chegou aqui pelas regras.</p>
</header>
<div class="grid2">
  <section class="panel">
    <h2>Semelhança com o humano</h2>
    <div class="big"><div><b>%.1f%%</b><span>F1 de peças</span></div><div><b>%d</b><span>peças iguais de %d do humano</span></div>
    <div><b>%d</b><span>peças do motor</span></div></div>
    %s
  </section>
  <section class="panel">
    <h2>Qualidade (fiadas 0–11, régua independente)</h2>
    <div class="tbl"><table><thead><tr><th>Etapa</th><th>F1</th><th>Peças</th><th>Furos quebrados</th><th>Septos sem apoio</th><th>Pastilhas</th></tr></thead>
    <tbody>%s</tbody></table></div>
  </section>
</div>
<section class="panel"><h2>Regras aplicadas</h2><ul class="rules">%s</ul></section>
<div class="grid2">
  <section class="panel"><h2>Pendente de decisão</h2><ul class="plain">%s</ul></section>
  <section class="panel"><h2>Observações</h2><ul class="plain">%s</ul></section>
</div>
<section class="panel">
  <h2>Paredes</h2>
  <div class="legend"><span><i style="background:var(--blk)"></i>B39</span><span><i style="background:var(--b34)"></i>B34 (‹ › lado do vazado menor)</span>
  <span><i style="background:var(--b19)"></i>B19</span><span><i style="background:var(--b54)"></i>B54</span><span><i style="background:var(--cmp)"></i>C04/C09</span>
  <span><i style="background:var(--ch)"></i>Canaleta</span><span><i style="border:1.6px solid var(--miss)"></i>diferente do humano</span>
  <span><i style="border:1px dashed var(--mute);background:var(--op)"></i>abertura</span></div>
  <div class="chips" style="margin-top:12px">%s</div>
</section>
%s
<footer>Gerado a partir do cálculo offline do motor (mesmas regras que o Revit usa). Passe o mouse sobre uma peça para ver fiada, código e posição.</footer>
</div>""" % (CSS, html.escape(meta.get("date", "")), 100 * F, tot_m, tot_h, tot_c, bars, steps_rows, rules, pend, notes, chips, "".join(blocks))
open(OUT, "w", encoding="utf-8").write(page)
print("F1 %.1f%% iguais %d humano %d candidato %d | %s %.1f MB" % (100 * F, tot_m, tot_h, tot_c, OUT, os.path.getsize(OUT) / 1e6))
