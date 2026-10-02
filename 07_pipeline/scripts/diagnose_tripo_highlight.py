"""保持颜色、相机、曝光和灯光不变，分别验证粗糙度与微法线的高光贡献。"""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tripo_wood_reference_blender import WORK, OUT, render


def main():
    """读回候选，仅输出三张通道隔离诊断；不保存工程改动。"""
    bpy.ops.wm.open_mainfile(filepath=str(WORK/'tripo_wood_reference.blend'))
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    bpy.context.scene.cycles.device='GPU' if any(d.use for d in prefs.devices) else 'CPU'
    records=[]
    for name in ('LP_part_02','LP_part_09'):
        t=bpy.data.objects[name].data.materials[0].node_tree; p=t.nodes.get('Principled BSDF')
        for key in ('Normal','Coat Normal','Roughness','Coat Roughness'):
            target=p.inputs[key]; source=target.links[0].from_socket
            records.append((t,target,source,key)); t.links.remove(target.links[0])
            if 'Roughness' in key: target.default_value=.39
    render('10_flat_diagnostic',(.29,-.47,.85),(0,-.035,.405),55)
    for t,target,source,key in records:
        if 'Roughness' in key: t.links.new(source,target)
    render('11_roughness_diagnostic',(.29,-.47,.85),(0,-.035,.405),55)
    for t,target,source,key in records:
        if 'Normal' in key: t.links.new(source,target)
    render('12_final_diagnostic',(.29,-.47,.85),(0,-.035,.405),55)


if __name__=='__main__': main()
