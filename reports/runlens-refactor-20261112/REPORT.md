# 2026-11-13 默认主链瘦身：代码接线完成，运行验证待执行

本节仅描述本轮源码修改，不覆盖下方历史测试或独立验收结论。历史 V1—V6、两次 UNKNOWN、费用预留、候选和 Gateway 服务未改动。本轮仅静态解析，没有任务运行、Provider、测试执行、发布或 ACFV。

| 范围 | 实际改动与保留边界 |
| --- | --- |
| 默认装配 | `F:/CGKN-LeanLoop-V1-20261101/cgkn/application/goal_driven.py` 保留 ProjectSession → HostPlanningScope → GoalComposer → 原接纳 → DAGRunner → 原收据/验收。删除每轮重复 schema 构造、重复执行器说明投影和提示中的字段示例副本；公开 schema 隐去 Host 身份字段。接口变更时才重建 schema。 |
| 项目职责 | `cgkn/application/project_strategy.py` 保存可选工作偏好和按需演化 recipe；媒体专用摘要字段退出默认上下文。原结果仍有精确可读引用。项目检查器仍由 `completion.checker_path/checker_sha256` 注入，保持实际对象、检查器身份和要求范围绑定；检查器时限可显式配置且受项目时限约束。 |
| 可选 Skill | `cgkn/adapters/veriarbor/skill_authority.py` 只在配置启用/使用 Skill 或恢复已有 Skill 目录时装配。`D:/VeriArbor/src/veriarbor/skills.py` 的晋级次数可由项目策略提供；旧默认仍为两次成功、共享两种上下文。收据、目标项目、语义/实用性/执行证据与适用性检查不变。 |
| 生长与消费 | `cgkn/adapters/veriarbor/component_package.py` 的实现来源不再限定模型 Worker；具有写入契约的已声明生产者也可供现有组件执行器消费。Host 仍验证真实提交收据、入口字节、Port 与效果。默认保留组件装配，未为瘦身关闭生长能力。 |
| 限制归位 | 上下文扩张/执行预留/近期结果数/节点分解偏好移至 `work_strategy`；`planning_scope.py`、`exchange.py`、`llm.py` 不再把 3 次上下文或 4 次规划调用当成普遍技术上限。正整数校验、实际 Permit/单一预算、Worker 总轮数和最后请求检查继续生效；显式硬节点限额优先。 |

前：CLI → 每次重建公开协议 + 两份执行器说明 + 固定探索参数 + 默认 Skill 资格装配 → 原 Agent/执行链。
后：同一 `scripts/run_goal_driven.py` → 校验项目策略 → 一份接口定义及缓存 schema → 按需 Skill/演化上下文 → 同一 Agent/执行链。没有第二个 Planner、状态库、生成器或发布器；未删除无法确认无调用者的历史模块，它们也未因此加入默认路径。

**加载与调用**：正常配置可增加以下字段，仍使用原 CLI。`project_evolution` 在指定决策时为原 Planner 提供构建/复用/组合/替换/退出建议入口，不另发模型请求、不自行接纳提案。输出使用原 TreeEdit → 有界 Worker/工具 → 候选检查 → 收据 → `local.component@1`，不是单独生成 SKILL.md。检查器或策略可以作为组件内候选文件生成；激活新版及改变必要要求仍走已有所有者授权/配置版本机制。

```json
{
  "work_strategy": {"context_expansions": 3, "worker_context_expansions": 3,
    "execution_reserve_base": 1, "execution_reserve_per_requirement": 3,
    "recent_results": 2, "max_new_nodes_per_decision": 4},
  "project_evolution": {"reason": "当前缺口需要一个可复用能力", "observations": [], "on_decision": 1},
  "enable_skills": false,
  "skill_qualification_policy": {"minimum_success_count": 2, "minimum_context_count": 2}
}
```

**迁移**：上述字段均可省略；旧项目探索默认和 Skill 晋级标准保持原义。`resource_and_effect_limits` 的显式硬限额不被策略放宽。项目可在 `work_strategy.result_fields` 指定需要的业务摘要字段、在 `instructions` 添加工作偏好；完整结果继续按引用读取。已有冻结配置不能就地改写，本轮没有迁移旧运行库，也不复活旧窗口。已有正常源码冻结机制包含新增模块；恢复历史运行仍需原版本/后继机制。可选执行器继续使用原 registry 和 `application_executors` 编译接入，不新增模块加载平台。

**下一轮测试入口（本轮未执行）**：在 Host 根目录，使用当前 Core 环境运行：

```powershell
D:/anaconda/python.exe -m pytest -q tests/application/test_project_assembly.py tests/runtime/test_graph_commit.py::test_optional_archive_cannot_hide_unknown_outcome tests/runtime/test_graph_commit.py::test_archival_preserves_goal_obligations tests/application/test_interface_autonomy.py::test_port_semantics_and_explicit_numeric_adapter_do_not_grant_pass
```

新增源码 `tests/application/test_project_assembly.py` 使用两个独立项目说明和检查器，NoProvider 遇任何派发即失败；由工程夹具通过原有确定性文件执行器真实产生实现，经原接纳/候选检查/收据链注册和 Port 消费，再构筑兼容新实现并归档恢复，验证新收据及历史保留。包含策略不可扩大授权、越界路径拒绝和 Skill 次数不替代收据的负控制。这里只准备源码，不生成成功记录；未来通过也只证明机制。

