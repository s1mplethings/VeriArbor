# VeriArbor / CGKN / Promotion 完整工作与卡点报告

证据截点：2026-11-04 15:41，Asia/Shanghai。本文是进行中快照，不是完成证书；执行继续后调用数量可能增加。

## 当前结论

- VeriArbor：最小积木替换核心已实现并接入，完整 V1 要求仍为 PARTIAL。
- 产品：M1–M11 有原验收通过证据；M12 当前 FAILED，产品不可宣布交付。
- 当前主要卡点是 M12 GUI 实现质量和重复无效修改，不是目录权限。
- 最近 continuation 83 的 GUI attempt 29 已返回，但未产生有效源码差异。已设置下一次调用前安全暂停，以核对原因和缩小修复范围；未中断在途响应。
- 最终打包、当前版本 DOGFOOD、证据归档、账目关联和最终报告尚未完成。

## 1. 范围与执行边界

库根目录：`D:/VeriArbor`；宿主：`F:/CGKN-LeanLoop-V1-20261101`；产品：`F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05`。

依赖方向保持 CGKN/Promotion → VeriArbor。原 Agent、CapabilityTree、DAG、执行器、FileRunStore、GoalAcceptance、预算/UNKNOWN 记录和交付路径保留。业务源码、业务测试和项目文档由原执行链的 Worker 修改，宿主直接业务补丁为 0。没有以诊断结果替代正式验收，没有发布仓库或包。

## 2. 已完成的库与宿主工作

| 工作 | 已有结果 | 边界 |
| --- | --- | --- |
| 核心抽取 | Block、Port、Contract、EffectContract、Variant、Certificate、Adapter 等最小对象及策略 | 不是全部 V1 场景完成 |
| 兼容与局部影响 | 方向性契约、四类兼容判定、rename/default 适配器、一跳影响及局部扩大策略 | 复杂适配器仍缺 |
| 证据复用 | 验证键、重复检查阻止、证书化替换及原生组合复用接入 | 旧文本契约保守处理，不推断结构 |
| 真实替换 | M6 实际替换后复用 M7–M10 原证据，无需重跑四个里程碑 | 仅证明该次 identical 场景 |
| 安装与构建 | 独立 wheel、隔离安装/导入及源码字节一致性检查 | 未发布；不等于产品验收 |
| 宿主迁移 | 45 条切换收据，含原始哈希和回滚证据 | 最新回归仅在记录范围内 PASS |
| 上下文与协议 | 语义响应使用网关支持的 JSON schema envelope；修复时注入现有目标和验证过的依赖源码 | 不保证模型正确使用源码 |

记录内通过的检查包括：库 37、协议/Agent 961、运行时 138、投影 46、novelty/provenance 74，以及后续作用域/指导失效/里程碑去重相关专项检查。最近协议检查 110 项通过，完整文件修复输入相关 38 项通过，方向检查通过。不同检查存在重叠，不能相加当作独立总用例数。

历史较宽 Provider 测试仍保留 16 失败、14 错误、356 通过的结果，涉及归档夹具、旧生命周期和插件/流式行为假设；没有改标为通过。阶段性新测试失败及后续修复记录也都保留。

## 3. 产品现状

M1–M11 在原验收体系中 VERIFIED，覆盖项目、证据/信号、声明、活动、内容、审批、发布、排程、回执、分析和媒体能力。这个结论只表示已有验收范围通过，不表示生成测试全部通过，更不表示当前 M12 GUI 已正确接入这些能力。

M11 已处理媒体模块定位、审批/发布前真实媒体校验和浏览器预览相关问题，并有通过证据。后续 M12 全文件重写发生回退，不能将较早 GUI 版本的成功结果当作当前版本成功。

当前 `main.py` SHA-256：`97fac580ddd0b04a91c35f26a91e3554abb82ad86e8e6159864d4e49f4dce478`。

