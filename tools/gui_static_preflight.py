"""Read-only literal DOM closure diagnostic; never an acceptance verdict."""
from pathlib import Path
from html.parser import HTMLParser
import ast, collections, hashlib, json, re, sys

source = Path(sys.argv[1])
raw = source.read_bytes()
tree = ast.parse(raw.decode('utf8'))
html = next(ast.literal_eval(n.value) for n in tree.body
            if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'INDEX_HTML' for t in n.targets))

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.testids = [], []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        if 'data-testid' in attrs: self.testids.append(attrs['data-testid'])

tags = Tags()
tags.feed(html)
refs = set(re.findall(r'''(?:getElementById|\bel)\(['"]([^'"]+)['"]\)''', html))
report = {
    'kind': 'StaticGuiClosureDiagnostic',
    'source_sha256': hashlib.sha256(raw).hexdigest(),
    'duplicate_ids': [k for k,v in collections.Counter(tags.ids).items() if v > 1],
    'duplicate_testids': [k for k,v in collections.Counter(tags.testids).items() if v > 1],
    'missing_literal_targets': sorted(refs - set(tags.ids)),
    'limitations': 'Dynamic DOM construction, media bytes, event execution and business readiness require browser verification.',
    'acceptance_authority': False,
    'host_business_patches': 0,
}
if len(sys.argv) > 2:
    with Path(sys.argv[2]).open('x', encoding='utf8') as out:
        json.dump(report, out, indent=2)
print(json.dumps(report))
