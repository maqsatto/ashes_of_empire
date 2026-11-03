"""Focused content validation, not a substitute for the HOI4 parser or playtest."""
from pathlib import Path
import re,sys,json

ROOT=Path(__file__).resolve().parents[1]
errors=[]
def require(ok,message):
    if not ok:errors.append(message)

scripts={}
for folder in ['common','events','history','interface']:
    for p in (ROOT/folder).rglob('*'):
        if p.suffix not in ('.txt','.gfx','.lua') or not p.is_file():continue
        text=p.read_text(encoding='utf-8-sig');scripts[p.relative_to(ROOT).as_posix()]=text
        stripped=re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*','',text)
        depth=0
        for c in stripped:
            depth+=(c=='{')-(c=='}')
            require(depth>=0,f'{p}: unexpected closing brace')
        require(depth==0,f'{p}: unbalanced braces {depth}')
        require(not re.search(r'\badd_(?:army|navy|air)_experience\s*=',stripped),f'{p}: obsolete XP effect')
        require(not re.search(r'\bexists\s*=\s*[A-Z]{3}\b',stripped),f'{p}: exists requires boolean in country scope')

localisations={}
for lang in ['english','russian']:
    keys={}
    paths=list((ROOT/'localisation'/lang).rglob('*.yml'))
    paths += list((ROOT/'localisation/replace').glob(f'*_l_{lang}.yml'))
    for p in paths:
        b=p.read_bytes();require(b.startswith(b'\xef\xbb\xbf'),f'{p}: missing BOM')
        s=b.decode('utf-8-sig');require(s.startswith('l_'+lang+':'),f'{p}: wrong header')
        for k in re.findall(r'^\s+([^\s:#]+):',s,re.M):
            require(k not in keys,f'{p}: duplicate mod localisation {k}')
            keys[k]=p
    localisations[lang]=keys

focus_text='\n'.join(s for p,s in scripts.items() if p.startswith('common/national_focus/'))
focus_ids=re.findall(r'\b(?:focus|shared_focus)\s*=\s*\{\s*id\s*=\s*(aof_\w+)',focus_text)
require(len(focus_ids)==len(set(focus_ids)),'duplicate focus IDs')
refs=re.findall(r'\b(?:focus|shared_focus|has_completed_focus|complete_national_focus)\s*=\s*(aof_\w+)',focus_text)
for ref in refs:require(ref in focus_ids,f'missing focus {ref}')
for ident in focus_ids:
    for lang,keys in localisations.items():
        require(ident in keys and ident+'_desc' in keys,f'{lang}: missing focus localisation {ident}')

event_ids=[]
for p,s in scripts.items():
    if p.startswith('events/'):
        event_ids+=re.findall(r'(?:^|\n)\s*(?:country_event|news_event)\s*=\s*\{\s*id\s*=\s*(aof[\w.]+)',s)
require(len(event_ids)==len(set(event_ids)),'duplicate event IDs')
for p,s in scripts.items():
    for ref in re.findall(r'\bid\s*=\s*(aof[\w]*\.[0-9]+)',s):
        require(ref in event_ids,f'{p}: missing event {ref}')

manifest=ROOT/'docs/design_v0_3/WORLD_MANIFEST.json'
if manifest.exists():
    world=json.loads(manifest.read_text(encoding='utf-8'))['countries']
    for tag,c in world.items():
        require(c['capital_state'] in c['states'],f'{tag}: capital not owned')
        require(c['capital_province']>0,f'{tag}: no capital province')
    print(f'World manifest: {len(world)} countries; capital ownership verified.')
print(f'{len(scripts)} scripts; {len(focus_ids)} focuses; {len(event_ids)} events; '+', '.join(f'{l}: {len(k)} localisation keys' for l,k in localisations.items()))
if errors:
    print('\n'.join(errors));sys.exit(1)
print('Static checks PASS. Engine loading, scopes and gameplay still require actual HOI4 checks.')