**静态结果与剩余范围**：10 个本轮 Python 文件 AST 解析、3 份现有治理 JSON 解析通过；没有导入项目执行。新测试尚未运行，无法据此承诺行为通过。默认路径本轮没有已知占位实现；更广的历史兼容入口清理和真实 Agent 自主形成能力不在本轮结论内。独立验收仍按原报告保持未完成。轻量原字节保护：`slimming-before-20261113/`，仅含本轮改动文件及起始 Git dirty 清单。

---

# 2026-11-12 提交/恢复路径修复：无新增 Provider 调用，定向 36 项通过

本轮不增加 Provider 调用，只修 successor3 最后候选为什么无法经过正常链路提交。真实 product 工作区、旧账本、旧失败和原始响应均未改写；没有发布，也没有进入 ACFV。

## 实际根因（successor3）

- **最后一个已完成步骤**：第 5 次 Worker 响应写入 `src/consumer.py`。候选在 `successor3/run/.../candidates/node-consumer-impl-001/attempt-0001/src/consumer.py`（1,684 字节，sha256 `8e4549d5...`），内容与保存的最后一个模型候选一致。
- **第一个未完成步骤**：没有显式提交意图。第 6 次响应为 `needs_escalation=true, actions=[]`，Host 没有收到“最后动作 + 提交”的信号，节点以 BLOCKED 结束。`consumed.json` 从未生成；即使当时有提交意图，精确交付检查也会失败。
- **轮数与上下文**：`max_rounds=6`；Worker 连续 5 次重写 `src/consumer.py`，没有使用 `run_tests`/`read_file` 形成最终验证；第 6 次把协议上下文额度耗尽误读成“不能再执行动作”，于是升级。直接原因是 Worker 协议缺少“最后一批动作 + 显式提交意图”，加上候选不完整。
- **分类结论**：未发出提交意图（是）；候选/交付文件不完整（是，缺 `consumed.json`）；正常检查未运行（是，因为没有进入提交）；局部循环结束未进入本来可执行的提交（是）；授权/预算禁止继续（仅第二节点 `node-consumer-retry-002` 在 48/48 前被拒绝，第一节点不是预算原因）。

## 修改位置

- `cgkn/execution/file_actions.py`：Worker schema 增加可选 `submit`；校验允许它与必需字段共存，拒绝 `submit` 与 `needs_escalation` 同时出现；原有动作/路径/权限校验不变。
- `cgkn/executors/llm.py`：同一响应可携带最后动作与 `submit:true`；Host 机械应用动作、运行本地测试后立即返回 SUCCEEDED，由既有 DAGRunner 执行精确交付检查并提交，不再强制发送空 actions 的额外模型调用。新增 `_recovered_submission`：按声明的候选哈希和 leaf 写范围验证已有候选，返回 SUCCEEDED，**不调用 Provider**。Prompt 明确说明两种提交方式和“提交不绕过检查”。
- `cgkn/runtime/dag_runner.py`：`recovered_submission` 恢复时，从指定 source node/attempt 的 `candidates/` 目录按精确哈希和当前 leaf 写范围复制候选；所有 file-worker 结果都暴露 `candidate_ref` 和 `candidate_hashes`，失败候选可见。交付检查、原子发布和收据仍走原有 `verified_proof`/`commit_node_execution`/`publish_candidate`，没有新发布器或状态权威。
- `cgkn/application/goal_driven.py`：`llm.cheap@1` 公开配置允许 `recovered_submission`；compact 执行结果保留 `candidate_ref`/`candidate_hashes`/`submission_intent`/`recovery_source`，供后续 Planner 读取已有候选，而不是只复制文件。

## 定向复验

- **36 项定向测试通过**：JUnit `interface-small/submission-recovery-recheck.xml`。新增 4 项：
  1. 最后动作 + `submit:true` 且候选完整：正常提交、`node_commit_receipt_id`、仅 1 次模型调用；
  2. 最后动作 + `submit:true` 但缺 `consumed.json`：精确交付检查失败，无收据，候选保留在 `candidates/`；
  3. 已保留候选的 `recovered_submission`：无 Provider 调用、精确哈希校验、正常提交和收据；
  4. 篡改候选哈希：拒绝，无收据，不调用 Provider。
- **隔离候选检查**：保存的模型 consumer 候选配合种子 `src/tool.py`，在临时工作区输出精确 `{"records":4,"total_ms":3250,"unit":"ms"}`，冻结检查器返回 `R_JSONL=true, R_CONSUMER=true`（`successor3/candidate-check.json`）。其中 `consumed.json` 是运行该候选生成的**本地测试输出**，不是模型生成的交付物；该检查只是机制证明，不是新的真实自主成功。
- **successor2 未复用种子的直接原因**：种子工具被复制到工作区，但没有作为可见的已知产物进入 Planner 的树/上下文；Planner 只看到 `predecessor.json` 摘要和“R_JSONL 未验证”，于是创建 normalizer 实现。后继配置增加了 `inputs/known_tool.py`/`known_tests.py` 只读上下文，并暴露候选哈希；模型仍自行判断，未被强制信任旧产物。
- **保留**：原始 normalizer、保存的 consumer 候选、原始 Worker 响应、旧账本/失败、successor3 候选目录均保留；没有修改真实 product 工作区，没有为历史运行补造成功收据。

