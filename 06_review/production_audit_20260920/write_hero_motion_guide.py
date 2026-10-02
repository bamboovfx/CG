"""Publish a conservative image-space guide: separate camera reveal from unproven actor locomotion."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
out=Path(r'D:/00_projects/10_CG/Shot_Test/06_review/production_audit_20260920');folder=out/'hero_motion_frames'
fs=list(range(3823,3963,12))+[3962]
raw=json.loads((out/'hero_tracks_raw.json').read_text())
# Clock center is stable and textured; track each requested sample near its measured horizontal trend.
ref=np.asarray(Image.open(folder/'source_003823.png').convert('L'));x,y=652,282;h=17;t=ref[y-h:y+h+1,x-h:x+h+1].astype(float);t-=t.mean();tn=np.sqrt((t*t).sum())
samples=[]
for f in fs:
    arr=np.asarray(Image.open(folder/f'source_{f:06d}.png').convert('L'));guess=round((f-3823)*159/139);best=(-2,None)
    for dy in range(-3,4):
        for dx in range(max(0,guess-8),guess+9):
            p=arr[y+dy-h:y+dy+h+1,x+dx-h:x+dx+h+1].astype(float);p-=p.mean();ncc=float((p*t).sum()/(tn*np.sqrt((p*p).sum())+1e-8))
            if ncc>best[0]:best=(ncc,[x+dx,y+dy])
    state='not_identifiable' if f<3847 else ('tiny_occluded_left_edge_fragment' if f==3847 else ('partly_cropped_at_left_edge' if f<3907 else 'body_revealed_with_chair_occlusion'))
    samples.append({'source_frame':f,'production_frame':1001+f-3823,'source_seconds':f/24,'clock_center_xy':best[1],'ncc':round(best[0],5),'actor_visibility':state,'image':f'hero_motion_frames/source_{f:06d}.png'})
tracknames=['clock_center','blackboard_top_right','small_sign_above_board']
tracks={name:{'method':'manually selected seed + integer-pixel normalized cross-correlation; visual check','absolute_seed_error_px':3,'relative_displacement_error_px':2,'samples':raw[name]} for name in tracknames}
tracks['tv_lower_left']={'method':'secondary lower-confidence patch; visual cross-check only','absolute_seed_error_px':5,'relative_displacement_error_px':6,'samples':raw['tv_lower_left']}
chair={'method':'manual corresponding chair-back upper-right corner; previous low-NCC automatic result rejected','source_frames':[3893,3962],'xy':[[70,653],[378,653]],'error_px':10,'delta_xy':[308,0]}
(out/'hero_chair_anchor.json').write_text(json.dumps(chair,ensure_ascii=False,indent=2),encoding='utf-8')
actor={'first_confidently_identifiable_source_frame':3847,'first_confident_production_frame':1025,'first_dark_fragment_uncertainty_source_frames':[3844,3847],'note':'This is first recognisable tin fragment between left-side desks, not the start of a walk. Few shadowed pixels may precede it.','end_frame':3962,'coordinate_method':'manual full-resolution reading, not segmentation or object tracking','end_visible_bbox_xyxy':[145,449,642,928],'end_visible_bbox_center_xy':[394,689],'bbox_error_px':20,'end_head_top_xy':[375,450],'head_top_error_px':15,'end_foot_contact_region_xyxy':[320,895,495,930],'end_foot_contact_representative_xy':[408,918],'foot_error_px':25,'foot_note':'Chair legs and dark cans overlap; individual feet and exact sole contacts cannot be reliably separated. Do not use this to invent footsteps.','body_motion_relative_to_chair':{'frame_pair':[3893,3962],'head_top_manual_xy':[[70,438],[375,450]],'head_delta_xy':[305,12],'chair_delta_xy':[308,0],'head_relative_delta_xy':[-3,12],'combined_error_px':25,'conclusion':'No measurable root travel relative to the same chair at this precision; local head/arm motion is visible.'},'occlusion':['The body is revealed from the left border; first fragments are in shadow between foreground desks.','The light wooden chair back and tubular frame cross in front of lower torso/legs throughout.','By the last frame the arm on screen-right rises/extends toward a nearby desktop; avoid freezing every can.','No verified alternating foot plant or movement across multiple chairs in this shot.']}
record={'reference':'REF027','source_range_inclusive':[3823,3962],'duration_frames':140,'fps':24,'production_range_inclusive':[1001,1140],'coordinates':{'image_size':[1920,1080],'origin':'top-left','x_positive':'right','y_positive':'down','encoded_black_bars_approx':{'active_top':132,'active_bottom_exclusive':948,'active_height':816},'active_crop_mapping':'x unchanged, y_active=y_full-132; normalized active=(x/1920,(y-132)/816). Crop limits are approximate visual boundaries, not a reformat mandate.'},'samples':samples,'background_tracks':tracks,'chair_anchor':chair,'actor':actor,'observed_camera_image_change':{'front_wall_dx_start_to_end_px':[158,159,159],'front_wall_dy_start_to_end_px':[0,0,0],'mean_front_wall_dx_px':158.6667,'mean_mid_dx_px':80,'fraction_of_full_width':0.08264,'nearly_linear':True,'image_scale_or_roll':'Three tracked wall features retain relative spacing/vertical coordinates within roughly2px; no measured basis to add deliberate roll or zoom.'},'inference_not_solved_camera':['Near chair shifts about308px during second half while far wall shifts79px; depth-dependent parallax is consistent with lateral camera translation/reveal.','Camera movement toward its left is a useful initial blocking hypothesis; absolute world direction, metres, lens and camera trajectory have not been solved.','Root can initially remain fixed relative to the chair; add local upper-body/head/arm action only after static-root reveal matches reference.'],'correction_of_prior_audit':'Earlier descriptions of walking into frame and slight roll were interpretations from small contact sheets. They must not be used as animation instructions. High-resolution chair-relative evidence supports camera reveal as the main cause.','blocking_recommendation':['Fit first/middle/last camera framing so wall points move approximately0/80/159px right while y is stable.','Keep the actor at the same chair; place it initially off the left image boundary by camera framing, not by root walking.','Aim for first identifiable sliver around production1025 (±3frames), substantial partial body by1071, and end visible bbox center around(394,689) full source pixels.','Match the foreground chair occlusion; a hero silhouette floating in the aisle is inconsistent with evidence.','Keep feet/root stable until a later close-shot reference explicitly requires a pose change; allow observed local arm/head changes.','Use this image-space guide with actual project projection. Do not copy source black bars into render output.']}
(out/'hero_motion_guide.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
rows='\n'.join(f"| {s['source_frame']} | {s['production_frame']} | {s['clock_center_xy']} | {s['actor_visibility']} |" for s in samples)
md=f'''# 教室主全景140帧：相机揭示与人物动作参考

**保守结论：先做摄影机横移揭示同一张椅子旁的角色；没有证据支持让角色从画外走进教室。** 此项修正早期小图拉片中的“走入”和“轻微roll”推测。角色有可见上身/手臂变化，但根部移动和交替落脚尚未验证，不能据此编一个步行周期。

源帧 **3823–3962（含）** → 制作帧 **1001–1140（含）**，24fps。坐标均基于1920×1080含黑边原片，左上为(0,0)。有效画面大致y=132…947；转无黑边坐标时减132，再按实际输出缩放。

## 固定背景的首中末实测

种子点手选后用35×35灰度块归一化相关搜索，并看图复核；相对位移误差约±2px，种子中心定义误差约±3px。这是屏幕测量，**不是原片3D相机解算**。

| 固定点 | 3823 / 本地1001 | 3893 / 本地1071 | 3962 / 本地1140 | 首尾位移 |
|---|---|---|---|---|
| 时钟中心 | (652,282) | (732,282) | (811,282) | (+159,0) |
| 黑板右上角 | (1098,318) | (1178,318) | (1256,318) | (+158,0) |
| 黑板上方小牌中心 | (1063,298) | (1143,298) | (1222,298) | (+159,0) |

三点相关系数0.93–0.99。电视左下角次要参考为(408,428)→(491,427)→(576,427)，但相关度较低0.62–0.77，仅作±6px辅助判断。

前墙整体约向屏幕右平移159px，即画宽8.26%，中点约80px。三点相对间距和y几乎不变，没有量化依据额外加roll、zoom或明显竖向摇镜。近景椅子后半段右移约308px，而同期前墙只右移79px；这种不同深度的位移差支持横向摄影机运动。相机自身向左平移可作为blocking起点，实际米数/焦距并未求出。

## 人物相对于椅子

在3893与3962两张原尺寸画面中，同一浅木色椅背右上转角手工读数约 **(70,653)→(378,653)，+308±10px**。角色头顶约 **(70,438)→(375,450)，(+305,+12)±20px**。相对椅背只有约(-3,+12)px变化，处于局部摆动与测量误差范围，不能说明角色根部跨过椅子。

最后一帧参考：可见角色包围范围约 **x145–642、y449–928**；包围盒中心约 **(394,689)**（±20px，包含伸出的手臂）；头顶约 **(375,450)**（±15px）。脚底/接地只能估计在 **x320–495、y895–930**，可暂取(408,918)（±25px）。椅腿和暗色罐体重叠，不能可靠拆分左右脚或据此编步态。

首次能明确辨认的罐体碎片约在源 **3847 / 本地1025**，位于画左桌椅间暗部；更早少量暗像素可能在3844–3847，保留±3帧不确定性。它是相机揭示的首次可见，**不是开始走路的时刻**。主体持续被浅木椅背、钢管架及桌边遮挡；末段画面右侧手臂抬起/伸出，应该保留这种局部动作。

证据：`hero_actor_chair_relative.jpg`、`hero_actor_grid.jpg`、`hero_entrance_pixel_window.jpg`。椅子自动匹配相关度仅0.50，因此已拒绝其结果，采用有误差声明的手读坐标。

## 每12帧采样（另含首尾）

`hero_motion_contact.jpg` 和 `hero_motion_frames/source_*.png` 为原图/联系表。表内时钟用相关追踪；人物栏是可见性描述，不是步态分类。

| 源帧 | 制作帧 | 时钟中心(px) | 人物可见性 |
|---:|---:|---|---|
{rows}

## 当前blocking建议

1. 先固定角色根部与同一张椅子的关系，匹配相机首/中/末，使前墙点约右移0/80/159px且高度稳定。
2. 让角色由构图在本地1025附近被画左逐渐揭示；后半段近景视差明显，不要只给整幅图加二维平移。
3. 匹配椅背遮住下胸/躯干、钢管遮住腿部的关系。先出静根部版本，再添加已看到的局部头部/手臂变化。
4. 当前镜头不增加未经验证的步行、位移落座或大幅roll。165.125秒开始的另一近镜头另行处理。

这些是相机/动作的可验证保守起点；没有改动项目工程。
'''
(out/'hero_motion_guide.md').write_text(md,encoding='utf-8')
# A review overlay records the manual character extent; it is not a source texture or final artwork.
im=Image.open(folder/'source_003962.png').convert('RGB');d=ImageDraw.Draw(im);d.rectangle((145,449,642,928),outline='#ffcc33',width=3)
for name,(px,py) in [('bbox center',(394,689)),('head top',(375,450)),('foot approx',(408,918))]:
    d.ellipse((px-7,py-7,px+7,py+7),outline='#ff55aa',width=3);d.text((px+10,py),name,fill='#ff55aa')
im.save(out/'hero_end_actor_measurement.jpg',quality=95)
print('hero_motion_guide ready; camera-reveal correction included')
