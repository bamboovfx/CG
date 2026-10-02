"""Create a gap-free reference inventory with explicit composite ranges and uncertain transitions."""
from pathlib import Path
import json
OUT=Path(r'D:/00_projects/10_CG/Shot_Test/06_review/production_audit_20260920')


def tc(f):
    """Convert source frame f (zero based, 24 fps) to HH:MM:SS:FF."""
    return f'{f//86400:02d}:{f//1440%60:02d}:{f//24%60:02d}:{f%24:02d}'


# Starts are verified frame events unless specifically marked uncertain below.
starts=[
(0,'开场黑场、线描糖果、木板上的实体糖果','compound','uncertain','overview_01.jpg','黑场到线描及实体的内部转化尚未逐帧定段，整体覆盖至第一个明确硬切。'),
(675,'俯看木板与彩色糖果','shot_candidate','verified','cut_pairs_01.jpg',''),
(838,'绿色旧挂钟与窗格日光','shot_candidate','verified','cut_pairs_01.jpg',''),
(943,'窗外建筑剪影和低角度太阳','shot_candidate','verified','cut_pairs_01.jpg',''),
(1066,'商店室内，纸盒、墙上商品与窗光','shot_candidate','verified','cut_pairs_01.jpg',''),
(1167,'商品货架与卡片包装近景','shot_candidate','verified','cut_pairs_01.jpg',''),
(1242,'倾斜构图的罐体堆/罐体墙，罐子开始运动','shot_candidate','verified','cut_pairs_01.jpg; shop_continuity_01.jpg',''),
(1364,'密集罐体近景','shot_candidate','verified','additional_pairs_01.jpg; shop_continuity_01.jpg','低阈值补查后相邻帧确认。'),
(1422,'店门内罐体从地面聚集起身并走出门口','shot_candidate','verified','shop_continuity_01.jpg; shop_continuity_02.jpg; cut_pairs_01.jpg','23.083秒长段内按1秒采样检查为持续相机/角色变化；不把角色起身、行走各自当切镜。'),
(1976,'店外冰柜旁俯看罐体运动','shot_candidate','verified','cut_pairs_01.jpg; shop_continuity_02.jpg',''),
(2059,'店前两台红色投币机器','shot_candidate','verified','cut_pairs_01.jpg; cut_pairs_02.jpg',''),
(2130,'绿棚店面全景与角色行走','shot_candidate','verified','cut_pairs_02.jpg',''),
(2252,'罐体脚部行走近景','shot_candidate','verified','cut_pairs_02.jpg','周期性脚部运动触发很多scene分数，不应拆成几十个镜头。'),
(2392,'红棚店前角色横向行走','shot_candidate','verified','cut_pairs_02.jpg',''),
(2610,'黑场停顿','black_interval','verified','cut_pairs_02.jpg','非需要建模的镜头。'),
(2668,'铺地砖上的树影','shot_candidate','verified','cut_pairs_02.jpg',''),
(2768,'树叶与天空近景','shot_candidate','verified','cut_pairs_02.jpg','画面本身含额外黑边/较窄有效区域。'),
(2901,'墙面、树影与角色行走','shot_candidate','verified','cut_pairs_02.jpg',''),
(3013,'黑场停顿','black_interval','verified','cut_pairs_02.jpg',''),
(3061,'自行车停车区，角色在纵深处行走','shot_candidate','verified','cut_pairs_02.jpg; cut_pairs_03.jpg',''),
(3290,'学校外墙窗格与空调','shot_candidate','verified','cut_pairs_03.jpg',''),
(3390,'黑场停顿','black_interval','verified','cut_pairs_03.jpg',''),
(3407,'冷色走廊全景，角色在纵深处','shot_candidate','verified','cut_pairs_03.jpg; classroom_motion_01.jpg',''),
(3526,'走廊窗边罐体角色近景','shot_candidate','verified','cut_pairs_03.jpg; classroom_motion_01.jpg; classroom_motion_02.jpg',''),
(3646,'教室门口低机位，地板反射和桌腿','shot_candidate','verified','cut_pairs_03.jpg; classroom_motion_02.jpg',''),
(3753,'黑板、擦板和粉笔槽近景','shot_candidate','verified','cut_pairs_03.jpg; classroom_motion_02.jpg; classroom_motion_03.jpg',''),
(3823,'教室主全景，角色由画面左缘入场','shot_candidate','verified','cut_pairs_03.jpg; classroom_motion_03.jpg','当前 sq010/sh010 的最直接参考，140帧；角色入场前有空景。'),
(3963,'更近机位中角色下沉/落座','shot_candidate','verified','cut_pairs_03.jpg; classroom_motion_04.jpg','明确另切机位，不是主全景连续推近。'),
(4033,'空课桌椅与斜阳','shot_candidate','verified','cut_pairs_03.jpg; cut_pairs_04.jpg; classroom_motion_04.jpg',''),
(4102,'教室后墙与书法展示，日光变暗变冷并进入扫描干扰','shot_candidate','verified','classroom_motion_04.jpg; rear_end.jpg; dense_rear_to_lamp.jpg','包含尾部扫描干扰；4268是干扰画面后第一帧清晰教室灯管，不能把干扰内部scene峰值算切镜。'),
(4268,'教室灯管与冷暗空间防护灯管交替，灯光闪烁','compound','uncertain','dense_rear_to_lamp.jpg; cut_pairs_04.jpg; dark_continuity_01.jpg','外边界确认；内部两个灯管机位交替尚未枚举每次1–数帧闪回。'),
(4364,'冷暗房间低机位仰视角色，背后灯管','shot_candidate','verified','cut_pairs_04.jpg; dark_continuity_01.jpg',''),
(4460,'冷暗房间角色中景，背景桶和管线','shot_candidate','verified','cut_pairs_05.jpg; dark_continuity_02.jpg',''),
(4570,'俯看椅子与画面右侧角色','shot_candidate','verified','additional_pairs_01.jpg; dark_continuity_02.jpg',''),
(4674,'冷暗房间全景，椅子、门与角色','shot_candidate','verified','additional_pairs_01.jpg; dark_continuity_03.jpg',''),
(4824,'高处俯看角色向椅子伸手','shot_candidate','verified','additional_pairs_01.jpg; dark_continuity_03.jpg; dark_continuity_04.jpg',''),
(4953,'罐体手臂倒出糖果，镜头向下跟随糖果到椅面','shot_candidate','verified','additional_pairs_01.jpg; dense_hand_to_chair.jpg; dark_continuity_04.jpg','208.667–210秒按2帧步长查看为连续下移构图；未发现原先疑似的暗场漏切。'),
(5082,'俯看椅面几颗糖果，光照变亮','shot_candidate','verified','additional_pairs_02.jpg; dark_continuity_05.jpg',''),
(5153,'房间闪回、走廊角色、线描/空背景角色与扫描噪声','compound','uncertain','cut_pairs_05.jpg; ending_continuity_01.jpg; dense_glitch_to_figure.jpg','外入点是硬切；尾部新角色画面与扫描噪声叠化。5305按新画面清晰可读的审计分界，不是原片硬切。'),
(5305,'近距离/主观视角中罐体角色摇动，背景为冷色竖向板面','shot_candidate','uncertain','dense_glitch_to_figure.jpg; ending_continuity_02.jpg; ending_continuity_03.jpg','入点5305是叠化后的审计分界，真实新图像已在5297附近开始出现。主体连续运动并有景深/失焦变化，未据运动峰值再拆镜。'),
(5647,'黑色前景遮挡从角色覆盖到面部','compound_transition','uncertain','dense_figure_to_face.jpg','5647开始明显遮挡，5649几乎全黑，5651面部清楚出现；剪接可藏于遮挡中，不声称单一精确硬切。'),
(5651,'女性面部侧向特写，轻微动作与焦点变化','shot_candidate','uncertain','dense_figure_to_face.jpg; female_transition.jpg; ending_continuity_03.jpg; ending_continuity_04.jpg','入点取遮挡后面部可辨帧；原始剪接点可能位于5649–5651，出点5850相邻帧硬切确认。'),
(5850,'罐体/糖果散落的俯视与近地面快速变化','compound','uncertain','cut_pairs_05.jpg; ending_continuity_04.jpg; dense_end_to_title.jpg','5850入点硬切确认；5864已有明确新机位，内部拆分及高速运动/变焦需进一步逐帧确认；5883开始明显扫描干扰。'),
(5883,'扫描干扰转黑底片名 dro:p 与亮斑','title_transition','uncertain','dense_end_to_title.jpg; ending_continuity_04.jpg; ending_continuity_05.jpg','5883为明显干扰起点；5894首次能辨片名，均为图像事件不是两个已确定制作镜头；最后一帧6026。')]
rows=[]
for i,(start,description,kind,status,evidence,note) in enumerate(starts):
    end=starts[i+1][0] if i+1<len(starts) else 6027
    transition_in='hard_cut'
    transition_out='hard_cut'
    if start==0:transition_in='media_start'
    if start==4268:transition_in='hard_cut_after_glitch'
    if start==5305:transition_in='glitch_dissolve_audit_boundary'
    if start==5647:transition_in='occlusion_transition_start'
    if start==5651:transition_in='occlusion_reveal_audit_boundary'
    if start==5883:transition_in='glitch_transition_start'
    if end==5305:transition_out='glitch_dissolve_audit_boundary'
    if end==5647:transition_out='occlusion_transition_start'
    if end==5651:transition_out='occlusion_reveal_audit_boundary'
    if end==5883:transition_out='glitch_transition_start'
    if end==6027:transition_out='media_end'
    rows.append({'reference_id':f'REF{(i+1):03d}','source_start_frame':start,'source_end_frame_exclusive':end,'in_timecode':tc(start),'out_timecode_exclusive':tc(end),'duration_frames':end-start,'duration_seconds':(end-start)/24,'visual_description':description,'entry_type':kind,'status':status,'transition_in':transition_in,'transition_out':transition_out,'evidence':evidence.split('; '),'notes':note,'production_commitment':False})
