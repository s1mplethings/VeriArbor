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