## 仍缺的业务内容

- consumer 尚未通过正常节点正式提交，`delivery.json`/`normalized.json`/`consumed.json` 不在正式工作区；CSV、组件注册/Port 消费、版本门槛、发布和 ACFV 仍未完成。
- 48/48 累计调用上限没有增加；本轮没有新的付费授权。后续真实续跑应使用已修通的提交/恢复路径完成 consumer 正式交付 → CSV → 组件/Port，再评估原版本门槛；不得把离线复验写为版本 PASS。

---

# 2026-11-12 后继真实续跑：48/48 调用耗尽，JSONL consumer 候选通过隔离检查但未提交

按新附件授权执行了合法后继续跑；**没有发布，没有进入 ACFV**。旧 16 次账本只读保留，新请求分别记在独立后继账本中；没有改旧账本、旧失败或旧截止时间。

| 运行 | 调用 | 输入/输出 token | 估算费用 | 结果 |
|---|---:|---:|---:|---|
| 原始运行 | 16 | 105,986 / 8,789 | CNY 0.282284 | normalizer 工具成功；consumer envelope 缺字段被拒；无 CSV |
| 失败 successor | 1 | 33,445 / 3,000 | CNY 0.09089 | Planner 输出上限 `stream_output_token_limit`，无业务动作；UNKNOWN 保留 |
| successor2 | 13 | 102,187 / 11,651 | CNY 0.297582 | Planner 未按种子复用，normalizer 节点路径范围错误，撞 8 次决定上限 |
| successor3 | 18 | 114,219 / 9,540 | CNY 0.304758 | 修正 consumer 写范围；两次协议遗漏纠偏；Worker 产出正确 consumer 候选；context/round 耗尽，第二节点预算拒绝 |
| **累计** | **48/48** | **355,837 / 32,980** | **CNY 0.975514** | 调用上限先到；无发布、无 ACFV |

- **合法续接**：后继配置绑定原 run `duration-normalization-small-20261112`（配置身份 `b48f09a1...`）、旧 16 次账本、旧工具/测试哈希和旧 consumer 失败；新工具/测试/consumer 候选按哈希种子复制，`seed-provenance.json` 记录来源。旧账本与旧失败均未改写。
- **真实 consumer 候选**：最后一次已付费 DeepSeek Worker 响应（`node-consumer-impl-001`）生成 `successor3/candidate-consumer-971238.py`（sha256 `8e4549d5...`，1,684 字节）。在隔离临时工作区使用种子 `src/tool.py` 运行，输出精确为 `{"records":4,"total_ms":3250,"unit":"ms"}`，冻结检查器返回 `R_JSONL=true, R_CONSUMER=true`（证据 `successor3/candidate-check.json`）。
- **但未提交**：该 Worker 动作只应用在候选 staging；正式 product 工作区没有 `src/consumer.py`、`delivery.json`、`normalized.json` 或 `consumed.json`，也没有执行 `goal.acceptance`。第二节点 `node-consumer-retry-002` 在发送前被 48/48 调用上限拒绝。候选检查不是生产收据，不把旧节点或本轮节点写成版本 PASS。
- **CSV**：未开始；`src/tool.py` 仍是 JSONL-only，`phase2-extension` 未应用。
- **组件/Port**：未完成；没有真实实现/Variant → Receipt 绑定组件包 → 注册 → `local.component@1` Port 消费。
- **D3**：模型在候选 consumer 中已去掉额外的 `mean_ms`，但未形成正式交付；旧记录的 `mean_ms` 失败仍保留为历史。
- **版本/发布**：`VERSION_VERDICT=BLOCKED`，`RELEASE_STATUS=NOT_RELEASED`；没有 commit/push/tag/GitHub Release。**ACFV_ADOPTION=NOT_STARTED**，没有 ACFV 入口、切片或付费调用。
- **费用**：旧 16 次 + 新 32 次 = 48 次；估算 CNY 0.975514（其中 1 次 UNKNOWN，0.09089；其余 47 次有实际 usage）；外层 OpenCode 费用 UNKNOWN，未计入。输入/输出/金额均未超限，先到的是调用次数上限。
- **源码/配置身份**：当前 Core `d3ab0f3...`、Host `6e30806...`（含 D1/D2 修复和既有 dirty changes）；失败 successor 配置身份 `f823d6b3...`，successor2 `66017e3b...`，successor3 `9b2be203...`；种子工具 `e14cd103...`、种子测试 `ed9f7950...`、旧 consumer 候选 `60b99c73...`。
- **尚未完成**：通过正常节点提交正确 consumer 与 `delivery.json`/实际产物 → 独立检查器 → CSV 正式 extend → 组件注册和 Port 消费 → 版本门槛。需要新的、明确覆盖剩余工作的付费授权和窗口；不得直接改旧账本或换 run_id 清零。当前调用上限已耗尽，本轮停止新增派发。

