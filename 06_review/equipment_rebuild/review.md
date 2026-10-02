# Equipment rebuild — wooden cabinet and native Substance Designer materials

Updated 2026-09-11 after the user's material correction. The earlier folded-metal cabinet and Pillow material pass are superseded; its recovery copy is `07_pipeline/cache/equipment_rebuild/equipment_pre_sd.blend`.

**Current source:** `02_assets/work/classroom_equipment.blend`. Import only `AST_fluorescent_fixture`, `AST_crt_television`, `AST_equipment_cabinet`, `AST_wall_clock`, `AST_wall_speaker`; exclude `EQ_review_rig`. All original collection offsets and -Y fronts are preserved.

## Wooden cabinet

The cabinet was rebuilt as timber construction, not recoloured metal. It has 25 mm side panels, a 30 mm wooden top, real shelves, a rebated 6 mm back, base bearers, separate door stiles and horizontal rails with 18–20 mm field panels. The plain door shape follows the film's classroom cupboard rather than the ornamental profile of reference furniture. Grain runs vertically on sides/stiles/field panels, horizontally on rails and along the top board. Metric UVs and actual board thickness make end faces independently editable.

After closeup inspection, the top door reveal was reduced to **3.0 mm**. TV rubber supports now meet the wooden top at **0.0 mm measured gap**. Small bare-wood patches occur at selected contact edges and around pulls; their positions are irregular, and their rougher SD material differs from the surviving varnish. Wear is deliberately restrained, not evenly scattered.

## Actual Substance Designer delivery

Nine editable `.sbs` graphs and nine compiled `.sbsar` files are in `02_assets/materials/equipment_rebuild`. Every family was compiled by the installed Adobe `sbscooker.exe` and exported by `sbsrender.exe`; 63 actual 16-bit, 2048 × 2048 PNG outputs are in `02_assets/textures/generated/equipment_sd`.

| Family | Construction | Mapping |
|---|---|---|
| varnished_wood | CC0 Poly Haven plywood Color/Roughness/Normal inputs + native wood-fibre detail, clearcoat roughness and handling scratches | 0.6 m tile; source grain U, actual board UVs oriented along grain |
| exposed_wood | Same SD scan workflow with paler timber tone, substantially rougher exposed surface and stronger pore normal | 0.6 m tile |
| abs | Native subtle moulded microtexture, restrained colour variation and handling scratches | 0.25 m tile |
| enamel | Native coating microtexture and roughness; used on fixture and speaker housing | 0.25 m tile |
| metal | Native anisotropic rolling marks and steel roughness | 0.25 m tile |
| rubber | Native dark dielectric microtexture | 0.25 m tile |
| glass | Native fine glass roughness/normal; clear clock cover uses optical transmission | 0.25 m tile |
| paper | Native fine dielectric texture; clock dial backing and white phosphor derivative | 0.25 m tile |
| dark | Native dark graphite surface for buttons, gaskets and grille cavities | 0.25 m tile |

The first all-procedural wood fibres looked too uniform under macro review. They were reduced to a detail layer and replaced by actual wide growth-grain scan inputs, processed **inside SD**. Output images are not copied or renamed old Pillow maps. Clock numerals and divisions are now vector/geometry printing over the SD dial material, so there is no legacy raster print dependency either.

`BaseColor` uses sRGB; Roughness, Metallic, Height, Normal and AO use Non-Color. Normals are OpenGL. Wood scan normals are subdued under the clearcoat and stronger on exposed timber. Other normal branches are derived in SD with documented tile size and micrometre relief values. AO outputs are unity because no lighting is baked into material colour.

**Editable wood input binding:** The two wood graphs expose `WoodColorScan`, `WoodRoughScan`, `WoodNormalScan`. In Designer, connect the three existing 4K maps under `02_assets/textures/polyhaven/plywood/4k`. Their exact files, CC0 credit, SHA-256 and `sbsrender --set-entry` bindings are recorded in `02_assets/textures/generated/equipment_sd/manifest.json`. This binding is required to reproduce the wood graph preview; it is not an embedded copyrighted product photograph. The other seven families need no external bitmaps.

Rebuild material outputs with `07_pipeline/scripts/equipment_build_sd.py`. Logs of each real compile and render are `07_pipeline/cache/equipment_rebuild/sd_<family>_cook.log` and `sd_<family>_render.log`. `sd_validation.json` verifies all nine sources/SBSARs, all 63 output hashes and sizes, current Blender dependencies, original offsets, UV presence and contact/reveal measurements. The current blend has **zero missing images and only SD-output image dependencies**.

## Reference material research

The film's 154 / 166 / 168-second frames were actually viewed for silhouette, installation and relative material brightness. The film does not identify a manufacturer or show precise rear details. The cabinet's wood construction follows the user's explicit correction. Hardware layout, clock time and unseen rear construction remain production interpretation.

The following material photographs were downloaded and actually viewed, independently of the model-reference photographs:

- [Popular Woodworking — worn wood edge](https://www.popularwoodworking.com/techniques/furniture%E2%80%99s-battle-scars/): finish loss exposes lighter fibres at handled edges; used to distinguish finish loss from an all-over dirty layer.
- [Woodweb — cabinet finish failure](https://woodweb.com/knowledge_base/Cabinet_Door_Finish_Failure__Diagnosis.html): local clearcoat failure concentrated on lower door rails.
- [Lacquered cabinet detail](https://www.1stdibs.com/furniture/storage-case-pieces/sideboards/antique-lacquered-sideboard-from-southeast-asia/id-f_32561992/): actual wood joinery, clearcoat reflections and local abrasion. Its much heavier wear is not copied wholesale.
- [Poly Haven plywood](https://polyhaven.com/a/plywood): existing 4K CC0 material source, actually viewed and then used as real SD graph input.

Reference-only photographs retain their owners' copyright and are not texture inputs. Source URLs and hashes are in `references/material_reference_sources.json`. The earlier supplier lamp and clock photos remain recorded in `references/sources.json`.

## Final visual checks

The five equipment views and the cabinet material macro were actually rendered and viewed. Fluorescent phosphor was corrected after it accidentally inherited the dark CRT glass family. Cabinet wear spacing, grain direction and 3 mm reveal were corrected after macro inspection. The last 2 mm rubber-foot underside trim matches the top height numerically; it does not change the visible cabinet/material design.

![Wood cabinet and CRT](tv_cabinet.png)

![SD wood material macro](cabinet_sd_material_closeup.png)

![CRT rear](crt_rear.png)

![Fluorescent fixture](fluorescent.png)

![Clock](clock.png)

![Speaker](speaker.png)
