"""Read-only evidence export requested by user; no product execution or publication."""
from pathlib import Path
from collections import Counter
import csv, datetime, hashlib, io, json, subprocess, zipfile

V=Path('D:/VeriArbor'); H=Path('F:/CGKN-LeanLoop-V1-20261101')
M=H/'migration/veriarbor'; R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
S=R/'state/iter132-promotion-studio/promotion-05'
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
O=V/'reports'/('工作报告与证据包_'+stamp.strftime('%Y%m%d_%H%M%S')); O.mkdir(parents=True,exist_ok=False)
def read(p): return json.loads(p.read_text(encoding='utf8'))
def put(name,v): (O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def md(name,s): (O/name).write_text(s,encoding='utf8')
def table(name,rows):
    if not rows:return
    with (O/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

state=read(S/'run_state.json'); assert not any(x['status']=='RUNNING' for x in state['nodes'].values())
assert (R/'continuations/veriarbor-85/STOP_BEFORE_NEXT_CALL').exists()
ledger=read(Path('F:/CGKN-ITER-076/global-provider-budget.json'))
baseline=read(R/'continuations/veriarbor-01/accounting-before.json'); calls=ledger['calls'][len(baseline['calls']):]
summary={'snapshot_time':stamp.isoformat(),'product_status':'PRODUCT_NOT_READY','library_status':'VERIARBOR_BLOCK_CORE_PARTIAL',
 'provider_dispatch':'HELD_BY_USER_REPORT_ONLY_REQUEST','running_nodes':[],
 'baseline_calls':len(baseline['calls']),'current_calls':len(ledger['calls']),'new_calls':len(calls),
 'new_call_statuses':dict(Counter(x['status'] for x in calls)),
 'new_models':dict(Counter(x.get('actual_model') or x.get('model') for x in calls)),
 'numeric_tokens_only':sum(x['total_tokens'] for x in calls if isinstance(x.get('total_tokens'),(int,float))),
 'unknown_token_rows':sum(not isinstance(x.get('total_tokens'),(int,float)) for x in calls),
 'cost_status':'ESTIMATES_NOT_VENDOR_INVOICE','host_business_patches':0,
 'main_sha256':hashlib.sha256((R/'candidate/main.py').read_bytes()).hexdigest()}
put('当前状态快照.json',summary)
md('完整工作与卡点报告.md',(V/'docs/WORK_STATUS_AND_BLOCKERS_2026-11-04.md').read_text(encoding='utf8')+
 '\n\n## 本证据包的最终截点\n\n'+stamp.isoformat()+'。用户明确只要工作报告，已停止下一次 Provider 派发；没有运行中的业务节点。continuation 85 在派发前以 controller_hold_before_dispatch 收尾，不产生新的 UNKNOWN。产品尚未修复完成。最新账目以本包 当前状态快照.json 与 调用明细.csv 为准，前文 15:41 数字为历史截点。\n')

continuations=[]
for folder in sorted((R/'continuations').glob('veriarbor-*'),key=lambda p:int(p.name.split('-')[-1])):
    row={'continuation':folder.name,'started':'','status':'NO_RESULT','reason':'','agent_calls_cumulative':'','worker_calls_cumulative':''}
    p=folder/'started.json'
    if p.exists():
        a=read(p);row['started']=str(a.get('started_at',a.get('created_at','')))
    p=folder/'result.json'
    if p.exists():
        a=read(p);r=a.get('result',{});row.update(status=a.get('status',''),reason=r.get('escalation_reason',''),agent_calls_cumulative=r.get('agent_calls',''),worker_calls_cumulative=r.get('worker_calls',''))
    else:
        for name in ['execution-error.json','local-launch-error.json']:
            p=folder/name
            if p.exists():row['status']=name;row['reason']=json.dumps(read(p),ensure_ascii=False)[:2500]
    continuations.append(row)
table('每轮执行明细.csv',continuations)
attempts=[]
for p in sorted((S/'attempts').glob('*/*.json')):
    a=read(p);e=a.get('error') or {};metadata=a.get('metadata') or {};progress=metadata.get('implementation_progress') or {}
    attempts.append({'node':a.get('node_id'),'attempt':a.get('attempt_id'),'status':a.get('status'),'started':a.get('started_at'),'ended':a.get('ended_at'),
      'executor':a.get('executor_ref'),'error_code':e.get('code'),'error_message':e.get('message'),'deliverable_verdict':metadata.get('deliverable_verdict'),
      'progress_verdict':progress.get('verdict'),'evidence':str(p.relative_to(R))})
table('节点尝试与失败明细.csv',attempts)
keys=['call_id','request_identity','model','actual_model','status','request_started_at','finished_at','input_tokens','output_tokens','total_tokens','estimated_cost','purpose','run_id','job_id','attempt_id','terminal_commit_state','authoritative_response_ref']
table('调用明细.csv',[{k:x.get(k) for k in keys} for x in calls])
switches=[json.loads(l) for l in (M/'AUTHORITY_SWITCH_RECEIPTS.jsonl').read_text(encoding='utf8').splitlines() if l.strip()]
table('宿主变更45条明细.csv',[{'序号':i,**{k:r.get(k) for k in ['file','authority','before_sha256','after_sha256','rollback','status']}} for i,r in enumerate(switches,1)])
checks=[]
for p in sorted((V/'governance/checks').glob('*/receipt.json')):
    a=read(p);checks.append({'check':p.parent.name,'receipt':str(p),'details':json.dumps(a,ensure_ascii=False)})
table('全部记录内测试明细.csv',checks)

answers=[
('Block/Port 核心','最小核心已实现；完整 V1 门禁未完成。'),
('复杂全局算法依赖','默认调度已脱离实验 Pareto/Bandit；未宣称所有历史代码已删除。'),
('依赖方向','保持 CGKN → VeriArbor。'),('第二 authority','未新增；原执行、状态、验收、交付体系保留。'),
('正式 Block 数量','现有 BLOCK_MAP 为 goal 边界投影，尚不能当作全部正式执行 Block 数；完整映射未收口。'),
('正式 Port 数量','PORT_MAP 同样未收口，不提供误导性总数。'),
('IDENTICAL 数量','有实际 M6 替换及下游复用见证；全部端口分类总数未完成统计。'),
('COMPATIBLE 数量','有策略/合成测试，真实产品变更见证未完成，不能报实际总数。'),
('ADAPTABLE 数量','rename/default 策略已实现，真实产品见证未完成。'),
('BREAKING 数量','一跳/逐步扩大策略已实现，真实产品见证未完成。'),
('Adapter 数量','完整自动/手工 Adapter 台账尚未收口；见 ADAPTER_MAP，不将合成测试计入生产实例。'),
('Adapter chain','V1 有界显式适配；未证明全部生产调用不存在历史链，需最终映射审计。'),
('无 consumer 旧 Adapter','最终全量退役清单与 consumer 数量审计尚未完成。'),
('内部实现局部验证','有真实 M6 替换复用 M7–M10 证据；旧 DAG 执行闭包仍有保守范围。'),
('接口变化优先 Adapter','策略支持；还缺真实接口改变场景的完整见证。'),
('Breaking 逐跳扩散','策略与测试存在；不得当作真实产品全场景通过。'),
('VerificationKey 阻止数','机制和本次重复 M12 测量阻止有记录；全历史去重计数尚未聚合，原协议与事件全量随包。'),
('Provider 去重阻止数','机制已接入；schema/admission/local hold 与真正 novelty 拦截不可混计，尚无完整可信总数。'),
('GUI 单一 writer','当前 main.py 原节点 143；无并行 GUI writer；宿主业务补丁 0。'),
('M11 三缺陷','模块定位、发布前真实媒体有效性和 GUI 媒体预览已由原链修复并验收；M12 重写回退另计。'),
('M11 verdict','VERIFIED。'),('M12 verdict','FAILED；155a1 对当前源码的创建项目可见性检查失败。'),
('DOGFOOD 实际启动','历史 M7 DOGFOOD 有启动证据；它不是当前 M12 完整产品。当前版本尚未交付。'),
('最终 GoalAcceptance','未完成，M12 未通过。'),('Final delivery','无当前有效最终交付；只允许原 local_packager / delivery gate 路径。'),
('Max 次数','本轮账本 0。'),('Pro 次数','本轮账本 0。'),
('UNKNOWN 保留','保留本轮 11 个 UNKNOWN 及历史记录；处置证据随包，不盲重放。'),
('Corpus 两次重建','本轮最终归档与两次只读一致重建尚未完成。'),
('最终产品状态','PRODUCT_NOT_READY；库为 PARTIAL；本包是工作/证据导出，不是产品交付包。')]
md('原任务30问逐项答复.md','# 原任务第44节：30问逐项答复\n\n'+ '\n\n'.join(f'{i}. **{q}**：{a}' for i,(q,a) in enumerate(answers,1)))
md('待办与解除卡点标准.md','''# 待办与解除卡点标准

| 顺序 | 工作 | 完成证据 |
| --- | --- | --- |
| 1 | 原 Agent 修复证据引用，清除旧策略污染 | 准入成功，真实执行节点启动；不能仅凭自然语言提案 |
| 2 | 项目 bootstrap 实际修改 | 当前文件哈希改变，真实创建后名称可见，刷新后可见，无初始化400 |
| 3 | 浏览器上传与预览 | PNG/视频实际字节、持久化、解码、无效输入拒绝、临时文件清理 |
| 4 | 完整M12功能闭环 | 声明/证据、编辑/变体/比较、审批/发布/排程/回执/分析/UNKNOWN对账 |
| 5 | 测试和文档债务 | 原测试owner修改、真实夹具验证、明确启动与操作命令 |
| 6 | 当前产品交付 | 实际DOGFOOD、完整GoalAcceptance、原provenance/local_packager/delivery gate |
| 7 | 库完整门禁 | 真实四类替换、缺失适配能力与完整映射；否则如实PARTIAL |
| 8 | 归档与账目 | 全调用关联、UNKNOWN处置、Corpus两次一致重建、两个最终报告 |

当前按用户要求暂停产品推进，只交付报告和证据。没有承诺完成时间；上述各项不能用 Provider SUCCEEDED 代替。
''')

files={};excluded=[]
def add(root,prefix):
    if not root.exists():return
    seq=root.rglob('*') if root.is_dir() else [root]
    for p in seq:
        if not p.is_file():continue
        rel=p.relative_to(root) if root.is_dir() else Path(p.name)
        parts=set(rel.parts)
        if parts & {'.git','.venv','__pycache__','.pytest_cache','node_modules','reports'} or p.suffix in {'.pyc','.lock'}:continue
        if p.name.lower() in {'session.json','credentials.json','.env','.env.local'} or p.name.lower().endswith(('.pem','.key')):
            excluded.append({'path':str(p),'reason':'credential/config exclusion'});continue
        files[prefix+'/'+rel.as_posix()]=p
add(V,'01_VeriArbor');add(M,'02_迁移全部证据');add(R,'03_Promotion原始运行')
for name in ['cgkn','tests','scripts','governance','project_management','skills/manage-pmp-agile-quality']:
    add(H/name,'04_宿主当前源码/'+name)
for name in ['AGENTS.md','PRODUCT_GOAL.md','MVP_SCOPE.md','pyproject.toml','README.md']:
    add(H/name,'04_宿主当前源码')
add(Path('F:/CGKN-ITER-076/global-provider-budget.json'),'05_账本')
for p in [Path('C:/Users/sunom/Downloads/VeriArbor_run_from_new_VB_folder_direct_migration_v2_prompt.txt'),Path('C:/Users/sunom/.codex/attachments/3623a09d-f8d9-41c6-972b-7afd9adaed0b/已粘贴的文本.txt')]:add(p,'00_任务原文')
for name in ['CHANGE_SCOPE.md']:
    add(R.parents[1]/name,'00_任务原文')
for root,label in [(V,'VeriArbor'),(H,'CGKN')]:
    for args,suffix in [(['status','--short'],'status.txt'),(['diff','--stat'],'diff-stat.txt'),(['diff','--binary'],'tracked-changes.patch')]:
        r=subprocess.run(['git','-c','safe.directory='+str(root),'-C',str(root),*args],capture_output=True)
        (O/(label+'-'+suffix)).write_bytes(r.stdout+b'\n'+r.stderr)
put('排除项与范围.json',{'excluded':excluded,'excluded_classes':['虚拟环境','.git数据库','缓存','lock文件','外部网关session与凭据'],
 'scope':'VeriArbor工作树、全部迁移证据、完整Promotion run-05、宿主cgkn/tests/scripts/governance与方法文件、原始任务、原账本。不是整个磁盘或其他项目的备份。',
 'security':'未复制环境变量或外部Provider session。原请求与响应包含项目源码/业务测试数据，请按本地项目资料保管。'})
md('先读我.md',f'''# 工作报告与完整证据包

快照时间：{stamp.isoformat()}。产品未完成；本包不代表最终交付。

建议阅读顺序：

1. `完整工作与卡点报告.md`：完成内容、原因、回退、责任、阻塞及剩余范围。
2. `原任务30问逐项答复.md`：逐项回答原任务要求，未知与未完成明确标记。
3. `待办与解除卡点标准.md`：恢复工作后的具体顺序及通过标准。
4. `每轮执行明细.csv`、`节点尝试与失败明细.csv`、`宿主变更45条明细.csv`、`全部记录内测试明细.csv`、`调用明细.csv`：可筛选明细。
5. `03_Promotion原始运行`：完整原始运行证据，包括Provider请求/响应、attempts、检查、候选版本、恢复和发布意图；所有历史FAIL保留。
6. `02_迁移全部证据`：诊断、局部替换、回滚、检查资格及历史记录。
7. `01_VeriArbor`与`04_宿主当前源码`：代码、测试、工具、文档及版本差异。

注意：旧 FINAL_REPORT 与部分映射是历史快照，不能代表当前状态；当前以顶层状态快照、原验收和本报告为准。CSV 中 Provider SUCCEEDED 不表示业务验收通过。估计成本不是供应商发票。

包内文件清单提供原路径、归档路径、大小、SHA-256。打包后会逐文件读取ZIP校验CRC。排除项单独列出，没有把缺失项目写成完成。
''')
for p in O.iterdir():
    if p.is_file():files['报告与索引/'+p.name]=p
archive=O.with_suffix('.zip');manifest=[]
print(json.dumps({'phase':'packing','files':len(files),'raw_bytes':sum(p.stat().st_size for p in files.values()),'archive':str(archive)},ensure_ascii=False),flush=True)
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
    for i,(name,p) in enumerate(sorted(files.items()),1):
        before=p.stat();digest=hashlib.sha256()
        with p.open('rb') as src,z.open(name,'w',force_zip64=True) as dest:
            while data:=src.read(1024*1024):digest.update(data);dest.write(data)
        after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('Source changed during export: '+str(p))
        manifest.append({'archive_path':name,'original_path':str(p),'bytes':before.st_size,'sha256':digest.hexdigest()})
        if i%2500==0:print(json.dumps({'phase':'packing','done':i,'total':len(files)}),flush=True)
    z.writestr('报告与索引/文件清单_SHA256.json',json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'phase':'verifying_zip_crc','archive_bytes':archive.stat().st_size}),flush=True)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.infolist())==len(manifest)+1
h=hashlib.sha256()
with archive.open('rb') as f:
    while b:=f.read(1024*1024):h.update(b)
receipt={'status':'REPORT_BUNDLE_VERIFIED','snapshot_time':stamp.isoformat(),'archive':str(archive),'archive_bytes':archive.stat().st_size,
 'archive_sha256':h.hexdigest(),'files':len(manifest)+1,'crc_all_files':'PASS','source_stability':'PASS','product_status':'PRODUCT_NOT_READY'}
put('打包校验收据.json',receipt)
archive.with_suffix('.sha256.txt').write_text(h.hexdigest()+'  '+archive.name+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False),flush=True)
