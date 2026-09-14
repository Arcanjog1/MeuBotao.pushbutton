# -*- coding: utf-8 -*-
"""Comparador HUMANO x SOLVER CHANNEL com criterios ENDURECIDOS (auditoria
independente de 2026-09-14). Evidencia, nao norma.

Por papel (acima/abaixo) de cada vao, na janela local da corrida (corrida
humana U corrida do solver, +-60 cm, eixo humano):

- fiada (z) igual - senao ACTUAL_ERROR;
- apoio EFETIVO do solver por lado = min(apoio, assentamento na fiada de baixo);
- juntas (pecas ao longo da PROPRIA parede, como a regua) da fiada da canaleta
  contra as fiadas vizinhas: coincidencias
  (<= 1,5 cm, prisma) e desencontros abaixo do alvo (1,5-10 cm), solver x humano,
  juntas a <= 2 cm de QUALQUER jamba da parede isentas (como a regua de benchmark);
- paridade em cada no' da parede dentro da janela: quem passa ao longo sobre o
  no' na fiada da canaleta (esta parede ou a outra), solver x humano;
- amarracao: problema da auditoria de amarracao do solver dentro da janela.

EXACT_MATCH: pontas da corrida a <= 1,6 cm, mesma paridade, sem piora de junta.
PHYSICALLY_EQUIVALENT: apoio de cada lado >= min(humano, 19) - 0,5, mesma
  paridade, prisma e desencontro nao piores, sem problema de amarracao local.
SOLVER_BETTER: EQUIVALENT + ganho objetivo (menor apoio +5 cm ou menos
  coincidencias), nenhum criterio pior.
VALID_ALTERNATIVE: apoio efetivo >= 9 cm dos dois lados, prisma nao pior, sem
  problema de amarracao local, mas difere do humano (apoio menor que o humano,
  paridade ou desencontro) - motivo explicito.
SOLVER_WORSE: apoio efetivo < 9 cm (abaixo do humano), mais coincidencias, ou
  problema de amarracao local. KNOWN_LIMITATION: apoio efetivo < 9 cm IGUAL ao
  do humano naquele lado, sem outra piora.
Passagem livre (humano sem pecas sobre o vao): EXACT_MATCH so' se as bordas
abertas do solver ficam a <= 1,6 cm das humanas em todas as fiadas comuns;
mais aberto que o humano = SOLVER_WORSE; menos aberto (alvenaria ate' a jamba,
regra pedida pelo usuario) = NORMATIVE_DECISION.
EXACT_MATCH de canaleta exige tambem apoio efetivo >= humano - 1,6 cm.
Canaleta ausente: ACTUAL_ERROR, exceto KNOWN_LIMITATION quando o proprio solver
registra trecho NAO MODULAR sobre o vao naquela fiada (limitacao declarada).
"""
import re
from collections import Counter

MIN_SUPPORT = 19.0
CONVERT_BELOW = 9.0
TOL = 1.6
JOINT_TOL = 1.5
STAGGER_TARGET = 10.0
WINDOW = 60.0
JAMB_EXEMPT = 2.0


CLOSING_CODES = ("B19", "C04", "C09", "K19", "KV", "CHANNEL_U_19", "CHANNEL_U_CUT")


def _joints(pieces, limits=()):
    """pieces: [(lo, hi, code)] da PROPRIA parede, ordenadas; junta = meio da
    folga entre vizinhas (folga de -2,5 a 5 cm: a bbox humana tem 1 cm de aba).
    Mesma isencao da regua (analysis.joint_is_opening_aligned_exempt): junta de
    peca de fechamento encostada em jamba ou ponta do eixo nao conta."""
    out = []
    for a, b in zip(pieces, pieces[1:]):
        gap = b[0] - a[1]
        if not -2.5 <= gap <= 5.0:
            continue
        exempt = False
        for piece in (a, b):
            if str(piece[2]).startswith(CLOSING_CODES) and any(
                    abs(piece[0] - e) <= 2.0 or abs(piece[1] - e) <= 2.0 for e in limits):
                exempt = True
        if not exempt:
            out.append((a[1] + b[0]) / 2.0)
    return out


def _joint_quality(by_course, course, window, jambs):
    def local(ci):
        return [j for j in _joints(sorted(by_course.get(ci) or []), jambs) if window[0] <= j <= window[1]]
    here = local(course)
    coinc = stagger = 0
    for other in (course - 1, course + 1):
        near = local(other)
        for j in here:
            if not near:
                continue
            d = min(abs(j - k) for k in near)
            if d <= JOINT_TOL:
                coinc += 1
            elif d < STAGGER_TARGET:
                stagger += 1
    return coinc, stagger