当前正式 M12 失败证据：`state/iter132-promotion-studio/promotion-05/attempts/sem-node-0155/attempt-0001.json`，checker 为 qualified-revision-8。检查等待“Browser Created Project”在页面可见时超时。该证据绑定的就是当前文件，而非旧文件。

## 4. 当前卡点及证据

| 卡点 | 观察到的事实 | 影响 / 后续动作 |
| --- | --- | --- |
| 项目创建后不显示 | 实际浏览器 project.create 返回 200，项目持久化成功；可见项目名数量 0；无 project_id 的 /api/state 返回 400 | loadProjects 先等待失败的 state 请求，未执行后续 project.list；修复启动加载、选择和刷新流程 |
| 上传失败 | 实际 GUI media.import 返回 400：path must be a non-empty string | 浏览器 base64 未转换为服务端临时文件；补齐适配、清理和真实图片/视频预览 |
| 无效重复修改 | attempt 28、29 未改变正式 main.py；29 写入字节与现有文件完全一致 | 不是写入丢失；模型复制旧实现。需要明确且更小的修改目标，避免再次整文件照抄 |
| 旧策略污染当前修复 | Agent 新叶目标包含 bootstrap，但策略仍保留“10 个模块绑定错误”的过期描述，且出现 M7.publish.send 等错误操作名示例 | 当前 11 个模块映射已全部正确；请求中 milestone 与 publish.send 应分开。必须清除旧修复目标 |
| 功能回退 | 较早版本曾验证上传、发布、重启及部分编辑；后续大范围重写丢失能力 | 必须依据当前字节重新证明功能，不能拼接不同版本的成功证据 |
| M12 完整性 | 当前 Signals 仍有占位；编辑/变体/比较、证据声明、审批参数、排程、分析历史及 UNKNOWN 对账等尚未形成当前版本完整通过证据 | 分功能闭环推进，完成全部 GUI 要求 |

当前已有进展：11 个实际 handler 身份全部匹配，直接 project.create 成功；HTTP 服务并发缺陷已修复。上述进展仍不足以通过完整 GUI。

## 5. 为什么时间拉长、出现重复

1. 早期执行器没有把实际目标源码和依赖内容完整送达，Worker 按猜测重写，导致模块映射与接口错误；现已修复输入投递，并验证 13 个实际文件进入上下文。
2. 响应格式、网关流式异常和 UNKNOWN 恢复增加了开销。UNKNOWN 均保留，不当作普通失败盲重试。
3. GUI 全文件重写造成回退，随后修复又存在“只改并发”“复制旧文件”而未完成目标的问题。
4. Agent 沿用旧策略，将已修复的模块绑定继续当成原因，分散了实际修复目标。
5. 我在 continuation 82 将最后一次尝试误认为产生了新源码，错误请求再次测量。哈希核对证明 155 的检查仍适用；系统阻止重复验收，未重跑 M1–M11，但已经发生额外 Agent 调用。这个判断错误需要计入，而不能归因于用户或权限。
6. 正式证据生成、绑定与保存本身耗时。它不是全部阶段重跑，但也不能掩盖前述无效工作。

## 6. 仍未完成的工作

### 产品主线

1. 修复项目启动/列表/选择状态与文件上传；先实际浏览器验证局部行为。
2. 完成当前版本完整 GUI：Signals/证据声明、活动内容、编辑和版本比较、渠道变体、审批、真实媒体预览、发布、排程取消改期、回执、分析历史、UNKNOWN 对账。
3. 验证跨项目隔离、非法媒体、媒体变更/丢失、审批失效、幂等性、重启持久化和无旧回执绑定。
4. 修复生成测试中的错误夹具与接口假设，完善真实启动/操作文档。
5. 生成当前产品的可运行 DOGFOOD，走原 GoalAcceptance、provenance、local_packager 和 delivery gate。

### 测试与文档债务