---

# 2026-11-12 原始真实小测：16 次调用耗尽，未过版本门槛

本轮按新用户指令实际补齐了授权、当前官方费率和具体模型 ID，并在正常入口 `scripts/run_goal_driven.py start` 上执行了一次真实小测。**没有发布，没有进入 ACFV。**

| 项目 | 实际结果 |
| --- | --- |
| 授权 | `current-chat:user-directive-2026-11-12-veriarbor-jsonl-csv-small-CNY3-200k-in-30k-out-16-attempts-1200s-direct-account`，写入 `phase1.json` 及账本每次调用。 |
| 模型/费率 | Planner `qwen3.7-flash`，Worker `deepseek-flash`；官方价 2026-11-12 核对，冻结保守上界 CNY2/M 输入、CNY8/M 输出（含 DeepSeek 高峰、无缓存折扣）。 |
| 阶段 1 消耗 | 16/16 次调用（12 规划、4 生成），105,986 输入 / 8,789 输出 token，估算 CNY 0.282284，132.5 秒；无 UNKNOWN、无发送前拒绝。 |
| 阶段 1 结果 | `node-jsonl-normalizer` 由真实 Worker 产出并经正常接纳、执行、收据绑定；`src/tool.py` 在样本上输出公开预期值，空输入语义正确，5 个本地测试通过。`node-jsonl-consumer` 未交付；外置检查器 `--phase jsonl` 仍因缺少 `delivery.json` 失败。 |
| 阶段 2 | 未开始。没有合格 JSONL 交付，没有填写父配置身份，没有 extend，没有 CSV。 |
| 版本/发布 | `VERSION_VERDICT=BLOCKED`，`RELEASE_STATUS=NOT_RELEASED`。未 commit、未 push、未建 tag、未创建 GitHub Release。 |
| ACFV | 未开始；没有安装、导入、governed 入口调用或付费派发。 |
| 外层 OpenCode | 费用 UNKNOWN（未被项目账本计量，不并入 CNY3）。 |

主要阻塞与工程缺陷（均保留原始失败）：

1. **D1：已记录的有效 Worker 响应被丢弃。** `cgkn/executors/llm.py` 的 schema 修复分支在 `actions` 非空时主动抛错，导致一次已付费的 consumer/tests/delivery.json 响应（1,669 输出 token）没有应用，节点失败后再次重试。
2. **D2：规划上下文扩张按每个决定固定消耗调用。** 三个决定共用了 12 次规划调用（每个决定 3 次上下文扩张 + 1 次决定），在 16 次阶段上限下，尚未执行验收和 CSV 就已耗尽。修复需在 `cgkn/application/goal_driven.py` 的 planning allocation 中为后续决定、验收和生成保留额度，或把扩张降为显式预算项。
3. **D3：consumer 业务输出不符公开契约。** 已记录的 consumer 响应额外返回 `mean_ms`，而公开 `consumer_result` 只允许 `records,total_ms,unit`；即使应用也需要一次真实修复调用。

证据位置：`interface-small/witness/run/`（账本、决策、上下文、attempt、工作区）、`interface-small/phase1-start.log`、`interface-small/phase1-status.json`、`interface-small/real-20261112-summary.json`、`interface-small/witness/preflight.json`、`interface-small/witness/authorization-status.json`。原始 `offline.xml` 到 `recheck-5.xml` 及本轮 `identity-check-current.xml` 保留；12 个唯一机制场景（18 个测试项含参数化）在真实运行前以当前源码复验通过，但 fake Provider 只证明接线，不构成本轮真实自主成功。

运行源码绑定：Core `d3ab0f3043996c3ee3c6debb6c60fe9f537785cb`（main，含既有 dirty changes）；Host `6e30806dc99a1151b3f389bf5cd313d2b363e4f5`（`codex/leanloop-v1-20261101`，含既有 dirty changes 与未跟踪的 `tests/application/test_interface_autonomy.py`）；checker `af616c81...`；冻结源摘要 `98c7df75...`（221 个 Host 源）与 `b0128c87...`（28 个 Core 源）；配置身份 `b48f09a1...`。真实失败发生时运行源码没有被修改；本轮随后做的 D1/D2 修复是**离线后继代码**，不改变上述真实运行的冻结源码身份、账本、失败和费用，也不把旧失败改成 PASS。

阶段截止后只做了本地收回与核对：运行已交付的 `src/tool.py` 生成 `normalized.local.json` 和 `empty.local.json`，运行其 5 个本地测试，并核对账本与记录响应；没有新增 Provider 派发、没有写产品代码、没有补造验收。

## D1/D2 离线修复与定向结果（续）

本轮只做代码修复和定向离线复验；没有新增付费调用，没有改旧账本、旧 run_id 或旧 attempt，也没有执行真实续跑。

### D1：已保存的 consumer 响应被“actions 非空”截断

