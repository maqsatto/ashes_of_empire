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

GAME=Path('C:/Hearts of Iron IV')
state_files={p.name:p for p in (GAME/'history/states').glob('*.txt')}
native_members=set()
for p in state_files.values():
    s=re.sub(r'#[^\n]*','',p.read_text(encoding='utf-8-sig'))
    m=re.search(r'\bprovinces\s*=\s*\{([^}]+)',s)
    if m:native_members.update(map(int,re.findall(r'\d+',m[1])))
state_files.update({p.name:p for p in (ROOT/'history/states').glob('*.txt')})
province_state={};state_owner={};state_ids=set()
for p in state_files.values():
    s=re.sub(r'#[^\n]*','',p.read_text(encoding='utf-8-sig'))
    sid=int(re.search(r'\bid\s*=\s*(\d+)',s)[1])
    require(sid not in state_ids,f'Duplicate state definition ID {sid}: {p}')
    state_ids.add(sid)
    m=re.search(r'\bowner\s*=\s*(\w+)',s)
    state_owner[sid]=m[1] if m else None
    m=re.search(r'\bprovinces\s*=\s*\{([^}]+)',s)
    members=list(map(int,re.findall(r'\d+',m[1]))) if m else []
    require(bool(members),f'Empty province list in state {sid}')
    for prov in members:
        require(prov not in province_state,f'Province {prov} assigned twice: {province_state.get(prov)}, {sid}')
        province_state[prov]=sid
    for block in re.findall(r'\bvictory_points\s*=\s*\{([^}]+)',s):
        pairs=re.findall(r'\d+(?:\.\d+)?',block)
        for prov in pairs[::2]:require(int(prov) in members,f'State {sid}: VP {prov} lies in another state')
require(set(province_state)==native_members,'Land province membership changed: missing '+str(sorted(native_members-set(province_state)))+'; new '+str(sorted(set(province_state)-native_members)))
buildings=ROOT/'map/buildings.txt'
if buildings.exists():
    rows=buildings.read_text(encoding='utf-8-sig').split('\n')
    require(all(len(row.split(';'))==7 for row in rows),'Map buildings requires seven fields per row and no terminal blank row')
    import csv,numpy as np
    from PIL import Image
    from map_model_sampling import audit_model_membership,validate_engine_observations,validate_required_sites,STATE_SITE_TYPES,NORMAL_MODEL_TYPES
    from build_v03_kaz_regions import BODY,NEW
    from build_v03_state_edits import AFFECTED,MOVES
    rgb={tuple(map(int,r[1:4])):int(r[0]) for r in csv.reader((GAME/'map/definition.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter=';') if len(r)>4 and r[0].isdigit()}
    pixels=np.asarray(Image.open(GAME/'map/provinces.bmp').convert('RGB'))
    validate_engine_observations(pixels,rgb)
    affected=set(BODY)|set(NEW)|AFFECTED
    affected_provinces={p for p,s in province_state.items() if s in affected}|set(MOVES)
    model_report=audit_model_membership(rows,pixels,rgb,province_state,affected,affected_provinces)
    require(not model_report['affected_mismatches'],'Map model/state mismatches in changed regions: '+str(model_report['affected_mismatches']))
    try:
        validate_required_sites(rows,pixels,rgb,province_state,set(BODY)|set(NEW),STATE_SITE_TYPES+NORMAL_MODEL_TYPES)
        print('All17oblasts have valid native visual sites; this adds no actual building levels.')
    except RuntimeError as exc:
        require(False,str(exc))
    print('Building-model placement checked; untouched native floating-harbour placeholders: '+str(len(model_report['native_floating_harbor_mismatches'])))
print(f'Effective map: {len(state_ids)} unique states; {len(province_state)} provinces assigned exactly once; VP membership checked.')
from build_v03_strategic import validate_effective
try:
    strategic_report=validate_effective()
    print('Strategic region membership PASS: every state fits within one area.')
except RuntimeError as exc:
    require(False,str(exc))

manifest=ROOT/'docs/design_v0_3/WORLD_MANIFEST.json'
if manifest.exists():
    world=json.loads(manifest.read_text(encoding='utf-8'))['countries']
    for tag,c in world.items():
        require(c['capital_state'] in c['states'],f'{tag}: capital not owned')
        require(c['capital_province']>0,f'{tag}: no capital province')
        require(province_state.get(c['capital_province'])==c['capital_state'],f'{tag}: capital province/state mismatch')
        require(state_owner.get(c['capital_state'])==tag,f'{tag}: actual capital state owner mismatch')
        for unit in c.get('deployment',[]):
            sid=province_state.get(unit['province'])
            require(state_owner.get(sid)==tag,f'{tag}: starting unit in foreign province {unit["province"]}')
    print(f'World manifest: {len(world)} countries; capital ownership verified.')
print(f'{len(scripts)} scripts; {len(focus_ids)} focuses; {len(event_ids)} events; '+', '.join(f'{l}: {len(k)} localisation keys' for l,k in localisations.items()))
if errors:
    print('\n'.join(errors));sys.exit(1)
print('Static checks PASS. Engine loading, scopes and gameplay still require actual HOI4 checks.')
