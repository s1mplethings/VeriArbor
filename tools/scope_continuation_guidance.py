from migrate_next import edit

def change(source):
    needle="    reusable_certificates=certificates(goal_state)"
    assert source.count(needle)==1
    source=source.replace(needle,needle+"\n    from cgkn.adapters.veriarbor.guidance_adapter import project_continuation",1)
    needle="'continuation_requirements':public_requirements(source.get('failure_details',{}).get('continuation_requirements',{})),"
    assert source.count(needle)==1
    return source.replace(needle,"'continuation_requirements':public_requirements(project_continuation(source.get('failure_details',{}).get('continuation_requirements',{}), goal_state)),",1)

edit('cgkn/protocol/context_pack.py',change,'Expire explicitly artifact/evidence-bound operational guidance after state changes; preserve raw history, general user requirements and canonical planner authority')