- 原始失败：`attempt-0001` 的 `GatewayCompletionError: schema_validation_failed`；保存的响应只有 `schema_version,node_id,summary,actions`，缺 `expected_outputs,confidence,needs_escalation,escalation_reason`；`attempt-0002` 被 `max_api_calls` 阻断。原始响应保存在 `witness/run/.../provider_calls/5fa7764.../error.json`，本轮复制为测试夹具 `tests/fixtures/worker_schema_incomplete_consumer.json`（sha256 `60b99c73...`）。
- 旧行为：`cgkn/executors/llm.py` 的 schema 修复分支先调用 `repair_worker_envelope`，但在 `actions` 非空时主动抛 `ProposalError`（修复前位于该文件的 `schema_validation_failed` 分支，约 447-458 行），随后返回 `INVALID_OUTPUT`；候选文件和已付费响应被丢弃。
- 修复：`llm.py` 现在把修复后的 proposal 作为**已付费的 synthetic completion** 排入同一 Worker 循环，下一轮不再请求模型，而是重新走 `validate_worker_proposal`、正常路径/权限检查、`_apply_proposal`、`run_tests` 和最终提交；不能修复时返回具体的 `schema_repair_failed`，并在 `protocol_repairs.raw_provider_response.raw_text` 保留候选原文。没有删除边界条件，也没有直接放行未经验证的 actions。
- 定向结果：新增 4 个测试，使用上述真实响应；在临时工作区中 `src/consumer.py`、`tests/test_consumer.py`、`delivery.json` 被写入，`run_tests` 为 `SUCCEEDED`，修复字段为 `expected_outputs,confidence,needs_escalation,escalation_reason`，调用数 2（1 次收回的已付费响应 + 1 次本地夹具提交）。非法路径仍被 `target_scope` 拒绝；非法 action 返回 `schema_repair_failed` 并保留候选；`finish_reason=length` 的截断响应返回 `schema_repair_incomplete`，不会被应用。`tests/project_agent/test_worker_loop.py` 11 项通过。
- 范围限制：离线回放只写临时工作区，不写正式 store、不生成生产收据、不改变旧失败或费用；真实 `src/tool.py`、原始测试和旧 attempt 均未改写。

### D2：9 次上下文读取的实际内容与修复

- 实际读取（来自保存的 12 次规划调用）：决定 1 读取 contract.json、sample.jsonl、advisory evidence；决定 2 再次读取 contract.json、sample.jsonl，并读取 normalizer contract；决定 3 再次读取 sample.jsonl、contract.json、normalizer contract。9 次中 6 次是前序决定的重复（contract 3 次、sample 3 次、normalizer contract 2 次），2 次是必要输入，1 次是可选的 advisory；consumer 失败观察本身没有被 fetch，但其压缩后的 `status/error` 已在 `execution_results` 中传递。
- 根因：`public_context_view` 把即使很小的 `public_artifacts`、成功的 contract、advisory evidence、失败的 dependency result 和 task feedback 都移出 prompt，变成可付费 fetch 的目录；而每个决定都从新 prompt 开始，已读内容没有复用，于是相同小材料被反复读取。`max_context_expansions=3` 又是固定上限，没有和全局剩余调用、未完成义务挂钩。
- 修复位置：`cgkn/protocol/adaptive_context.py` 的 `public_context_view(..., inline_small=True, small_material_bytes=6000)`；小输入、小 contract、小 advisory、小失败结果和小 feedback 直接内联，只有大结果保留精确 sha256 的 fetch 条目；已在 `capability_catalog` 中的 contract 不再重复广告；输入哈希变化时 `prepare_context` 仍抛 `authorized input identity changed`，属于明确刷新。未新增批量读取协议或调度器；大材料继续走现有单 ref fetch。
- 预算修复位置：`cgkn/application/goal_driven.py` 计算 `remaining_calls`、`unfinished_requirements`、`execution_reserve = 1 + 3 × 未完成项数` 和 `context_expansion_limit = min(3, remaining - reserve)`，写入 `composer.max_context_expansions`，并在 `resource_scope` 暴露这些真实值及“小材料已内联、不要重复 fetch、保留执行/修复/验收额度”的 `context_policy`。
- 定向结果：新增 2 个 `test_goal_driven.py` 测试和 1 个 `test_public_context_completion.py` 测试；小输入在首轮直接内联、目录为空，`complete_with_context` 以单次决策调用返回；3 次剩余调用加 2 个未完成义务得到 reserve 7、扩张上限 0；小失败结果内联，只有大结果可 fetch。`tests/executor_authority_support.py` 只增加一个默认关闭的 `preserve_declared_effects` 选项，供 D1 测试保留 `local_process`，不改变其他调用。

### 定向复验与保留

- 最终定向 32 项通过：`test_worker_loop.py`（11）、`test_public_context_completion.py`（9）、`test_interface_autonomy.py`（7）、3 个既有 runtime/governance 场景、3 个新增 D2 场景（2 个内联/预算 + 1 个投影）；JUnit 为 `interface-small/d1d2-targeted-recheck.xml`。
- 本文件其余历史 `test_goal_driven.py` 测试仍有 13 项失败，根因是该夹具的 `Fake.complete` 同时调用 `perform_scoped_effect` 和 executor 的 `guard_effect`，在 `max_calls_per_leaf=2` 下累计调用 3 次触发 `BUDGET_SCOPE_REJECT`；这不是 D1/D2 引入的，也没有被当作本轮证据。未为此扩大修改范围。
- 保留：`src/tool.py`、原始测试、`normalized.local.json`、`empty.local.json`、旧 attempt、旧决策/上下文、16/16 账本和费用全部原样保留；没有新 run_id、没有改旧账本。