assert rows[0]['source_start_frame']==0 and rows[-1]['source_end_frame_exclusive']==6027
assert all(a['source_end_frame_exclusive']==b['source_start_frame'] for a,b in zip(rows,rows[1:]))
assert sum(r['duration_frames'] for r in rows)==6027
payload={'title':'dro:p complete-coverage reference inventory','audit_date':'2026-09-20','source':'01_preproduction/references/video/drop_official_1080p.mp4','source_sha256':'34a69cce22601bd3083d254ddd6e9986cf98cc4ce859756902ce064ca9714758','fps':24,'frame_basis':'zero-based source; end exclusive','coverage':{'source_start_frame':0,'source_end_frame_exclusive':6027,'uncovered_frames':0,'overlap_frames':0,'container_count':len(rows),'final_shot_count':None,'final_shot_count_reason':'entries include black intervals, title, transitions and composite montage ranges; not a locked editorial shot count'},'status_definitions':{'verified':'outer adjacent-frame cut events visually checked; interior checked with sparse/dense samples as documented, not a claim of every-frame viewing','uncertain':'contains unresolved internal shots or an audit boundary inside a transition; concrete source span retained'},'entries':rows,'unresolved_compounds':[{'source_range':[0,675],'issue':'opening wireframe/material transformation boundaries and any editorial subsegments not locked'}, {'source_range':[4268,4364],'issue':'two lamp viewpoints intercut; internal 1–several-frame alternations not fully enumerated','known_event_frames':[4319,4331]}, {'source_range':[5153,5305],'issue':'rapid flashback and progressive glitch/line-art transition; incomplete microcut inventory','known_event_frames':[5153,5158,5162],'dissolve_overlap_observed':[5297,5305]}, {'source_range':[5647,5651],'issue':'cut hidden by foreground occlusion; face reveal at5651 verified as visible event, edit may be5649–5651'}, {'source_range':[5850,5883],'issue':'final scattering has changed viewpoints and extreme motion; known change at5864, remaining internal boundaries unresolved'}, {'source_range':[5883,6027],'issue':'glitch/title visual-event start rather than hard editorial cut; title readable by5894'}],'verification_notes':['All listed evidence sheets actually visually inspected.','Scene detection only generated candidates. Periodic foot motion, light flicker and random noise peaks were rejected.','Full-film timeline is covered without gaps, while exact final shot count deliberately remains unset.','Local reference has no audio; no audio rhythm claims.','No source video or .blend edited.'],'recommended_next_action':'Use this as PM reference inventory. Split explicitly unresolved composite entries before final shot locking and preserve current hero REF027 (3823–3963) priority.'}
(OUT/'full_film_shot_inventory.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
header='''# 《dro:p》全片连续覆盖镜头候选清单

审计日期：2026-09-20。源文件 `01_preproduction/references/video/drop_official_1080p.mp4`，24 fps，6027帧，251.125秒，无音轨。所有源帧为**零起始**，Out **不含**。

本清单完整覆盖 **[0,6027)**，无遗漏区间、无重叠，但**不是最终锁定镜头总数**。条目包括镜头候选、黑场、转场、片尾和未完全拆分的复合段。明确保留的不确定性位于条目内，而不是漏掉对应时间。

`verified` 表示外边界经相邻帧看图核实，内部按对应采样资料查过；不是声称每帧都看过。`uncertain` 表示内部微切仍待拆，或审计分界落在叠化/遮挡转场中。程序 scene 阈值从未直接当成最终镜头边界。

当前教室主全景对应 **REF027，源帧3823–3963（140帧）**。本清单没有改变任何制作编号、既定源工程或用户承诺范围。

| 条目 | 源帧 [In,Out) | 时码 In → Out | 帧数 | 类型/状态 | 可见内容 |
|---|---:|---|---:|---|---|
'''
lines=[]
for r in rows:
    lines.append(f"| {r['reference_id']} | {r['source_start_frame']}–{r['source_end_frame_exclusive']} | {r['in_timecode']} → {r['out_timecode_exclusive']} | {r['duration_frames']} | {r['entry_type']} / {r['status']} | {r['visual_description']} |")
footer='''

## 本轮解决的关键问题

- **后墙到灯管**：4267仍是扫描干扰，4268（177.833333秒）首次是清晰教室灯管。证据 `dense_rear_to_lamp.jpg`。
- **两个灯管交替**：4268–4364保留复合段，能确认教室普通灯管与冷暗房间防护灯管两个画面交替。178秒的很多检测峰值只是亮灭，不是不同镜头。相邻画面变化至少包含4319与4331，尚未枚举全部短闪回。
- **暗房镜头**：185.833333、190.416667、194.750000、201.000000、206.375000、211.750000秒的构图切换已看相邻帧确认。证据 `additional_pairs_01.jpg`、`additional_pairs_02.jpg` 与 `dark_continuity_02..05.jpg`。
- **倒糖果不是两镜**：208.667–210秒密集采样显示手臂→下落糖果→椅面是连续向下取景，不应由于景物变化随意新增切点。证据 `dense_hand_to_chair.jpg`。
- **214.7–221秒**：从房间闪回到走廊、线描角色、扫描噪声，再叠化到近距离角色。5297附近已出现下一画面，5305起清晰可辨。清单以5305作审计分界，明确不是可测得的硬切。证据 `ending_continuity_01.jpg`、`dense_glitch_to_figure.jpg`。
- **女性面部入点**：5647前景黑色遮挡开始，5649几乎全黑，5651面部清楚出现。隐藏剪接可能发生在5649–5651；清单保留独立四帧转场容器，不伪造唯一硬切。证据 `dense_figure_to_face.jpg`。
- **片尾**：5850从面部硬切至散落；5864明确换机位；5883开始扫描干扰，5894已有可辨片名。散落和片名分别按复合段/片尾条目完整收纳。证据 `cut_pairs_05.jpg`、`dense_end_to_title.jpg`。

## 明确待拆范围与覆盖

1. `[0,675)`：开场黑场、线描与实体的连续转化，内部制作分段未锁。
2. `[4268,4364)`：灯管闪回交替，内部短切未完全枚举。
3. `[5153,5305)`：快切、线描、扫描噪声和叠化，内部镜头总数未锁。
4. `[5647,5651)`：遮挡转场，原始隐藏剪接位置不能直接看清。
5. `[5850,5883)`：最终散落的快速机位变化，至少5864换机位，其余待复核。
6. `[5883,6027)`：干扰转片名/亮斑及结束，作为片尾整体；不以每次随机闪烁计镜头。

这些范围已有可制作内容和明确覆盖，不应放入“无资料”状态。全片最终镜头总数保持空值，直到复合段拆分完成并由项目决定实际制作边界。结构化字段、外部转场类型、证据文件和逐条注释见同名 JSON。

新增接触表仅由已有本地视频缩小解码，保留参考用途；没有下载新媒体，没有修改源视频、规范或 .blend。
'''
(OUT/'full_film_shot_inventory.md').write_text(header+'\n'.join(lines)+footer,encoding='utf-8')
print(json.dumps({'entries':len(rows),'total_frames':sum(r['duration_frames'] for r in rows),'verified_containers':sum(r['status']=='verified' for r in rows),'uncertain_containers':sum(r['status']=='uncertain' for r in rows),'hero':[r['reference_id'] for r in rows if r['source_start_frame']==3823]},ensure_ascii=False))
