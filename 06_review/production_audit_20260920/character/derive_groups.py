"""从只读 JSON 和旧构建器的身体段规则恢复分组建议；不调用 Blender。"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
audit = json.loads((OUT / 'character_audit.json').read_text(encoding='utf-8'))
figures = {o['name']: o for o in audit['figures']}
cx, cy = -1.95, -3.65 + 1.0875
segments = [
    ('torso', 0, 54, (cx,cy,.60), (cx-.05,cy+.06,1.20), .165),
    ('head', 55, 76, (cx-.06,cy+.06,1.32), (cx-.035,cy+.075,1.51), .133),
    ('neck', 77, 80, (cx-.04,cy+.065,1.18), (cx-.04,cy+.07,1.34), .066),
]
for side, dx, upper, lower in [('minus_x',-.19,(81,90),(91,98)), ('plus_x',.19,(99,111),(112,116))]:
    segments.extend([
        ('upper_arm_'+side,*upper,(cx+dx,cy+.02,1.15),(cx+dx*1.3,cy+.27,.86),.065),
        ('forearm_'+side,*lower,(cx+dx*1.3,cy+.27,.86),(cx+dx*1.15+.18,cy+.50,.84),.061),
    ])
for side, dx, thigh, shin, foot in [('minus_x',-.13,(117,125),(126,136),(137,139)),
                                   ('plus_x',.15,(140,152),(153,163),(164,166))]:
    segments.extend([
        ('thigh_'+side,*thigh,(cx+dx,cy,.53),(cx+dx+.22,cy+.24,.48),.066),
        ('shin_'+side,*shin,(cx+dx+.22,cy+.24,.48),(cx+dx+.22,cy+.27,.12),.061),
        ('foot_'+side,*foot,(cx+dx+.23,cy+.28,.07),(cx+dx+.38,cy+.32,.07),.036),
    ])


def fits_scatter(point, start, end, radius):
    """输入中心点、旧生成段和半径；判断是否存在 t 使该点落在原散布盒内。"""
    lo, hi = 0., 1.
    for k, extent in enumerate([radius, radius*.85, radius*.4]):
        delta = end[k] - start[k]
        if abs(delta) < 1e-9:
            if abs(point[k]-start[k]) > extent + 2e-6:
                return False
        else:
            ts = sorted([(point[k]-start[k]-extent)/delta, (point[k]-start[k]+extent)/delta])
            lo, hi = max(lo,ts[0]), min(hi,ts[1])
    return lo <= hi + 2e-6


groups = []
for label, first, last, start, end, radius in segments:
    names = [f'tin_{i:03d}' for i in range(first,last+1)]
    groups.append({'body_part':label,'instances':names,'count':len(names),
                   'rest_start':start,'rest_end':end,'scatter_radius':radius,
                   'fits_source_scatter':all(fits_scatter(figures[n]['world_location'],start,end,radius) for n in names),
                   'raw_bounds':[[min(figures[n]['bounds_raw'][0][i] for n in names) for i in range(3)],
                                 [max(figures[n]['bounds_raw'][1][i] for n in names) for i in range(3)]]})
assert sum(g['count'] for g in groups)==167
assert all(g['fits_source_scatter'] for g in groups)
result = {'method':'Recovered contiguous IDs from source creation order, verified every centre fits its source scatter segment after known +1.0875m Y translation; not authored rig metadata.',
          'rest_pelvis':[cx,cy,.53], 'groups':groups,
          'limitations':['No L/R anatomical metadata; plus_x/minus_x labels avoid inventing side identity.',
                         '13 groups preserve each can rigidly, but each joint needs silhouette and overlap QA.',
                         'Original cluster calls can return fewer tins than requested; counts were recovered from actual positions, not requested counts.']}
(OUT / 'body_groups.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('BODY_GROUPS_VERIFIED',[(g['body_part'],g['count']) for g in groups])