M12 生成测试原有 6 项中曾出现 5 通过、1 失败，失败包含 server.port 与实际 server_port 不符；这不是当前源码的全量通过结果。其他 M1–M3、M5、M6、M7、M10 的测试中也已有旧数据结构、错误状态、HTTP 假平台或存储路径假设，需要原测试执行节点修复。M11 生成测试的静态 GUI 断言不能替代真实浏览器证据。

README/TEST_PLAN 还需提供 GUI 与本地发布平台的真实启动方式、独立端口/数据目录、证据声明流程、排程时区与持久化说明。

### VeriArbor 完整门禁

真实 compatible/adaptable/breaking 三类替换见证仍未补齐；enum、wrapper、split/merge 等适配能力尚未实现；当前图映射主要覆盖 goal 边界，不是全部执行叶。旧 DAG 重试闭包仍较保守。若这些未达到用户要求，最终只能报告 PARTIAL，不能把最小核心通过写成完整 V1 完成。

### 交付与归档

需要更新 Block/Port/Adapter/Certificate 映射、关联全部实际调用、UNKNOWN 处置和成本口径、按原 Corpus loader 归档并完成两次一致重建，以及刷新两个仓库的最终报告。当前旧 FINAL_REPORT 停留在凌晨 continuation 48，不适合代表最新进度；本文用于纠正当前工作状态，不覆盖历史报告。

## 7. 调用与费用快照

2026-11-04 15:41 的原账本快照：基线 3153 条，当前 3628 条，本轮增加 475 条。

| 本轮账本项 | 数量 |
| --- | ---: |
| SUCCEEDED | 462 |
| FAILED | 2 |
| INTERRUPTED_UNKNOWN | 11 |
| qwen3.8-flash | 333 |
| deepseek-flash | 142 |
| Pro / Max | 0 / 0 |

SUCCEEDED 是 Provider 调用状态，不是业务任务完成。数值型 token 字段合计 23,316,559，另有 13 行非数值/未知字段，因此不是完整供应商计费 token 数。账本 estimated_cost 是估计值，不是供应商账单；最终费用尚未完成核对。完整 request/response/ledger 关联仍需更新，旧 300/300 关联报告已过时。

原账本前缀当前与基线相同。但历史上有 5 行曾被改动后恢复，不能据此声称从未触碰过历史账目。原 UNKNOWN 与失败记录均保留。

## 8. 完成判断与下一步

不能按“11/12 里程碑”声称已完成 91.7%；M12 集成、测试修复、最终交付与迁移完整门禁仍有实质工作量。当前无法给出可信的剩余小时数。

下一步先让原节点 143 只修复项目列表的实际失败路径，要求真实源码差异和创建后可见、刷新后仍可见的浏览器结果。随后完成上传及剩余 GUI 闭环。不会从 P0 重来，也不会重复已经可复用的 M1–M11 检查。全部交付门禁通过前，状态保持 PRODUCT_NOT_READY。

## 9. 关键证据路径

- `D:/VeriArbor/REGRESSION.json`
- `F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor/AUTHORITY_SWITCH_RECEIPTS.jsonl`
- `F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor/m12-dispatch-143a28/receipt.json`
- `F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor/m12-bootstrap-143a28-v3/receipt.json`
- `F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor/m12-product-143a28/receipt.json`
- `F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05/state/iter132-promotion-studio/promotion-05/attempts/sem-node-0155/attempt-0001.json`
- `F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05/state/iter132-promotion-studio/promotion-05/attempts/sem-node-0143/attempt-0029.json`
- `F:/CGKN-ITER-076/global-provider-budget.json`

## 后续执行补记

continuation 84：Agent 提出了 bootstrap 小范围修改，但 hypothesis.falsifying_evidence 使用了原文件 SHA，而不是当前验收要求的 receipt_hash，触发 HYPOTHESIS_EVIDENCE_UNBOUND / ADMISSION_STRATEGY_EXHAUSTED。实际 Worker 执行数为 0，未发生代码修复。不能把 Agent 提案等同于准入成功。已在 continuation 85 提供准确的原验收收据引用继续校正；尚无新的产品通过结论。
