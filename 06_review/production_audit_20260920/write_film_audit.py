"""Write reviewed film evidence and clearly separate verified cuts from production scope decisions."""
from pathlib import Path
import json
ROOT=Path(r'D:/00_projects/10_CG/Shot_Test')
OUT=ROOT/'06_review/production_audit_20260920'


def tc(frame):
    """Return 24 fps source timecode for a zero-based frame number."""
    return f'{frame//86400:02d}:{frame//1440%60:02d}:{frame//24%60:02d}:{frame%24:02d}'


boundaries=json.loads((OUT/'detected_boundaries.json').read_text())
# Classification uses the immediately adjacent decoded images, not score magnitude alone.
noise={29,30,31,32,34,41,42,44}
montage={33,35,38,39,40,45}
for i,r in enumerate(boundaries,1):
    r['id']=f'C{i:02d}'
    r['evidence']=f'cut_pairs_{(i-1)//9+1:02d}.jpg'
    r['before_frame']=r['frame']-1
    if i in noise:
        r['status']='reviewed_not_editorial_cut'
        r['note']='灯光闪烁、抖动或噪声变化；不能按检测点计镜头'
    elif i in montage:
        r['status']='reviewed_viewpoint_change_in_montage'
        r['note']='画面内容/机位突变已见，周围快速闪回尚未逐帧拉完，不能据此声称完整镜头边界'
    else:
        r['status']='verified_adjacent_frame_cut'
        r['note']='前后相邻帧看图确认构图/场景切换'
extra=[(1364,'罐体墙转罐体近景'),(4570,'角色中景转俯视椅子与角色'),(4674,'俯视转冷暗房间全景'),(4824,'房间全景转高处俯视'),(4953,'俯视转手臂近景'),(5082,'椅面糖果转俯视椅面')]
for f,note in extra:
    boundaries.append({'id':f'LOW_{f}','frame':f,'seconds':f/24,'timecode':tc(f),'status':'verified_adjacent_frame_cut','note':note,'evidence':'additional_pairs_01.jpg' if f<=4953 else 'additional_pairs_02.jpg','before_frame':f-1})
sections=[
    {'id':'SEC01','range_seconds':[0,34.9166667],'description':'黑场、线描糖果变实体、木板糖果近景','granularity':'visual_section_not_shot'},
    {'id':'SEC02','range_seconds':[34.9166667,44.4166667],'description':'绿钟与窗外夕阳','granularity':'visual_section_not_shot'},
    {'id':'SEC03','range_seconds':[44.4166667,88.75],'description':'商店纸盒/展示、罐体聚集成形、走出门口、店前机器','granularity':'visual_section_not_shot'},
    {'id':'SEC04','range_seconds':[88.75,108.75],'description':'街边行走：绿棚店、脚部、红棚店','granularity':'visual_section_not_shot'},
    {'id':'SEC05','range_seconds':[108.75,137.0833333],'description':'黑场、树影路面、树叶、墙边行走、黑场、自行车停车区','granularity':'visual_section_not_shot'},
    {'id':'SEC06','range_seconds':[137.0833333,151.9166667],'description':'学校外墙、黑场、冷走廊远景与窗边角色','granularity':'visual_section_not_shot'},
    {'id':'SEC07','range_seconds':[151.9166667,177.8],'description':'教室低机位、黑板擦、主全景、角色落座、桌椅、后墙变暗至干扰','end_accuracy':'approximate_transition_neighborhood','granularity':'visual_section_not_shot'},
    {'id':'SEC08','range_seconds':[177.8,214.7083333],'description':'灯管切换/闪烁、冷暗房间中的角色、椅子与糖果','start_accuracy':'approximate_transition_neighborhood','granularity':'visual_section_not_shot'},
    {'id':'SEC09','range_seconds':[214.7083333,243.75],'description':'快速闪回/噪声、罐体角色主观视角和女性面部','granularity':'visual_section_not_shot','internal_cuts':'not_fully_verified'},
    {'id':'SEC10','range_seconds':[243.75,251.125],'description':'罐体散落与快速切换、片尾标题','granularity':'visual_section_not_shot','internal_cuts':'not_fully_verified'}]