### D3 与真实续跑状态

- D3 仍是需要 Worker 修复的业务错误：公开预期 `{"records":4,"total_ms":3250,"unit":"ms"}`；保存的 consumer 实际输出 `{"records":4,"total_ms":3250,"mean_ms":812.5,"unit":"ms"}`。Host 没有删除 `mean_ms`，也没有放宽检查器；外层 OpenCode 没有直接改消费者产品代码。
- **真实续跑未执行**：本指令没有追加付费额度，16/16 调用上限和 20 分钟窗口不可自动重置；没有新 Provider 调用、没有新收据、没有发布、没有 ACFV。待有效追加授权后再沿同一任务或明确后继任务执行：consumer 业务修复与交付 → 真实组件注册和 Port 消费 → CSV 正式扩展。本轮 D1/D2 代码仅为离线后继，不得把旧真实运行称为 PASS。
- **恢复身份限制**：Host 源已因 D1/D2 修复而变化，旧 run 的冻结 `goal-config.json` 仍绑定旧源哈希，不能无条件 `resume`；后续真实续跑必须是明确授权且绑定当前源码的**后继任务/新配置**，并使用独立的新账本；旧 run、旧账本、旧失败和费用继续作为历史证据保留。

---

# 接口巩固与边界内自主权：代码已接线，12 项离线机制通过

2026-11-12：使用当前 Core/Host 开发工作树完成修改，保留既有 Planner、Tree、DAGRunner、状态、预算及验收权威。没有全仓回归、长测、Provider 调用、commit 或 push。以下是本轮范围；后文保留历史记录，不混算旧 RunLens 成果。

| 项目 | 本轮结果与限制 |
| --- | --- |
| 接口 | 默认 GoalComposer 的实际提示、公开 schema、编译器共用 executor_interfaces，Host 生成内部字段。Port 连接检查结构和语义；显式操作者适配规则可转换毫秒/秒，不能猜单位。声明匹配不授予实现 PASS。计划中的实现与输出允许先绑定，执行前核对真实依赖、收据、产物身份及契约。 |
| 自主权 | Worker 在组件目录内可新增实现、空内部文件及自测，读取失败结果后局部修复再提交；旧授权输入与新证据可共存。委派、请求、自测分开计时并受剩余额度约束。工作区外、独立检查器和权限变更仍被控制，不开放任意 shell，不宣称 OS 沙箱。 |
| 生长 | implementation_node → 原有 Worker/DAG → 收据绑定 Block/Variant 候选包 → local.component@1 → 真实 Port 消费与显式适配。既有归档/恢复保留历史和必需目标。组件导入和显式未认证 Skill 导入均保持候选资格；正式 Skill 复用仍需当前目标项目收据。 |
| 离线小测 | 12 个唯一场景最新结果全部 PASS。一组合并首跑 7 通过、5 失败；修复实际协议准备、不可变收据路径、包 JSON 表示及适配规则比较等根因和夹具问题后，仅复验受影响项。保留所有初始失败及后续 JUnit，不重复整批。fake Provider 只证明接线；Worker 自测实际经历失败、修改与通过。 |
| 真实小测 | BLOCKED_AUTHORIZATION。没有覆盖本轮的有效授权、冻结费率和具体获准模型路由；正常 preflight 返回阻断且 provider_contacted=false。已备 JSONL/CSV 样本、公开预期、外置检查器及两阶段配置，未写产品实现、未创建业务树、未正式应用 CSV 增量、未生成产品成果。真实自主新增能力及纠偏 NOT_EXERCISED。 |

代码位置：Core `src/veriarbor/{compatibility,adapter,component_package,skills}.py`；Host `cgkn/agent/composer.py`、`application/goal_driven.py`、`executors/llm.py`、`protocol/exchange.py`、`adapters/veriarbor/{component_package,skill_authority}.py` 和 `scripts/run_goal_driven.py`。必要入口说明同步于 Host `docs/artifact-driven-migration.md`，委托清单同步于 `reports/generic-boundary-closure-v1/BOUNDARIES.md`。

验证源码：`F:/CGKN-LeanLoop-V1-20261101/tests/application/test_interface_autonomy.py`；复用 graph_commit 的归档/恢复与目标保护、core_governance_completion 的目标项目 Skill 收据、public_context_completion 的 Planner/Worker 上下文与最终响应场景。机器汇总 `interface-small/results.json`；原始 `offline.xml` 与 `recheck-1.xml` 至 `recheck-5.xml` 保留失败和最终通过依据。只覆盖所选机制，不代表全仓或全部历史迁移完成验证。

正常入口配置：`D:/VeriArbor/reports/runlens-refactor-20261112/interface-small/witness/phase1.json`。执行入口为 `D:/anaconda/python.exe F:/CGKN-LeanLoop-V1-20261101/scripts/run_goal_driven.py preflight --config <phase1.json>`；本轮只运行此无 Provider 的启动前检查，结果保存在 `witness/preflight.json`。授权及可靠费率补齐后才可经同一入口 start；首次交付后，`phase2-extension.json` 需填写实际父配置身份再走 extend，共享原任务账本和额度，不能直接新建项目重跑。

