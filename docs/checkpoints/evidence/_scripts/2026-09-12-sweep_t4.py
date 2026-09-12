import sys, time, itertools
sys.path.insert(0, "tests")
import test_block_node_fill_revalidation as T
seg = T.seg
t0=time.time(); hits=[]
def check(name, lines):
    with T.node_fill(False):
        r, w = T.solve_plan(lines); a = T.node_fill_prism_violations(w, r["candidates"])
    if not a: return
    with T.node_fill(True):
        r, w = T.solve_plan(lines); b = T.node_fill_prism_violations(w, r["candidates"])
    hits.append((name, a, b)); print("HIT", name, "antes", a, "depois", b, flush=True)
# T no meio com posicoes variadas
for L in range(300, 801, 50):
    for t1 in range(100, L-99, 50):
        check(("T", L, t1), [seg(0,0,L,0), seg(t1,0,t1,300)])
        for t2 in range(t1+100, L-99, 50):
            check(("TT", L, t1, t2), [seg(0,0,L,0), seg(t1,0,t1,300), seg(t2,0,t2,300)])
# L livre com comprimentos variados
for a in range(100, 501, 25):
    for b in range(100, 501, 50):
        check(("L", a, b), [seg(0,0,a,0), seg(0,0,0,b)])
# parede curta entre L e T (a geometria de W088)
for short in range(40, 160, 5):
    check(("LT", short), [seg(0,0,300,0), seg(0,0,0,short), seg(-300,short,300,short)])
    check(("LT2", short), [seg(0,0,-300,0), seg(0,0,0,short), seg(-300,short,300,short)])
print("done", len(hits), "hits", round(time.time()-t0,1), "s")