class_specs=[
('REF_CORRIDOR_WIDE',3407,3526,'冷走廊全景','角色在纵深处姿态/步态变化；固定建筑边线有轻微位移与倾斜变化，不能当成完全锁机','classroom_motion_01.jpg'),
('REF_CORRIDOR_CLOSE',3526,3646,'走廊窗边角色近景','角色上身摇摆、转向；窗框相对画面也有变化，未解算镜头和角色各自运动','classroom_motion_01.jpg; classroom_motion_02.jpg'),
('REF_CLASSROOM_LOW',3646,3753,'从门口看教室地面的低机位','门框/桌腿有透视位移与画面倾斜，地板反射明显；机位路径未解算','classroom_motion_02.jpg'),
('REF_BOARD_DETAIL',3753,3823,'黑板擦与粉笔槽近景','黑板擦、粉笔和板面细节清楚，构图向下/横向缓慢变化；有浅景深','classroom_motion_02.jpg; classroom_motion_03.jpg'),
('REF_CLASSROOM_HERO',3823,3963,'正对讲台的教室全景','先空景；约161–162秒角色由画面左边进入，继续向左侧课桌间推进；相机缓慢变化和轻微roll，未解算实际路径','classroom_motion_03.jpg'),
('REF_CLASSROOM_SEAT',3963,4033,'更近的角色与课桌机位','罐体角色向下收拢/落座；此处另切近机位，不能视为上一全景的连续推镜','classroom_motion_03.jpg; classroom_motion_04.jpg'),
('REF_CLASSROOM_DESKS',4033,4102,'空课桌椅中近景','桌面与椅背随横向/倾斜构图变化，木材受斜阳；路径未解算','classroom_motion_04.jpg')]
shots=[]
for ident,a,b,desc,motion,evidence in class_specs:
    shots.append({'reference_id':ident,'source_start_frame':a,'source_end_frame_exclusive':b,'source_in':tc(a),'source_out_exclusive':tc(b),'duration_frames':b-a,'duration_seconds':(b-a)/24,'description':desc,'motion_observed':motion,'boundary_status':'both_verified_adjacent_frames','evidence':evidence,'production_scope':'candidate_requires_project_decision'})
