"""Align user-defined structural Block ownership without changing executable DAG."""
from pathlib import Path
import json,sys,uuid
from cgkn.state import FileRunStore,EventRecord
from cgkn.orchestration.capability_tree import CapabilityTree
from cgkn.orchestration.tree_edits import TreeEdit,apply_tree_edits
from cgkn.orchestration.execution_dag import compile_tree
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
block=sys.argv[1];assert block in ['B'+str(i).zfill(2) for i in range(1,11)]
store=FileRunStore(R/'state');pid='iter132-promotion-studio';rid='promotion-05';root=store.run_dir(pid,rid)
def read(p):return json.loads(p.read_text(encoding='utf8'))
with store.exclusive_file(root/'project_session.lock'):
    state=store.load_run(pid,rid);assert not any(n.status=='RUNNING' for n in state.nodes.values())
    original=read(root/'capability_tree.json');tree=CapabilityTree.from_dict(original);checkpoint=read(root/'agent_checkpoint.json')
    assert checkpoint['tree']==original
    target='m12-'+block.lower();node=tree.by_id['sem-node-0143'];assert not tree.by_id[target].executable
    if node.parent_id==target:print('Ownership already aligned');sys.exit(0)
    proof={'source':'explicit-user-M12-B01-B11-composition','block_id':block,'purpose':'Structural owner only; Agent-authored leaf contract, writes, execution edges and receipts unchanged'}
    edit=TreeEdit('block-owner-'+uuid.uuid4().hex,'move_node',node.id,{'parent_id':target},proof)
    proposed=apply_tree_edits(tree,(edit,),known_capabilities={n.capability_ref for n in tree.nodes if n.executable})
    assert compile_tree(proposed).as_dict()==compile_tree(tree).as_dict()==state.execution_dag
    store.immutable_json(root/'recovery'/('block-owner-'+block+'-'+uuid.uuid4().hex+'.json'),{'tree':original,'checkpoint':checkpoint,'edit_provenance':proof})
    checkpoint['tree']=proposed.as_dict();store.save_definition(pid,rid,'capability_tree.json',proposed.as_dict());store.atomic_json(root/'agent_checkpoint.json',checkpoint)
    store.append_event(EventRecord(str(uuid.uuid4()),pid,rid,'BLOCK_WRITER_OWNER_ALIGNED',data={**proof,'node_id':node.id,'from_parent':node.parent_id,'to_parent':target,'executable_dag_changed':False}))
    graph=read(M/'M12_BLOCK_GRAPH.json');graph['current_writer']={'node_id':node.id,'block_id':block,'canonical_parent':target}
    (M/'M12_BLOCK_GRAPH.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'writer':node.id,'parent':target,'executable_dag_unchanged':True}))
