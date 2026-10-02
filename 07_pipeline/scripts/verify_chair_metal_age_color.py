"""重开已保存工程，复核既有54项保护检查和本次实际老化控制接线。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_chair_metal
from revise_chair_metal_age_color import GROUP, OUT, PARTS


def main():
    """输入磁盘重开的工程，输出保护检查与11件漆面调色接口的实测记录。"""
    verify_chair_metal.main()
    g = bpy.data.node_groups[GROUP]
    colour = next(n for n in g.nodes if n.get('chair_metal_role') == 'paint_oxidation_colour')
    total = next(n for n in g.nodes if n.get('chair_metal_role') == 'whole_surface_age_factor')
    checks = {'color_connected': colour.inputs[2].is_linked,
              'coverage_connected': colour.inputs[0].links[0].from_node == total,
              'factor_clamped': total.use_clamp,
              'age_drives_global_coverage': any(l.from_socket.name == 'Age' for n in g.nodes
                  if n.get('chair_metal_role') == 'whole_surface_age_coverage' for l in n.inputs[0].links)}
    values = {}
    for name in PARTS:
        app = next(n for n in bpy.data.objects[name].active_material.node_tree.nodes
                   if n.get('chair_metal_role') == 'appearance')
        values[name] = {k: app.inputs[k].default_value for k in ['Age', 'Age Coverage', 'Age Variation']}
        checks[name] = all(abs(values[name][k]-v) < 1e-6 for k, v in
                           [('Age', .95), ('Age Coverage', .78), ('Age Variation', .30)])
    audit = {'file': bpy.data.filepath, 'passed': all(checks.values()), 'checks': checks, 'controls': values}
    (OUT/'reopen_validation.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    assert audit['passed'], checks
    print('AGE_COLOR_REOPEN ' + json.dumps({'passed': True, 'paint_parts': len(values)}), flush=True)


if __name__ == '__main__':
    main()
