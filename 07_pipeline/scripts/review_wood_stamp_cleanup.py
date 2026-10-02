"""后台读取清理前后工程：导出保护摘要和固定背面机位渲染，不保存场景改动。"""
from pathlib import Path
import json
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cleanup_wood_rear_stamp import OUT, protected_state
from wood_layers_blender import aim


def main():
    """输入CLI末尾的before/after标签，输出保护摘要和同光背面PNG。"""
    label = sys.argv[sys.argv.index('--') + 1]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (label + '_state.json')).write_text(
        json.dumps(protected_state(), ensure_ascii=False, indent=2), encoding='utf-8')
    if label == 'verify':
        # 重新打开保存文件后检查残留，避免仅验证实时内存状态。
        trees = list(bpy.data.node_groups) + [m.node_tree for m in bpy.data.materials if m.use_nodes]
        residual = {'attributes': [m.name for m in bpy.data.meshes if m.attributes.get('reference_rear')],
            'nodes': [[g.name, n.name] for g in trees for n in g.nodes
                if n.get('wood_layers_role') in {'rear_stamp', 'rear_stamp_preserved', 'stamp_note', 'rear_only'}],
            'images': [im.name for im in bpy.data.images if 'StampMask' in im.name],
            'inputs': [g.name for g in bpy.data.node_groups if 'Scanned finish' in g.name
                and any(s.name == 'Rear' for s in g.interface.items_tree)]}
        assert not any(residual.values()), residual
        (OUT / 'reopen_validation.json').write_text(json.dumps(residual, indent=2), encoding='utf-8')
        print('STAMP_REOPEN_VALID', flush=True)
        return
    sc = bpy.context.scene
    sc.camera.location = (0, .95, .73)
    sc.camera.data.lens = 65
    aim(sc.camera, (0, .168, .673))
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 900
    sc.render.resolution_percentage = 100
    sc.cycles.samples = 48
    sc.cycles.seed = 930
    sc.cycles.use_animated_seed = False
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    sc.cycles.device = 'GPU'
    sc.render.filepath = str(OUT / (label + '.png'))
    bpy.ops.render.render(write_still=True)
    print('STAMP_REVIEW_COMPLETE ' + label, flush=True)


if __name__ == '__main__':
    main()
