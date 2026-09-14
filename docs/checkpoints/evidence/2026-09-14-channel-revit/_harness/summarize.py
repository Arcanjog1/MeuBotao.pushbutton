import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
st = dict((s['label'], s) for s in d['steps'])
s = d.get('solve', {})
print('walls', d.get('walls'), 'ops', d.get('openings_assigned'), 'pieces', s.get('pieces'), 'pf', s.get('preflight_ok'),
      s.get('opening_violations'), s.get('collisions'), 'bond', s.get('bond_reproved'), 'nmod', s.get('non_modular'), 't_solve', s.get('t_s'))
print('  val', dict((k, v) for k, v in (s.get('channel_validation') or {}).items() if v))
from collections import Counter
print('  find', dict(Counter(f['code'] for f in s.get('channel_findings') or [])))
print('  cross', len(s.get('node_crossings') or []), 'conv', len(s.get('tie_conversions') or []), 'ftt', len(s.get('free_to_top') or []))
print('  create', dict((k, v) for k, v in (st.get('CREATED') or {}).items() if k != 'label'))
rb = d.get('readback') or {}
print('  readback checked', rb.get('checked'), 'mismatch', rb.get('mismatch_count'), rb.get('mismatches', [])[:3])
print('  perf', (d.get('create') or {}).get('perf'))
print('  human', d.get('human_modified_before'), d.get('human_modified_after'), 'steps', [x['label'] for x in d['steps']])
