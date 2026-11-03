"""Explicit user-approved province corrections; default is READ-ONLY inspection.

Run --prepare-backup PATH once with HOI4 CLOSED, then --apply --backup-dir PATH
AFTER world generation and the guarded Caspian stage. No installed game writes.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math,re,subprocess,sys
from PIL import Image
from map_model_sampling import engine_pixel
from contentlib import ROOT
GAME=Path('C:/Hearts of Iron IV')
BACKUP=Path('C:/Users/maqsatto/.codex/backups/ashes_of_empires/user-state-edits-20261103')
BRANCH='spike/caspian-navigation'
MOVES={4265:651,10185:651,1334:573,3265:251,4324:251,227:251}
DONORS={4265:582,10185:582,1334:582,3265:652,4324:652,227:652}
OWNERS={582:'KAZ',652:'KAZ',236:'KAZ'}
AFFECTED={236,251,573,582,651,652}
def sha(data):return hashlib.sha256(data).hexdigest()
def mask(s):return re.sub(r'"(?:[^"\\]|\\.)*"|#[^\n]*',lambda m:' '*len(m[0]),s)
def block(s,key):
    m=re.search(r'(?<!\w)'+re.escape(str(key))+r'\s*=\s*\{',mask(s));assert m,('missing block',key)
    start=m.start();a=m.end();b=a;depth=1;clean=mask(s)
    while depth:depth+=(clean[b]=='{')-(clean[b]=='}');b+=1
    return start,a,b-1,b
def ps(s):
    _,a,b,_=block(s,'provinces');return list(map(int,re.findall(r'\d+',mask(s[a:b]))))
def owner(s):return re.search(r'\bowner\s*=\s*(\w+)',mask(s))[1]
def effective(rel):
    p=ROOT/rel
    return p.read_bytes() if p.exists() else (GAME/rel).read_bytes()
def inventory():
    result={}
    for p in (GAME/'history/states').glob('*.txt'):
        native=p.read_text(encoding='utf-8-sig');sid=int(re.search(r'\bid\s*=\s*(\d+)',mask(native))[1]);rel='history/states/'+p.name
        result[sid]={'rel':rel,'native':native,'text':effective(rel).decode('utf-8-sig')}
    return result
def closed_and_isolated():
    if sys.platform=='win32':
        r=subprocess.run(['tasklist','/FI','IMAGENAME eq hoi4.exe','/FO','CSV','/NH'],capture_output=True,text=True)
        if 'hoi4.exe' in r.stdout.lower():raise RuntimeError('Close HOI4 before preparing or applying state edits.')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!=BRANCH:raise RuntimeError('Use isolated branch '+BRANCH)
def backup_path(value):
    p=Path(value).resolve()
    if p!=BACKUP.resolve():raise RuntimeError('Use the explicitly approved external backup directory '+str(BACKUP))
    if ROOT.resolve() in p.parents:raise RuntimeError('Backup must remain outside the project.')
    return p
def prepare(value):
    closed_and_isolated();base=backup_path(value)
    if (base/'manifest.json').exists():raise RuntimeError('Existing backup is preserved; use its --backup-dir after checking the manifest.')
    inv=inventory();rels=[inv[i]['rel'] for i in sorted(AFFECTED)]+['map/buildings.txt','map/railways.txt','map/supply_nodes.txt','map/provinces.bmp','map/definition.csv','docs/design_v0_3/WORLD_MANIFEST.json']
    files={}
    for rel in rels:
        data=effective(rel);target=base/'inputs'/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=data:raise RuntimeError('Preserve existing different backup '+str(target))
        target.write_bytes(data);files[rel]=sha(data)
    native={inv[i]['rel']:sha((GAME/inv[i]['rel']).read_bytes()) for i in AFFECTED}
    base.mkdir(parents=True,exist_ok=True)
    (base/'manifest.json').write_text(json.dumps({'branch':BRANCH,'moves':MOVES,'owners':OWNERS,'files':files,'native_state_sha256':native},indent=2)+'\n',encoding='utf8')
    print('Verified-byte backup prepared outside the project:',base)
def replace_provinces(text,ids):
    _,a,b,_=block(text,'provinces');return text[:a]+'\n\t\t'+' '.join(map(str,sorted(ids)))+'\n\t'+text[b:]
def detach_attachments(text,province):
    """Move native VP blocks and province-specific building blocks, not factories."""
    attachments=[];building=None
    for m in list(re.finditer(r'\bvictory_points\s*=\s*\{',mask(text)))[::-1]:
        start,a,b,end=block(text[m.start():],'victory_points');start+=m.start();a+=m.start();b+=m.start();end+=m.start()
        nums=re.findall(r'\d+(?:\.\d+)?',mask(text[a:b]));pairs=[(int(nums[i]),nums[i+1]) for i in range(0,len(nums),2)]
        selected=[pair for pair in pairs if pair[0]==province]
        if selected:
            attachments.extend('victory_points = { '+str(pid)+' '+value+' }' for pid,value in selected)
            remaining=[pair for pair in pairs if pair[0]!=province]
            replacement='victory_points = { '+' '.join(str(pid)+' '+value for pid,value in remaining)+' }' if remaining else ''
            text=text[:start]+replacement+text[end:]
    _,ha,hb,_=block(text,'history');history=text[ha:hb]
    if re.search(r'\bbuildings\s*=\s*\{',mask(history)):
        _,ba,bb,_=block(history,'buildings');body=history[ba:bb]
        if re.search(r'(?<!\d)'+str(province)+r'\s*=\s*\{',mask(body)):
            start,_,_,end=block(body,str(province));building=body[start:end];body=body[:start]+body[end:];history=history[:ba]+body+history[bb:];text=text[:ha]+history+text[hb:]
    return text,attachments,building
def attach(text,vps,building):
    _,a,b,_=block(text,'history');history=text[a:b]
    if building:
        _,_,bb,_=block(history,'buildings');history=history[:bb]+'\n'+building+'\n'+history[bb:]
    history+='\n'+'\n'.join(vps)+'\n';return text[:a]+history+text[b:]
def plan():
    inv=inventory();membership={};before={};observed={}
    for sid,data in inv.items():
        for province in ps(data['text']):
            observed.setdefault(province,[]).append(sid)
            membership[province]=sid
        before[sid]=set(ps(data['text']))
    for province,sids in observed.items():
        if len(sids)>1:
            # A full rebuild rewrites donor histories before this stage, while
            # recipient overrides from its previous run still exist. Reconcile
            # only that exact known pair, never arbitrary duplicate provinces.
            if province not in MOVES or set(sids)!={DONORS[province],MOVES[province]}:raise RuntimeError('Duplicate initial province '+str(province))
            membership[province]=DONORS[province]
    report={'moves':{},'owners':OWNERS,'railways_unchanged':True,'supply_nodes_unchanged':True,'province_bitmap_unchanged':True,'navigation_verified':False}
    for province,target in MOVES.items():
        native_members=[sid for sid,data in inv.items() if province in ps(data['native'])]
        if native_members!=[DONORS[province]]:raise RuntimeError('Installed province membership changed '+str(province))
        current=membership.get(province)
        if current not in [DONORS[province],target]:raise RuntimeError('Unexpected effective membership '+str(province))
        vps=[];building=None
        if current!=target:
            donor=inv[current];dest=inv[target];donor['text'],vps,building=detach_attachments(donor['text'],province)
            donor['text']=replace_provinces(donor['text'],set(ps(donor['text']))-{province})
            dest['text']=replace_provinces(dest['text'],set(ps(dest['text']))|{province})
            if vps or building:dest['text']=attach(dest['text'],vps,building)
            membership[province]=target
        report['moves'][str(province)]={'native_from':DONORS[province],'to':target,'victory_points_moved':vps,'province_building_moved':bool(building)}
    # Ownership comes from world authoring; enforce it if independently applied.
    for sid,tag in OWNERS.items():
        text=inv[sid]['text'];_,a,b,_=block(text,'history');h=text[a:b]
        h=re.sub(r'\bowner\s*=\s*\w+','owner = '+tag,h,count=1)
        if re.search(r'\bcontroller\s*=',mask(h)):h=re.sub(r'\bcontroller\s*=\s*\w+','controller = '+tag,h,count=1)
        else:h='\ncontroller = '+tag+'\n'+h
        if not re.search(r'\badd_core_of\s*=\s*'+tag+r'\b',mask(h)):h+='\nadd_core_of = '+tag+'\n'
        inv[sid]['text']=text[:a]+h+text[b:]
    after=[p for s in inv.values() for p in ps(s['text'])]
    if len(after)!=len(set(after)) or set(after)!=set(membership):raise RuntimeError('Province disappeared or duplicated')
    outputs={inv[sid]['rel']:inv[sid]['text'].replace('\r\n','\n').encode('utf8') for sid in AFFECTED}
    # Static map building models also carry a state index. Reassign only models
    # physically inside a moved province; coordinates, type and counts stay put.
    definitions={}
    for row in csv.reader((GAME/'map/definition.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter=';'):
        if len(row)>4 and row[0].isdigit():definitions[tuple(map(int,row[1:4]))]=int(row[0])
    image=Image.open(GAME/'map/provinces.bmp').convert('RGB');lines=effective('map/buildings.txt').decode('utf-8-sig').splitlines();changed=[]
    for i,line in enumerate(lines):
        row=line.split(';')
        if len(row)<7 or not row[0].isdigit() or int(row[0]) not in AFFECTED:continue
        x,y=engine_pixel(row[2],row[4],image.height)
        if not (0<=x<image.width and 0<=y<image.height):continue
        province=definitions.get(image.getpixel((x,y)))
        if province in MOVES and int(row[0]) in {DONORS[province],MOVES[province]}:
            row[0]=str(MOVES[province]);lines[i]=';'.join(row);changed.append({'province':province,'native_province_state':DONORS[province],'to_state':MOVES[province],'type':row[1],'line':i+1})
    outputs['map/buildings.txt']='\n'.join(lines).encode('utf8');report['building_model_state_indices']=changed
    # Update the authoritative world manifest after the province corrections.
    world=json.loads(effective('docs/design_v0_3/WORLD_MANIFEST.json').decode('utf-8-sig'))
    for sid in AFFECTED:
        data=inv[sid];text=data['text'];points=[]
        for m in re.finditer(r'victory_points\s*=\s*\{([^}]+)',mask(text)):
            nums=re.findall(r'\d+(?:\.\d+)?',m[1]);points.extend([int(nums[i]),float(nums[i+1])] for i in range(0,len(nums),2))
        entry=world['states'].setdefault(str(sid),{'source_file':Path(data['rel']).name,'name_key':'STATE_'+str(sid),'installed_name':{236:'Astrakhan',251:'Kuybyshev',573:'Zlatoust',582:'Magnitogorsk',651:'Ufa',652:'Orenburg'}[sid],'installed_owner':owner(data['native'])})
        entry.update({'fixture_owner':owner(text),'provinces':ps(text),'victory_points':points})
    for tag,country in world['countries'].items():
        country['states']=[sid for sid,data in inv.items() if owner(data['text'])==tag]
        for deployment in country.get('deployment',[]):
            actual=membership[deployment['province']]
            if owner(inv[actual]['text'])!=tag:raise RuntimeError('Starting unit is across the new border '+str(deployment))
            deployment['state']=actual
    world['user_authorized_province_transfers']=report['moves'];outputs['docs/design_v0_3/WORLD_MANIFEST.json']=(json.dumps(world,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    return outputs,report
def apply(value):
    closed_and_isolated();base=backup_path(value);saved=json.loads((base/'manifest.json').read_text(encoding='utf8'))
    for rel,expected in saved['files'].items():
        if sha((base/'inputs'/rel).read_bytes())!=expected:raise RuntimeError('Damaged backup '+rel)
    for rel,expected in saved['native_state_sha256'].items():
        if sha((GAME/rel).read_bytes())!=expected:raise RuntimeError('Installed state changed '+rel)
    outputs,report=plan()
    # Immutable province identities / transport network: no edits or repair.
    for rel in ['map/provinces.bmp','map/railways.txt','map/supply_nodes.txt']:
        if sha(effective(rel))!=saved['files'][rel]:raise RuntimeError('Unreviewed concurrent transport/geometry edit '+rel)
    for rel,data in outputs.items():
        p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    upstream_path=ROOT/'docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json'
    upstream=json.loads(upstream_path.read_text(encoding='utf8')) if upstream_path.exists() else {}
    report.update({'backup_directory':str(base),'branch':BRANCH,'upstream_caspian_backup_directory':upstream.get('backup_directory'),'upstream_caspian_base_commit':upstream.get('base_commit'),'output_sha256':{rel:sha(data) for rel,data in outputs.items()},'actual_game_test':'UNVERIFIED; full restart and new campaign required'})
    p=ROOT/'docs/design_v0_3/USER_STATE_EDITS_MANIFEST.json';data=(json.dumps(report,indent=2)+'\n').encode('utf8')
    if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    notes='''# Explicit owner-authorised state corrections — 3 November 2026

The owner explicitly requested provinces 4265 and 10185 from Magnitogorsk 582 to Ufa 651; province 1334 from Magnitogorsk to Zlatoust 573; and provinces 3265, 4324 and 227 from Orenburg 652 to Kuybyshev 251. Whole states 582, 652 and 236 (Astrakhan) belong to Alash. This records those specific border decisions; it does not approve other provisional geography, capitals or personalities.

Installed initial history attaches no victory point or province-level building to these six provinces. The generator nevertheless moves either attachment if present in current effective history. State-level resources, population, factories and infrastructure remain with their respective states. Static building model state indices follow the provinces, without changing model positions or types. Railway province IDs and supply nodes are preserved; the native Ufa route uses provinces 3265 and 4324, and will now follow the new political boundary. No new railway or supply node is invented. Astrakhan 236 is distinct from Stavropol 235 and is not in the current canal corridor.

Back up outside the repository, apply only on the isolated map branch with HOI4 closed, then fully restart and inspect a new campaign. Province membership and ownership checks are static; the generator does not claim an actual game test or mark Caspian navigation verified.
'''
    p=ROOT/'docs/design_v0_3/USER_STATE_EDITS.md';data=notes.encode('utf8')
    if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    print('Owner-requested state corrections applied; full restart/new campaign required.')
def main():
    cli=argparse.ArgumentParser(description=__doc__);mode=cli.add_mutually_exclusive_group();mode.add_argument('--inspect',action='store_true');mode.add_argument('--prepare-backup');mode.add_argument('--apply',action='store_true');cli.add_argument('--backup-dir');args=cli.parse_args()
    if args.prepare_backup:prepare(args.prepare_backup)
    elif args.apply:
        if not args.backup_dir:cli.error('--apply requires --backup-dir')
        apply(args.backup_dir)
    else:
        outputs,report=plan();report['mode']='READ_ONLY_NO_RUNTIME_WRITES';report['planned_outputs']={rel:sha(data) for rel,data in outputs.items()};print(json.dumps(report,indent=2))
if __name__=='__main__':main()