def _owner(pieces_along, t, lip):
    return any(lo - lip <= t - 3.0 and hi + lip >= t + 3.0 for lo, hi in pieces_along)


class StrictComparator(object):
    def __init__(self, m, orf, walls, nodes, res, wall_ids, walls_json, human_records, human_sequences):
        self.m, self.orf, self.walls, self.nodes, self.res = m, orf, walls, nodes, res
        self.wall_ids = wall_ids
        self.walls_json = walls_json
        self.human = dict((r["id"], r) for r in human_records)
        self.seq = human_sequences["per_wall"]
        self.rein = res["opening_reinforcement"]

    # ---- eixos
    def to_human_t(self, wi, t_cm):
        m = self.m
        p0, _p1, d, _l, _t = m._wall_axis_and_length(self.walls, wi)
        x = p0.X * 30.48 + d.X * t_cm
        y = p0.Y * 30.48 + d.Y * t_cm
        w = self.walls_json[self.wall_ids[wi]]
        hx0, hy0 = w["p0_cm"]
        hx1, hy1 = w["p1_cm"]
        L = ((hx1 - hx0) ** 2 + (hy1 - hy0) ** 2) ** 0.5
        return (x - hx0) * (hx1 - hx0) / L + (y - hy0) * (hy1 - hy0) / L

    def flipped(self, wi):
        return self.to_human_t(wi, 0.0) > self.to_human_t(wi, 100.0)

    # ---- pecas por fiada no eixo humano
    def solver_course(self, wi, ci, along_only=False, codes=False):
        rows = self.orf._wall_strip_pieces(self.res["course_candidates"].get(ci) or [], self.walls, wi)
        out = []
        for r in rows:
            if along_only and not (r["along"] and r["cand"].get("wall_idx") == wi):
                continue
            a, b = sorted((self.to_human_t(wi, r["lo"]), self.to_human_t(wi, r["hi"])))
            out.append((a, b, r["cand"].get("logical_code")) if codes else (a, b))
        return sorted(out)

    def human_course(self, wid, ci, along_only=False, codes=False):
        items = self.seq.get(str(wid), {}).get(str(ci)) or []
        return sorted(((p[0], p[1], p[2]) if codes else (p[0], p[1])) for p in items if (p[3] or not along_only))

    def node_ts(self, wi):
        return [self.to_human_t(wi, self.m._ft_to_cm(t)) for _n, t in
                self.m._wall_junction_nodes_and_ts_ft(self.walls, self.nodes, wi)]

    def bond_positions(self, wi):
        audit = (self.res.get("wall_bond_audits") or {}).get(wi) or {}
        out = []
        for p in audit.get("problems") or []:
            match = re.search(r"X~(-?[0-9.]+)cm", str(p))
            if match:
                out.append((str(p).split(":")[0], self.to_human_t(wi, float(match.group(1)))))
        return out

    def non_modular_over(self, wi, ci, lo, hi):
        for span in self.res.get("non_modular") or []:
            if span.get("wall_idx") != wi:
                continue
            courses = span.get("course_indices")
            letter = span.get("course")
            if courses is not None and ci not in courses:
                continue
            if courses is None and letter is not None and letter != ("A" if ci % 2 == 0 else "B"):
                continue
            s_lo = span.get("start_cm", span.get("seg_start_cm"))
            s_hi = span.get("end_cm", span.get("seg_end_cm"))
            if s_lo is None or s_hi is None:
                return True
            a, b = sorted((self.to_human_t(wi, s_lo), self.to_human_t(wi, s_hi)))
            if min(b, hi) - max(a, lo) > 0.5:
                return True
        return False

    # ---- classificacao
    def compare(self, opening_ids):
        rows = []
        runs_by_id = dict((r["run_id"], r) for r in self.rein["runs"])
        self.jambs = {}
        for rec in self.rein["openings"]:
            for t in (rec["t_lo_cm"], rec["t_hi_cm"]):
                self.jambs.setdefault(rec["wall_idx"], []).append(self.to_human_t(rec["wall_idx"], t))
        for rec in self.rein["openings"]:
            wi, oi = rec["wall_idx"], rec["opening_index"]
            oid = opening_ids[wi][oi]
            wid = self.wall_ids[wi]
            h = self.human.get(oid)
            span = sorted((self.to_human_t(wi, rec["t_lo_cm"]), self.to_human_t(wi, rec["t_hi_cm"])))
            for role in ("above", "below"):
                s = rec.get(role)
                hh = (h or {}).get(role)
                if s is None and hh is None:
                    continue
                row = {"opening_id": oid, "wall": wid, "role": role, "solver_status": (s or {}).get("status")}
                h_has = bool(hh and "run" in hh and hh.get("all_over_channel"))
                row["human_status"] = "CHANNEL" if h_has else ("NO_CHANNEL" if hh is not None else "NONE")
                st = row["solver_status"]
                cls, reasons = None, []
                if h_has and st == "CHANNEL":
                    cls, reasons = self._channel_vs_channel(wi, wid, rec, s, hh, span, runs_by_id, row)
                elif hh is not None and not h_has and st == "FREE_TO_TOP":
                    cls, reasons = self._free_to_top(wi, wid, s, hh, span, row)
                elif h_has and st == "FREE_TO_TOP":
                    cls, reasons = "ACTUAL_ERROR", ["human_channel_solver_open"]
                elif not h_has and st in ("HEAD_OFF_GRID", "SILL_OFF_GRID"):
                    cls, reasons = "NOT_COMPARABLE", ["off_grid_needs_rule_51_8"]
                elif h_has and st in ("HEAD_OFF_GRID", "SILL_OFF_GRID"):
                    cls, reasons = "ACTUAL_ERROR", ["off_grid_but_human_channel"]
                elif h_has and st in ("MISSING", None):
                    ci = (s or {}).get("course_index")
                    covered = sum(max(0.0, min(b, span[1]) - max(a, span[0]))
                                  for a, b in (self.solver_course(wi, ci) if ci is not None else []))
                    if (ci is not None and covered < (span[1] - span[0]) - 1.0
                            and self.non_modular_over(wi, ci, span[0], span[1])):
                        cls, reasons = "KNOWN_LIMITATION", ["solver_non_modular_span_over_opening"]
                    else:
                        cls, reasons = "ACTUAL_ERROR", ["missing_channel"]
                elif not h_has and st == "CHANNEL":
                    cls, reasons = "NORMATIVE_DECISION", ["solver_channel_human_none"]
                else:
                    cls, reasons = "NOT_COMPARABLE", ["unmatched_states"]
                row["classification"], row["reasons"] = cls, reasons
                rows.append(row)
        return {"summary": dict(Counter(r["classification"] for r in rows)),
                "by_role": dict(("%s:%s" % k, v) for k, v in Counter((r["role"], r["classification"]) for r in rows).items()),
                "rows": rows}

    def _channel_vs_channel(self, wi, wid, rec, s, hh, span, runs_by_id, row):
        ci = s["course_index"]
        run = runs_by_id[s["run_id"]]
        s_run = sorted((self.to_human_t(wi, run["lo_cm"]), self.to_human_t(wi, run["hi_cm"])))
        eff = [min(s["support_l_cm"], s["bearing_l_cm"]), min(s["support_r_cm"], s["bearing_r_cm"])]
        if self.flipped(wi):
            eff = eff[::-1]
        h_sup = [hh["support_l"], hh["support_r"]]
        h_run = hh["run"]
        row.update(solver_course=ci, human_z=hh["z_lo"], solver_support_effective=[round(v, 3) for v in eff],
                   human_support=h_sup, solver_run=[round(v, 2) for v in s_run], human_run=h_run)
        if abs(hh["z_lo"] - (1 + 20 * ci)) > 1.5:
            return "ACTUAL_ERROR", ["different_course"]
        window = (min(s_run[0], h_run[0]) - WINDOW, max(s_run[1], h_run[1]) + WINDOW)
        by_solver = dict((c, self.solver_course(wi, c, along_only=True, codes=True)) for c in (ci - 1, ci, ci + 1))
        by_human = dict((c, self.human_course(wid, c, along_only=True, codes=True)) for c in (ci - 1, ci, ci + 1))
        wall_len = self.walls_json[wid]
        axis_len = ((wall_len["p1_cm"][0] - wall_len["p0_cm"][0]) ** 2 + (wall_len["p1_cm"][1] - wall_len["p0_cm"][1]) ** 2) ** 0.5
        jambs = (self.jambs.get(wi) or list(span)) + [0.0, axis_len]
        s_coinc, s_stag = _joint_quality(by_solver, ci, window, jambs)
        h_coinc, h_stag = _joint_quality(by_human, ci, window, jambs)
        parity = []
        s_along = self.solver_course(wi, ci, along_only=True)
        h_along = self.human_course(wid, ci, along_only=True)
        for t in self.node_ts(wi):
            if window[0] <= t <= window[1]:
                parity.append((round(t, 1), _owner(s_along, t, 0.0), _owner(h_along, t, -1.0)))
        parity_diff = [p for p in parity if p[1] != p[2]]
        bond_local = [p for p in self.bond_positions(wi) if window[0] <= p[1] <= window[1]]
        row.update(joint_coincidences={"solver": s_coinc, "human": h_coinc},
                   stagger_below_target={"solver": s_stag, "human": h_stag},
                   node_parity=parity, local_bond_problems=[p[0] for p in bond_local])
        reasons = []
        low = [i for i in (0, 1) if eff[i] < CONVERT_BELOW - 1e-6]
        if low and all(h_sup[i] <= eff[i] + 0.5 for i in low) and s_coinc <= h_coinc and not bond_local:
            # mesmo apoio baixo do humano naquele lado: limitacao declarada,
            # nunca equivalencia (auditoria 2026-09-14)
            return "KNOWN_LIMITATION", ["effective_support_below_9cm_same_as_human"]
        if low:
            reasons.append("effective_support_below_9cm")
        if s_coinc > h_coinc:
            reasons.append("more_joint_coincidences")
        if bond_local:
            reasons.append("local_bond_problem")
        if reasons:
            return "SOLVER_WORSE", reasons
        support_worse = [i for i in (0, 1) if eff[i] < min(h_sup[i], MIN_SUPPORT) - 0.5]
        if parity_diff:
            reasons.append("node_parity_differs")
        if s_stag > h_stag:
            reasons.append("more_stagger_below_target")
        if support_worse:
            reasons.append("support_below_human")
        exact = (abs(h_run[0] - s_run[0]) <= TOL and abs(h_run[1] - s_run[1]) <= TOL
                 and all(eff[i] >= h_sup[i] - TOL for i in (0, 1)))
        if not reasons:
            if exact:
                return "EXACT_MATCH", []
            gain = []
            if min(eff) > min(h_sup) + 5.0:
                gain.append("min_support_gain")
            if s_coinc < h_coinc:
                gain.append("fewer_joint_coincidences")
            return ("SOLVER_BETTER", gain) if gain else ("PHYSICALLY_EQUIVALENT", [])
        return "VALID_ALTERNATIVE", reasons

    def _free_to_top(self, wi, wid, s, hh, span, row):
        from_ci = s.get("course_index")
        diffs = []
        worse = []
        inside = []
        human_courses = sorted(int(c) for c in self.seq.get(str(wid), {}))
        for ci in [c for c in human_courses if c >= from_ci]:
            sol = self.solver_course(wi, ci)
            hum = [(a + 1.0, b - 1.0) for a, b in self.human_course(wid, ci)]  # sem a aba de 1 cm
            for pieces, label in ((sol, "solver"), (hum, "human")):
                if [p for p in pieces if p[1] > span[0] + 0.5 and p[0] < span[1] - 0.5]:
                    inside.append((ci, label))
            for side, t in ((-1, span[0]), (1, span[1])):
                def gap(pieces):
                    if side < 0:
                        edges = [b for a, b in pieces if t - 80 <= b <= t + 0.5]
                        return max(0.0, t - max(edges)) if edges else 80.0
                    edges = [a for a, b in pieces if t - 0.5 <= a <= t + 80]
                    return max(0.0, min(edges) - t) if edges else 80.0
                g_s, g_h = gap(sol), gap(hum)
                diffs.append((ci, side, round(g_s, 2), round(g_h, 2)))
                if g_s > g_h + TOL:
                    worse.append((ci, side, round(g_s, 2), round(g_h, 2)))
        row.update(free_to_top_gaps=diffs, pieces_inside=inside)
        if [x for x in inside if x[1] == "solver"]:
            return "SOLVER_WORSE", ["solver_piece_inside_open_span"]
        if worse:
            return "SOLVER_WORSE", ["solver_opens_wider_than_human"]
        if all(abs(g_s - g_h) <= TOL for _c, _sd, g_s, g_h in diffs):
            return "EXACT_MATCH", []
        # O humano abre alem das jambas (ate' as faces dos nos); a regra pedida
        # pelo usuario (auditoria 2026-09-14) abre SO' o vao. Diferenca real,
        # nunca equivalencia: decisao normativa registrada.
        return "NORMATIVE_DECISION", ["user_rule_opens_only_the_opening_human_opens_to_node_faces"]
