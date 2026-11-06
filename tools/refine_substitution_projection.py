from migrate_next import edit


def prefer_native(source):
    old = "            matching = []\n            for historical in self.data['checks']:"
    new = """            native_available = any(r['goal_id'] == g['id'] and r['subjects'] == subjects
                                   and r['condition_hash'] == identity(g['acceptance'])
                                   for r in self.data['checks'])
            matching = []
            for historical in self.data['checks']:"""
    assert old in source
    source=source.replace(old,new,1)
    old="                peers = [r for r in self.data['checks'] if r['goal_id'] == g['id']"
    new="                if native_available:\n                    continue\n"+old
    assert old in source
    return source.replace(old,new,1)


if __name__=='__main__':
    edit('cgkn/state/acceptance.py',prefer_native,
         'Prefer exact current evidence over derived substitution, including current counterexamples')
