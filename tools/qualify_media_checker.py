"""Strengthen the independent observer; never modify product implementation."""
from pathlib import Path
import ast, hashlib, json, tempfile
R=Path('F:/CGKN-ITER-132/production-core-convergence-v1/promotion/run-05')
M=Path('F:/CGKN-LeanLoop-V1-20261101/migration/veriarbor')
old=R/'consumer-revisions/gui-locators-v3.py'
new=R/'consumer-revisions/media-integrity-v4.py'
helper='''
def media_publish_integrity_probe(pid, cid, mid, stored):
    original_bytes = stored.read_bytes()
    try:
        with Platform() as platform:
            first = call('M7', 'publish.send', project_id=pid, content_id=cid,
                         platform_url=platform.url, idempotency_key='media-valid')
            require(first['status'] == 'PUBLISHED', 'Valid media must publish')
            repeated = call('M7', 'publish.send', project_id=pid, content_id=cid,
                            platform_url=platform.url, idempotency_key='media-valid')
            require(repeated['id'] == first['id'] and len(platform.posts) == 1,
                    'Media publication must retain idempotency')
            stored.write_bytes(original_bytes + b'changed-after-approval')
            invalid(lambda: call('M7', 'publish.send', project_id=pid, content_id=cid,
                                 platform_url=platform.url, idempotency_key='media-changed'))
            require(len(platform.posts) == 1, 'Changed media caused a network effect')
            stored.write_bytes(original_bytes)
            require(call('M11', 'media.get', project_id=pid, media_id=mid)['status'] == 'VALID',
                    'Restored media bytes must revalidate')
            stored.unlink()
            invalid(lambda: call('M7', 'publish.send', project_id=pid, content_id=cid,
                                 platform_url=platform.url, idempotency_key='media-missing'))
            require(len(platform.posts) == 1, 'Missing media caused a network effect')
    finally:
        stored.write_bytes(original_bytes)
        call('M11', 'media.get', project_id=pid, media_id=mid)

'''
source=old.read_text(encoding='utf8')
needle="    stored.unlink();require(call('M11','media.get',project_id=pid,media_id=mid)['status']=='BROKEN','Missing media hidden')"
assert source.count(needle)==1
revised=source.replace('def milestone11():',helper+'def milestone11():',1).replace(needle,'    media_publish_integrity_probe(pid, cid, mid, stored)\n'+needle,1)
with new.open('x',encoding='utf8') as f:f.write(revised)
def defs(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before,after=defs(source),defs(revised)
unchanged=[name for name in before if before[name]==after[name]]
assert set(before)-set(unchanged)=={'milestone11'}
scope={}
exec(compile(ast.Module(body=[n for n in ast.parse(revised).body if isinstance(n,ast.FunctionDef) and n.name in {'require','invalid','media_publish_integrity_probe'}],type_ignores=[]),str(new),'exec'),scope)
controls=[]
for mode,kind,expected in [('correct','positive',True),('cached_only','negative',False),('always_reject','negative',False),('changed_only','mutation',False),('post_then_reject','mutation',False),('duplicate_post','mutation',False)]:
    with tempfile.TemporaryDirectory(dir=M/'scratch') as folder:
        stored=Path(folder)/'fixture';stored.write_bytes(b'original')
        class Platform:
            def __enter__(self):self.posts=[];self.url='fixture-only';scope['active']=self;return self
            def __exit__(self,*args):pass
        receipts={}
        def call(tag,op,**kw):
            valid=stored.exists() and stored.read_bytes()==b'original'
            if op=='media.get':return {'status':'VALID' if valid else 'BROKEN'}
            key=kw['idempotency_key'];platform=scope['active']
            if mode=='always_reject':raise ValueError('fixture rejects everything')
            if mode!='cached_only' and not valid:
                if mode=='post_then_reject':platform.posts.append(key)
                if not (mode=='changed_only' and not stored.exists()):raise ValueError('fixture invalid media')
            if key not in receipts or mode=='duplicate_post':platform.posts.append(key)
            return receipts.setdefault(key,{'id':key,'status':'PUBLISHED'})
        scope.update(Platform=Platform,call=call)
        try:scope['media_publish_integrity_probe']('p','c','m',stored);observed=True;error=''
        except Exception as e:observed=False;error=type(e).__name__+': '+str(e)
        controls.append({'name':mode,'kind':kind,'expected':expected,'observed':observed,'passed':observed==expected,'error':error})
        assert stored.read_bytes()==b'original'
assert all(c['passed'] for c in controls)
report={'kind':'IndependentMediaCheckerControls','status':'PASS','previous_checker_hash':hashlib.sha256(old.read_bytes()).hexdigest(),'checker_hash':hashlib.sha256(new.read_bytes()).hexdigest(),'controls':controls,'unchanged_functions_and_classes':unchanged,'changed_functions':['milestone11'],'policy':'Adds real valid-media publish/idempotency and mutation/deletion-before-media.get assertions. All previous assertions retained. Fixture controls are observer qualification, not product acceptance.','activation':'NOT_ACTIVATED','host_business_patches':0}
with (M/'MEDIA_CHECKER_V4_QUALIFICATION.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
