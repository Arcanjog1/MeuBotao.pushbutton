import cProfile, io, json, os, pstats, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,ROOT)
from nuvem.benchmark import runner, solver_bridge
solver_bridge.engine()
inp=json.load(open(runner.project_paths(sys.argv[1])["input"],encoding="utf-8"))
pr=cProfile.Profile(); pr.enable()
solver_bridge.run_solver(inp)
pr.disable()
s=io.StringIO(); ps=pstats.Stats(pr,stream=s).sort_stats("cumulative")
ps.print_stats(45)
print(s.getvalue())
