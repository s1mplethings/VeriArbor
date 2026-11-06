"""Import the user's explicit non-executable composition via original TreeEdit.

No business config/receipt is replaced; executable DAG must stay byte-identical.
"""
from pathlib import Path
import hashlib,json,uuid
from cgkn.state import FileRunStore
from cgkn.state.models import EventRecord
from cgkn.orchestration.capability_tree import CapabilityTree
from cgkn.orchestration.tree_edits import TreeEdit,apply_tree_edits
from cgkn.orchestration.execution_dag import compile_tree

R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
store=FileRunStore(R/'state');pid='iter132-promotion-studio';rid='promotion-05';s=store.run_dir(pid,rid)
prompt=Path('C:/Users/sunom/Downloads/CGKN_Veriarbor_M12_block_closure_final_delivery_prompt.txt')
provenance={'source':'explicit-user-composition','instruction_path':str(prompt),'instruction_sha256':hashlib.sha256(prompt.read_bytes()).hexdigest(),
    'authority':'User supplied B01-B11 decomposition; original Agent retains all implementation decisions'}
with store.exclusive_file(s/'project_session.lock'):
    state=store.load_run(pid,rid);assert not any(n.status=='RUNNING' for n in state.nodes.values())
    original=json.loads((s/'capability_tree.json').read_text(encoding='utf8'));tree=CapabilityTree.from_dict(original)
    checkpoint=json.loads((s/'agent_checkpoint.json').read_text(encoding='utf8'))
    assert checkpoint['tree']==original,'reconcile checkpoint before importing composition'
    store.immutable_json(s/'recovery/m12-user-composition-before.json',{'tree':original,'checkpoint':checkpoint,'provenance':provenance})
    graph=json.loads((M/'M12_BLOCK_GRAPH.json').read_text(encoding='utf8'))
    edits=[TreeEdit('user-m12-rollup','add_node','m12-final-rollup',{'config':{'name':'M12 Final Product','rollup_only':True,'acceptance_goal_id':'accept-c094cd66fb2ff494ecdf','required':True}},provenance)]
    for block in graph['blocks']:
        node='m12-'+block['block_id'].lower()
        edits.append(TreeEdit('user-'+node,'add_node',node,{'parent_id':'m12-final-rollup','config':{
            'name':block['name'],'block_id':block['block_id'],'required':True,'rollup_only':True,
            'ordered_predecessor_blocks':block['depends_on'],'acceptance_goal_id':'block-acceptance-'+block['block_id']}},provenance))
        block['canonical_node']=node
    # Preserve the executed writer identity, only assign its structural owner.
    # The next Agent decision must narrow its leaf before it can execute.
    edits.append(TreeEdit('user-b01-existing-writer','move_node','sem-node-0143',{'parent_id':'m12-b01'},provenance))
    proposed=apply_tree_edits(tree,tuple(edits),known_capabilities={n.capability_ref for n in tree.nodes if n.executable})
    assert compile_tree(proposed).as_dict()==compile_tree(tree).as_dict()==state.execution_dag
    checkpoint['tree']=proposed.as_dict()
    # Preserve all previous strategies in the immutable snapshot and original
    # attempt receipts. Only the active continuation guidance is superseded.
    checkpoint['failure_details']['continuation_requirements']={'user_instruction':provenance,
        'current_failure_context':json.loads((M/'M12_CURRENT_FAILURE_CONTEXT.json').read_text(encoding='utf8')),
        'historical_strategy_notice':'Prior full-file/module-mapping strategies are historical invalidated proposals, not active repair instructions.'}
    store.save_definition(pid,rid,'capability_tree.json',proposed.as_dict())
    store.atomic_json(s/'agent_checkpoint.json',checkpoint)
    store.append_event(EventRecord(str(uuid.uuid4()),pid,rid,'USER_COMPOSITION_IMPORTED',data={**provenance,
        'nodes_added':['m12-final-rollup']+['m12-'+b['block_id'].lower() for b in graph['blocks']],
        'executable_dag_changed':False,'source_changed':False,'acceptance_changed':False}))
    graph['authority']='Projection of original FileRunStore CapabilityTree; no second scheduler'
    graph['parent']['registration']='REGISTERED_NON_EXECUTABLE';graph['parent']['canonical_node']='m12-final-rollup'
    # This is a derived report, deliberately outside the canonical state root.
    (M/'M12_BLOCK_GRAPH.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':'USER_COMPOSITION_REGISTERED','executable_dag_unchanged':True,'business_writes':0}))