shots.append({'reference_id':'REF_CLASSROOM_REAR','source_start_frame':4102,'source_in':tc(4102),'start_boundary_status':'verified_adjacent_frames','end_boundary_status':'not_locked_transition','end_transition_seconds':[176.3333333,177.8333333],'description':'教室后墙、书法展示与窗户；画面持续变冷变暗，继而进入扫描噪声和灯管画面','motion_observed':'构图横向/倾斜变化；颜色/亮度改变显著，不能解释成单一静态灯光','evidence':'classroom_motion_04.jpg; rear_end.jpg','production_scope':'candidate_requires_project_decision'})
record={'audit_date':'2026-09-20','source':'01_preproduction/references/video/drop_official_1080p.mp4','source_sha256':'34a69cce22601bd3083d254ddd6e9986cf98cc4ce859756902ce064ca9714758','metadata':json.loads((OUT/'verified_media.json').read_text()),'methodology':['Reuse existing thumbnails first. contact_001..021 are single untimed stills, not a shot list.','Decode source sequentially to 480x270 for reviewed evidence; source video untouched.','320px scene detection thresholds 0.18 and 0.08 generate candidates, never final counts.','Inspect adjacent frames for stated cuts; inspect 0.5-second classroom samples for action.','All source ends are exclusive. Production frame 1001 mapping remains a proposal.'],'visual_sections':sections,'verified_and_rejected_boundary_events':boundaries,'additional_low_threshold_candidates':[{'frame':f,'seconds':f/24,'status':'candidate_unverified' if f not in {p[0] for p in extra} else 'see_verified_event'} for f in json.loads((OUT/'additional_candidates_008.json').read_text())],'classroom_shots':shots,'proposed_first_test':{'reference_id':'REF_CLASSROOM_HERO','duration_frames':140,'fps':24,'proposed_production_start':1001,'proposed_production_end_inclusive':1140,'scope_status':'recommendation_not_user_commitment','minimum_acceptance':['140 consecutive readable frames with reviewed camera and character entrance timing','Lighting/material continuity at start/mid/end, no missing linked assets','Cloth motion only if explicitly included; existing settled cloth is not wind animation','Separate low-cost blocking review from final shaded/composited playback; technical render completion is not art approval']},'known_gaps':['This is not a complete approved full-film shot list and must not drive a final total shot count.','Some cuts in dark scenes and all fast montage around 177–182, 214–221, 236–251 seconds need continuous frame review.','No audio stream in local reference; sound rhythm and sound clearance cannot be evaluated.','No original camera solve or measured lens/scale, no authorial narrative claims.','Full-film remake/adaptation choice, exact selected shots and delivery commitments remain user/project decisions.']}
(OUT/'film_candidates.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
rows='\n'.join(f"| {r['reference_id']} | {r['source_in']} → {r['source_out_exclusive']} | {r['duration_frames']} | {r['description']} |" for r in shots if 'source_out_exclusive' in r)
md=f'''# 原片媒体与镜头审计（2026-09-20）

原片当前主教室全景是 **00:02:39:07 → 00:02:45:03（出点不含，24 fps）**，共 **140 帧 / 5.833333 秒**。此前常用的 154–168 秒抽帧横跨低机位、黑板近景、全景和角色落座近景，不能作为一个连续镜头的时长。

## 已核实的媒体事实

- 本地文件：`01_preproduction/references/video/drop_official_1080p.mp4`。来自既有来源清单的作者公开视频流，不是制作母版。
- H.264，1920×1080，24 fps，逐帧解码 **6027 帧**，准确视频时长 **251.125 秒（00:04:11:03）**。容器摘要把它显示为 251.13 秒。
- **没有音轨**。本审计不能判断声音节奏，也没有交付音频。
- 视频带编码黑边；1920×1080 是文件尺寸，不是项目有效画幅建议。当前项目 2.37:1 输出约定另行保留。
- 证据：`ffmpeg_source_probe.txt`、`verified_media.json`；复现脚本 `audit_film.py`。

## 已有资料的限制

`01_preproduction/storyboards/film_visual_outline.md` 自身注明是按剧照建立的八个视觉段落，时码和持续时间未核对。它不是八个完整镜头。现有 `contact_001.jpg` 到 `contact_021.jpg` 其实是 21 张 480×270 单幅缩略图，没有可追溯时码；本次汇成 `existing_contacts.jpg` 供复用。原来的 `classroom_research_20260917/film_contact_sheet.jpg` 有 100–175 秒、每五秒一张，已实际查看。

本次只做低分辨率抽帧验证，没有重新下载原片、没有全片高分辨率抽帧、没有修改 .blend。

## 教室周边已逐切点验证的候选镜头

下面均以相邻前后帧确认起止切点。编号是**参考候选编号**，不是已经承诺制作的镜头编号。

| 参考编号 | 源时码 In → Out（不含） | 帧数 | 内容 |
|---|---|---:|---|
{rows}

后墙镜头从 **00:02:50:22（源帧4102）** 开始；约176.33秒出现明显扫描干扰，177.83秒已见灯管，转场没有锁定为一个精确镜头切点。不能把整个闪烁段等同一个硬切。证据 `rear_end.jpg`。

前后相邻帧证据集中在 `cut_pairs_03.jpg`、`cut_pairs_04.jpg`；0.5秒动作采样为 `classroom_motion_01.jpg` 至 `classroom_motion_04.jpg`。它们已经实际看图，不只是程序检测结果。

### 当前主教室全景可见动作

- 全景开头为空教室；约161–162秒角色由画面左缘进入，至165秒已进入左侧桌椅间。
- 画面构图和倾斜有缓慢变化。这里只确认图像变化，未区分 dolly、pan、roll 的实际数值，未测量焦距。
- 165.125秒明确切到更近机位，角色随后向下收拢/落座。不能把这次景别切换实现成上一镜头的连续推镜。
- 后墙镜头有明显从暖亮到冷暗的变化。全片复刻时需要光照/合成随时间变化；静态冷暖校色不能覆盖这段演变。

## 全片段落与切点覆盖

`overview_01.jpg` 至 `overview_03.jpg` 是每五秒采样并实际查看的全片索引；`film_candidates.json` 保存十个**视觉段落**、45个高阈值检测事件的人工分类、6个额外确认切点和其余低阈值候选。

全片主要工作域包括：糖果与木板/钟；旧商店包装和罐体聚集；街道/店面和角色步态；树影、树叶、墙面及自行车区；学校外墙与冷走廊；暖教室与冷暖变化；冷暗房间中的角色/椅子/糖果；闪回干扰、女性面部和最终散落。每个域包含多个镜头，**不等于十个镜头**。

自动检测会把灯管闪烁、运动、噪声当成切点；例如178秒附近多个高分点实际仍是同一灯管构图，已在 JSON 标记 `reviewed_not_editorial_cut`。暗场可能漏切。因此本次**没有宣称完成全片最终镜头总数**。特别是177–182、214–221和236–251秒的快速段，以及暗房间细部切换，需要下一轮连续逐帧确认。

## 下一步最小验收建议（尚未代用户定范围）

首条动画测试可选已经建好的主教室全景完整 **140 帧**，映射到制作帧 **1001–1140（含）**，24 fps。优先验收相机构图变化、角色入场时机、桌椅遮挡与路径、首/中/末光照材质连续性；先出可播放 blocking，再出有阴影和材质的测试并进入合成。最终评审至少应包含可播放文件和首中末对照，不能以出过静帧代替动画完成。

该建议不把未授权的镜头长度、角色表演或窗帘随风设为既定需求。现有窗帘是真实布料求解的静态稳定形，是否追加风动画需要纳入具体镜头规格。若下一镜头也做，落座近景应另建镜头条目（70帧），共享同一建筑资产。

全片规划还需要确认复刻/改编边界、最后要交哪些镜头、音频和角色制作范围及投入节奏。上述缺口应作为决策项，不能藏在“制作中”状态里。
'''
(OUT/'film_audit.md').write_text(md,encoding='utf-8')
print('WROTE film_candidates.json and film_audit.md')
print('hero frames',3963-3823,'near frames',4033-3963)