外置检查器和公开预期已固定身份，作者为外层 Codex，不是独立盲测。准备上限为 16 次尝试、3 元、输入 20 万/输出 3 万 token、首次派发后 20 分钟，这些不是授权。实际 Provider 尝试 0，费用未知不记零，外层 Codex 成本未计量。旧 RunLens 未因此完成。

本轮必要文件修改前副本在 `interface-small/before/`。支持范围仍是显式 Python JSON stdio 组件；专用证据策略和远程副作用需要相应明确适配。没有新增调度器、Registry、账本或归档权威。

---

以下是此前各轮记录；其中“本轮”指对应历史会话：

# 本轮代码收口：三项接线已完成，运行验证未执行

遵照最新指令，本轮只读取和修改源码、测试源码及文档：**未运行测试（包括 collect）、未启动项目、未调用 Provider，未执行项目 import、编译、构建、lint 或资格脚本。** 完成的是下面三项代码接线，不是经运行证明的产品或自增长闭环。旧实验和账本原样保留。

| 本轮要求 | 已完成的源码修改 | 运行证据 |
| --- | --- | --- |
| 历史测试迁移 | 删除对已退役生成循环的调用；有效行为转到现有 LLMExecutor、DAGRunner、独立文件检查与恢复接口。保留端点、DOM、语法的业务断言；旧循环专有路由、自动扩额和固定模板规则逐项标为退役。同步显式候选提交、反馈与调用计数夹具，没有批量 skip。映射记录在 `code-completion/retired-test-inventory.json`。 | NOT_RUN |
| 迁移组件直接调用 | Core 内容包新增显式 `python-json-stdio@1` 调用协议；Host 注册 `local.component@1`，支持输入值及依赖输出 Port 绑定。核对完整依赖、实现内容、边界与适用条件，经现有 CommandExecutor、效果许可、候选工作区、独立检查、CAS 发布及收据链执行。输入输出校验 Port schema，未知结果不自动重试。 | NOT_RUN |
| 跨项目 Skill 再资格化 | 正常 CLI 接入 register/export/import/requalify-skill；来源只按操作者声明的 `skill_sources` 查找。导入清除源项目资格和指标，进入 NEEDS_REVALIDATION；`skill_trial` 在目标项目走共同编译、TreeEdit/admission 和执行链。Permit 绑定清单策略哈希；目标项目真实收据通过既有 promotion_check 后才可 VERIFIED 和正常消费。 | NOT_RUN |

同时保留此前本轮的 component_roots、候选内 run_tests 反馈、显式空 actions 提交、源码身份绑定与发布隔离。数字 Worker 协议补上本地测试与提交操作；精确文件写入保留独立并行，开放组件目录的写入使用共享根互斥。新增组件调用与跨项目 Skill 回归用例源码，未执行。

主要位置：Core `src/veriarbor/component_package.py`、`skills.py`；Host `cgkn/adapters/veriarbor/component_package.py`、`skill_authority.py`、`capability_adapter.py`、`application/goal_driven.py`、`runtime/node_authority.py`、`agent/project_loop.py`、`protocol/`、`scripts/run_goal_driven.py`。调用契约见 Host `docs/artifact-driven-migration.md` 的 Portable components and Skill transfer 节；新正式入口的委托关系已登记在 `reports/generic-boundary-closure-v1/BOUNDARIES.md`。

适用边界：v1 包仍可作源码输入；直接执行必须由 v2 包显式声明 Python JSON 标准输入/输出协议。不支持的语言、远程副作用或带专用证据策略的 Port 必须提供明确适配器，不能隐式降级。子进程沿用既有 Host 效果边界，不宣称操作系统级沙箱。独立业务验收仍是最终权威，进程成功、schema 合法和本地自测均不能替代它。

Skill 的目标项目再资格化仍要求至少两个不同目标 run 的有效执行/验收收据、相同策略身份、当前依赖/检查器及适用环境；源项目 PASS 不能代替。策略或依赖契约变化需明确新版本再试用。上述条件已由代码接线约束，真实验证尚未进行；本轮不生成成功运行、验收证书或成本记录。

本次编辑前字节保存在 `code-only/closure-before/`；上一轮副本在 `code-only/before/`。未 commit、push，也未覆盖既有 dirty changes 或历史 run/账本。下面的 PASS 和测试次数只属于各自历史源码，不适用于当前工作树。

---

以下为此前报告，涉及 PASS、测试次数和真实调用的叙述只适用于各自历史源码：

# VeriArbor / RunLens 当前交付

本次继续直接修改 Host 生产主链。用户要求缩短测试后，仅运行三个 schema 短检查（0.75 秒）和一个受影响的离线项目路径（3.62 秒），均通过。没有再启动长回归或新付费调用。代码修改不能等同于真实自增长已完成。

