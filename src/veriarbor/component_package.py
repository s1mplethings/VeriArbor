"""Portable content envelope for existing Block/Variant contracts, never authority."""
import base64
import hashlib
import re
from pathlib import PurePosixPath
from .block import Block
from .model import stable_hash


def relative_name(name):
    p=PurePosixPath(name)
    if (not isinstance(name,str) or not p.parts or p.is_absolute() or
            any(x in name for x in ('\\', ':')) or
            any(x in {'.','..','inputs','__pycache__'} or x.startswith('.') for x in p.parts)):
        raise ValueError('nonportable artifact path')
    if p.suffix.lower() not in {'.py','.json','.txt','.md','.toml','.yaml','.yml','.js','.ts','.html','.css'}:
        raise ValueError('artifact type requires explicit portable adapter')
    if any(word in p.name.lower() for word in ('credential','secret','token','authorization','budget','ledger')):
        raise ValueError('control or credential artifacts cannot be packaged')
    return p.as_posix()


def pack(block, contents, *, entrypoint, dependencies, applicability, invocation=None):
    entrypoint=relative_name(entrypoint)
    expected=dict(block.variant.artifacts)
    if set(contents)!=set(expected) or entrypoint not in expected:
        raise ValueError('package must contain exactly the selected variant and its entrypoint')
    def public_metadata(value):
        if isinstance(value,dict):
            for k,v in value.items():public_metadata(k);public_metadata(v)
        elif isinstance(value,(list,tuple)):
            for v in value:public_metadata(v)
        elif isinstance(value,str) and (re.search(r'[A-Za-z]:[\\/]',value) or value.startswith(('/home/','/Users/','/tmp/'))):
            raise ValueError('package metadata contains a host path')
    public_metadata(block.as_dict());public_metadata(dependencies);public_metadata(applicability)
    if len(contents)>128 or sum(len(raw) for raw in contents.values())>8_000_000:
        raise ValueError('portable package exceeds content bounds')
    files={}
    for name,raw in contents.items():
        relative_name(name)
        if hashlib.sha256(raw).hexdigest()!=expected[name]:raise ValueError('variant identity mismatch')
        if len(raw)>2_000_000:raise ValueError('artifact exceeds portable size bound')
        text=raw.decode('utf-8')
        if re.search(r'-----BEGIN .*PRIVATE KEY-----|(?:sk-|sk_)[A-Za-z0-9_-]{20,}',text):
            raise ValueError('credential material cannot be exported')
        files[name]=base64.b64encode(raw).decode('ascii')
    # Only the chosen implementation travels. Certificates remain at their authority.
    public=block.as_dict();public['variants']=[block.variant.__dict__];public['certificate_ref']=None
    public['variants'][0]={**public['variants'][0],'status':'ACTIVE'}
    value={'format':'veriarbor.component/1','block':public,'files':files,'entrypoint':entrypoint,
           'dependencies':dict(dependencies),'applicability':dict(applicability)}
    if invocation is not None:
        if (set(invocation)!={'protocol','input_semantics','error_semantics'} or
                invocation['protocol']!='python-json-stdio@1' or not entrypoint.endswith('.py') or
                not all(isinstance(invocation[k],str) and invocation[k].strip() for k in invocation)):
            raise ValueError('explicit supported invocation contract required')
        if not block.output_ports:raise ValueError('callable component requires output ports')
        public_metadata(invocation)
        value.update(format='veriarbor.component/2',invocation=dict(invocation))
    value['identity']=stable_hash(value)
    return value


def unpack(value, *, available, context):
    expected={'format','block','files','entrypoint','dependencies','applicability','identity'}
    if value.get('format')=='veriarbor.component/2':expected.add('invocation')
    if set(value)!=expected or value['format'] not in {'veriarbor.component/1','veriarbor.component/2'}:
        raise ValueError('unsupported portable envelope')
    if stable_hash({k:v for k,v in value.items() if k!='identity'})!=value['identity']:
        raise ValueError('package identity mismatch')
    block=Block.from_dict(value['block'])
    if len(block.variants)!=1 or block.certificate_ref:raise ValueError('package carries nonportable state')
    if not all(context.get(k)==v for k,v in value['applicability'].items()):
        raise ValueError('current context does not satisfy applicability')
    if any(available.get(k)!=v for k,v in value['dependencies'].items()):
        raise ValueError('unresolved or incompatible dependency; explicit adapter required')
    if len(value['files'])>128:raise ValueError('package file count exceeded')
    if sum(len(v) for v in value['files'].values())>11_000_000:raise ValueError('encoded package exceeds bounds')
    contents={relative_name(k):base64.b64decode(v,validate=True) for k,v in value['files'].items()}
    canonical=pack(block,contents,entrypoint=value['entrypoint'],dependencies=value['dependencies'],applicability=value['applicability'],invocation=value.get('invocation'))
    if canonical['identity']!=value['identity']:raise ValueError('noncanonical package')
    return block,contents
