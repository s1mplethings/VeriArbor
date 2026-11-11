import pytest
from veriarbor.governance import LegacyPolicy, legacy_scope


@pytest.fixture(autouse=True)
def explicit_historical_skill_policy(request):
    if request.path.name!='test_capability_skills.py':
        yield
        return
    events=[]
    with legacy_scope(LegacyPolicy(True,('unit.test_capability_skills',)),
            caller='unit.test_capability_skills',reason='Replay pre-authority Skill policy fixtures',event_sink=events.append):
        yield