| 原始验收项 | 结果 | 范围 |
|---|---|---|
| 重构和旧路径清理 | PASS | 本轮生产主链：默认入口委托 ProjectSession，被替代的生成/修复所有者已删除；不代表全部历史业务代码清空 |
| 核心工程机制 | PASS | 有限离线及受影响路径；不代表整个最终工作树或真实产品已资格化 |
| 真实 RunLens / CSV | BLOCKED | 已真实规划及调用 Worker，未发布产品；原时间额度已到 |
| 产品纠偏 | NOT_EXERCISED | 框架纠偏不计为产品纠偏 |
| 实际 Block 替换、归档、恢复 | NOT_EXERCISED | 既有离线机制证据保留 |
| 第二项目迁移及 Skill 消费 | NOT_EXERCISED | 无真实组件或消费记录 |

代码修改：

- 规划许可覆盖既有上下文读取次数加最终决策，Worker 原有限额独立保持；所有请求仍共用原账本。
- 最后一次上下文请求只接受业务响应。引用 schema 从同一个 resolver 生成，绑定操作与引用类型；本轮已读引用不再可选。错误反馈说明实际操作与允许操作。
- Planner 的修复 schema 只开放 goal、read_paths、verified_artifact_change_reason，禁止写入 Host 的 leaf_contract、input_paths 或更改写入权限。Worker 写入/补丁 schema 由获准 target_scope 生成，不再向模型展示任意写入路径；执行前检查继续保留。
- 发送前拒绝不再误报为无效响应；预算错误包含实际累计值、上限和合法后续动作。
- 连续中断恢复跳过所有已占用上下文编号，保持旧字节不变。已知本地协议拒绝关闭规划许可；旧活跃许可须核对精确上下文、Host 拒绝事件及全部请求已结算后才能关闭。存在 UNKNOWN 仍阻止恢复。
- 源码修订可保留失败但尚未形成产品的运行；拒绝成功历史、UNKNOWN 或现有产品字节，不重置目标、费用、原截止时间，不给予旧证据新 PASS。
- 删除会话侧旧生成重试/验证循环、模拟启动、旧队列入口、MVP 直接执行基线，以及十个旧整项目/组件生成和修复调度函数；删除旧组件流水线 smoke 脚本。正常 CLI、动态入口继续走原有 ProjectSession，保留仍被消费者使用的验收、媒体和打包辅助函数。被替代的生成实现移除约 6,000 行，不另建状态权威。
- 迁移对应路由检查及相关当前测试。旧生成 API 的历史测试引用另列在 code-completion/retired-test-inventory.json，未重跑全部历史项目，也未宣称那些旧测试全绿。

验证：合并相关回归 194 PASS；后续受影响批次 58 PASS、3 FAIL，三个旧夹具问题修复后精确复验 3 PASS。其余对应修复回归见 results.json，均保留原始日志及失败 XML，不累加重叠批次制造测试数量。最终 schema/Worker 路径修改按最新用户指令仅做短检查；较早整体工作树回执不能冒充最终源码的新鲜回执。架构/路由/产品方向检查的各自适用源码和日志保留在 code-completion/。

真实运行：同一 runlens-lite / runlens-20261112，累计 18 次实际提交，18 次确认，无 UNKNOWN，另有一次账本中的发送前取消。输入 118,250、输出 7,261 token；估算 0.294588 元 / 20 元，按冻结的每百万输入 2 元、输出 8 元计算，非供应商账单。实际模型为 qwen3.7-flash 和 deepseek-flash；外层 Codex 成本未知，不记零。

Agent 曾创建核心解析器节点，Worker 提出了 runlens.py 和未授权 test_runlens.py 两个写入，执行边界在发布前拒绝。后续 Planner 因重复上下文读取和接口修改提议触发 ADMISSION_NO_PROGRESS。相关 schema 已继续修正，但最后的源码未再次真实验收；原始 60 分钟额度已经结束。没有清空失败、重开运行或代写 RunLens 成品。

交付位置：Host F:/CGKN-LeanLoop-V1-20261101；代码差异 code-completion/changes.patch，最终源码哈希 source-final.json，必要备份 before/，机器结果 results.json。实际 RunLens、CSV 产品、可迁移 Block 包及 Skill 消费结果仍不存在。原工作区 dirty changes 保留，未 commit/push。

正常入口及状态命令：

```powershell
$env:PYTHONPATH='D:/VeriArbor/src;F:/CGKN-LeanLoop-V1-20261101'
$env:CGKN_APPLICATION_PROFILE='D:/VeriArbor/reports/runlens-refactor-20261112/live/application.json'
$env:CGKN_PROVIDER_LAB_CONFIG='D:/VeriArbor/reports/runlens-refactor-20261112/live/providers.json'
D:/anaconda/python.exe F:/CGKN-LeanLoop-V1-20261101/scripts/run_goal_driven.py status --config D:/VeriArbor/reports/runlens-refactor-20261112/live/runlens.json
```

正常新任务使用 start；本任务已启动过，不能重开来绕过截止时间。resume 是同一运行恢复入口，但当前原窗口已到时且最后源码尚未绑定到 live 修订，不能直接重试。原始证据 live/resume-4.log、resume-5.log、campaign-budget.json 保留。不得称为本轮完整自增长闭环。
