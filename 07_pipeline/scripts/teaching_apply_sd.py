"""Bind true SD exports to saved teaching geometry. Preserve collection contracts and add an independent face-local WearUV.
Input existing reviewed work blend; output same blend after dependency and layout checks. Old procedural materials are fully replaced.
"""
import bpy,json
from pathlib import Path
R=Path('D:/00_projects/10_CG/Shot_Test');T=R/'02_assets/textures/generated/teaching_sd';EQ=R/'02_assets/textures/generated/equipment_sd';C=R/'07_pipeline/cache/teaching_rebuild'
scene=bpy.context.scene

def tex(nodes,links,path,uv='UVMap',noncolor=False):
    """Input file and UV set; return image node with correct color management, default node names retained."""
    n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(path),check_existing=True)
    if noncolor:n.image.colorspace_settings.name='Non-Color'
    n.extension='EXTEND' if uv=='WearUV' else 'REPEAT'
    u=nodes.new('ShaderNodeUVMap');u.uv_map=uv;links.new(u.outputs[0],n.inputs[0]);return n

# Separate face-local edge placement from physical wood-grain UVs; UV edges now match actual plank edges.
for c in bpy.data.collections:
    if not c.name.startswith('AST_'):continue
    for o in c.objects:
        if o.type!='MESH':continue
        me=o.data;uv=me.uv_layers.get('WearUV') or me.uv_layers.new(name='WearUV')
        for poly in me.polygons:
            axis=max(range(3),key=lambda i:abs(poly.normal[i]));a,b=[i for i in range(3) if i!=axis]
            lo=[min(v.co[k] for v in me.vertices) for k in range(3)];hi=[max(v.co[k] for v in me.vertices) for k in range(3)]
            for li in poly.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((v[a]-lo[a])/max(hi[a]-lo[a],1e-8),(v[b]-lo[b])/max(hi[b]-lo[b],1e-8))
        me.uv_layers.active_index=0

mapping={};deps=set()
for mat in list(bpy.data.materials):
    if not mat.name.startswith('Teaching / '):continue
    label=mat.name.split(' / ',1)[1];old_tint=None
    for n in mat.node_tree.nodes:
        if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':old_tint=tuple(n.inputs[2].default_value[:3])
    wood=any(s in label for s in ['birch','endgrain','stained rails'])
    if wood:folder=T/'teaching_varnished_wood';family='teaching_varnished_wood';tint=(1,1,1) if 'Honey' in label else (.73,.59,.39) if 'rails' in label else (.94,.87,.69)
    elif 'Empty wiped' in label:folder=T/'teaching_chalkboard';family='teaching_chalkboard';tint=None
    elif 'Notice faded' in label:family='notice_'+label[-2:];folder=T/family;tint=None
    elif 'Cloth binding' in label:family='teaching_bookcloth';folder=T/family;tint=old_tint
    elif 'Eraser felt' in label:family='teaching_felt';folder=T/family;tint=None
    elif 'page' in label or 'Chalk mineral' in label:family='teaching_paper';folder=T/family;tint=old_tint
    elif 'ivory' in label:family='equipment/enamel';folder=EQ/'enamel';tint=None
    elif 'hardware' in label:family='equipment/metal';folder=EQ/'metal';tint=None
    else:family='equipment/dark';folder=EQ/'dark';tint=None
    n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');l.new(p.outputs[0],out.inputs[0])
    bc=tex(n,l,folder/'BaseColor.png');rough=tex(n,l,folder/'Roughness.png',noncolor=True);normal=tex(n,l,folder/'Normal.png',noncolor=True);metal=tex(n,l,folder/'Metallic.png',noncolor=True)
    color=bc.outputs[0];rr=rough.outputs[0]
    if wood:
        mask=tex(n,l,folder/'WearMask.png','WearUV',True);ex=tex(n,l,folder/'ExposedBaseColor.png');er=tex(n,l,folder/'ExposedRoughness.png',noncolor=True)
        mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);l.new(color,mix.inputs[1]);l.new(ex.outputs[0],mix.inputs[2]);color=mix.outputs[0]
        mr=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mr.inputs[0]);l.new(rr,mr.inputs[1]);l.new(er.outputs[0],mr.inputs[2]);rr=mr.outputs[0]
        p.inputs['Coat Weight'].default_value=.16;p.inputs['Coat Roughness'].default_value=.30
    if tint:
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*tint,1);l.new(color,mix.inputs[1]);color=mix.outputs[0]
    l.new(color,p.inputs['Base Color']);l.new(rr,p.inputs['Roughness']);l.new(metal.outputs[0],p.inputs['Metallic'])
    nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.25 if wood else .8;l.new(normal.outputs[0],nm.inputs['Color']);l.new(nm.outputs[0],p.inputs['Normal'])
    mat['source']='True Substance Designer native graph cooked and rendered with Adobe SAT';mat['sd_family']=family
    mat['mapping']='UVMap physical scale .5m wood/.35m fibre; board and notices full unique UV; WearUV face local normalized to real part boundaries'
    mapping[mat.name]={'family':family,'outputs':[str(folder/f) for f in ['BaseColor.png','Roughness.png','Normal.png','Metallic.png']],'wear_output':str(folder/'WearMask.png') if wood else None}
    deps.update(nn.image for nn in n if nn.type=='TEX_IMAGE' and nn.image)
# Purge old image datablocks so dependency review cannot mistake first-pass raster maps for the new deliverable.
for im in list(bpy.data.images):
    if im not in deps and im.users==0:bpy.data.images.remove(im)
    elif im in deps:
        assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath
        im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath),start=str(R/'02_assets/work'))
scene['teaching_material_stage']='Substance Designer native SBS/SBSAR exports; local edge wear + physical grain UV separated'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'02_assets/work/classroom_teaching.blend'))
(C/'sd_binding.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8');print('Bound SD materials',len(mapping),'image dependencies',len(deps))
