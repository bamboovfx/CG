# 课桌模型参考

原实物参考：props/props_01.jpg、20160220_3cc38d.JPG、20160220_47c158.JPG；参考用途，不分发原摄影作品。

2026-10-01：imagegen 制作多视图。初版四宫格侧视带透视歧义，修订四宫格仍引起 Tripo 书斗重复和底部回环管件。用户提供侧面／正面网格截图，判为不合格，未发布。

初次 Tripo Studio P2.0 Quad 10,000 面：4191933b-d10f-4af3-844a-36f3a3511bce。导出FBX实测10,603面、30连通件、无UV。原始保留在pipeline cache，不进镜头。

v2 回到参考环节：独立正侧视图→校正400:670深高比例→以侧面为一致性依据生成正面、背面；侧框沿深度弯曲，书斗仅一个，无书包钩和额外回环。左右结构对称，两个侧槽使用同一个正侧参考。尺寸按场景适配记录，不能宣称像素精确工程尺寸。

生成提示词要求：exact orthographic elevation；zero camera elevation；far two legs occluded；single pressed steel tray；continuous depthwise inverted-U side frames；low U brace open at student front；no hooks, extra supports or looping rods；plain white background。

v2任务c572b7c7-7fb9-4182-812b-2ef6bfe775a0：实测10,848面，19连通件，仍有错误的学生侧低横杆，未发布。用户再次明确四个独立方向，撤销将左右图重复输入的做法。v3分别保存front/back/left/right；右侧由imagegen独立生成，书斗前端从左侧图的左端反转到右侧图的右端。

2026-10-01最新澄清：用户所说左侧／右侧是分别从正面绕到左、右约45°的三分之四视角。v3纯侧视输入撤销，尚未提交生成。v4保留正面／背面，重新用内置imagegen生成独立左前／右前斜侧参考。提示要求同一桌体600×400×670比例、四腿、单书斗、两侧沿深度倒U框、低U支撑在学生前方开口；白背景，无钩／回环／额外横杆。输出为生成参考，角度与尺寸尚非精密工程校准；后续以实际模型结构检查为准。

v4原始输出：exec-280e8316-f662-4ce8-9413-2546abd96d50.png（左前）；exec-480dcf81-4f8f-45fb-9dac-3bf0dd1087d3.png（右前）。项目消费图保存在v4/front.png、back.png、left.png、right.png。
