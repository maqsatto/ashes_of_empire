"""Native VP markers and local names. Default --inspect is READ ONLY.

Apply after world -> Caspian -> explicit state edits -> Kazakhstan regions.
Prepare the external backup after those stages, before this stage writes.
"""
from pathlib import Path
import argparse,csv,hashlib,json,re,subprocess,sys
from contentlib import ROOT
from build_v03_state_edits import block,mask,ps,owner
GAME=Path('C:/Hearts of Iron IV');BRANCH='spike/caspian-navigation'
BACKUP=Path('C:/Users/maqsatto/.codex/backups/ashes_of_empires/user-cities-20261103')
CATALOG=json.loads((ROOT/'tools/v03_city_catalog.json').read_text(encoding='utf8'))
RENAMES={7341:('Актобе','Aktobe'),7597:('Акмешит','Aqmeshit'),3618:('Атырау','Atyrau'),11537:('Орал','Oral'),10312:('Костанай','Kostanay'),1591:('Алматы','Almaty'),12594:('Семей','Semey'),1668:('Аягоз','Ayagoz'),4333:('Акмола','Akmola'),7708:('Кереку','Kereku'),12583:('Бишкек','Bishkek'),1384:('Душанбе','Dushanbe'),1554:('Кармана','Karmana'),12333:('Ашхабад','Ashgabat'),1493:('Дашогуз','Dashoguz'),1573:('Бухара','Bukhara'),10671:('Самарканд','Samarkand'),1459:('Ташкент','Tashkent'),10488:('Коканд','Kokand'),12465:('Хива','Khiva'),1614:('Нукус','Nukus')}
PROTECTED={1591:'KAZ',1459:'TRK',10671:'UZB',12333:'TMS',12583:'KYR',1384:'TAJ'}
SOURCES={
 'coordinates':'https://download.geonames.org/export/dump/cities15000.zip',
 'small_town_coordinates':'https://download.geonames.org/export/dump/cities5000.zip',
 'small_settlement_coordinates':'https://download.geonames.org/export/dump/KZ.zip',
 'kaz_1897':'https://www.atyrau-city.kz/index.php?ch=7-6-&l=r&r=7&uid=historyKZ',
 'turkestan_1924':'https://mytashkent.uz/wp-content/uploads/2025/01/statisticheskij_ezhegodnik_1917_1923_gg_t_i_tashkent_1924_300125-071636.pdf',
 'kokshetau':'https://www.gov.kz/org/aqmola-kokshetau/?lang=ru',
 'taldykorgan':'https://www.gov.kz/org/zhetysu-architecture/documents/details/882590?lang=ru',
 'atbasar':'https://e-history.kz/ru/news/show/32804',
 'ekibastuz':'https://www.gov.kz/uploads/2021/6/15/ec35879e03f22b4e68354b96aed89ca7_original.7749330.pdf',
 'zhitikara':'https://zhitcollege.edu.kz/istoriya-goroda/',
 'zhosaly':'https://www.gov.kz/memleket/entities/kyzylorda-karmakshy/press/news/details/1295069?lang=ru',
 'shiyeli':'https://osken-onir.kz/kogam/6468-brnshler.html',
 'karagandy':'https://rail-news.kz/ru/news/2413-karaganda-tranzitnyy-potencial.html',
 'karkaraly':'https://www.gov.kz/org/karaganda-karkaraly/press/article/details/26183',
 'fergana':'https://www.fnpz.uz/en/company-profile/sutainable-development/home-city',
 'kyrgyz_history':'https://stepen.vak.kg/wp-content/uploads/2023/05/Dissertazia-Omurkanovoi-Tom-1.2-2024.pdf',
 'kulob':'https://egov.tj/site/kulob?lang=tg',
 'khorog':'https://www.khorugh.tj/index.php/ru/city-government-ru/history-establishment',
 'shahrisabz':'https://whc.unesco.org/en/list/885/',
 'sulukta':'https://www.rmebrk.kz/journals/440/41782.pdf',
 'karmana':'https://yuz.uz/index.php/ru/news/drevnyaya-karmana-v-obektive-istorii',
 'karsakpay':'https://www.gov.kz/org/ulytau-satpaev/press/article/details/9301?lang=ru',
 'karsakpay_settlement':'https://kazpravda.kz/n/v-poselke-karsakpay-nachinalas-istoriya-mednorudnogo-kraya/',
}
def digest(data):return hashlib.sha256(data).hexdigest()
def effective(rel,overlay=None):
    if overlay and rel in overlay:return overlay[rel]
    p=ROOT/rel
    return p.read_bytes() if p.exists() else (GAME/rel).read_bytes()
def inventory(overlay=None):
    paths={p.name:p for p in (GAME/'history/states').glob('*.txt')}
    paths.update({p.name:p for p in (ROOT/'history/states').glob('*.txt')})
    for rel in overlay or {}:
        if rel.startswith('history/states/') and rel.endswith('.txt'):paths[Path(rel).name]=ROOT/rel
    result={};membership={}
    for filename in sorted(paths):
        rel='history/states/'+filename;data=effective(rel,overlay);text=data.decode('utf-8-sig');sid=int(re.search(r'\bid\s*=\s*(\d+)',mask(text))[1])
        if sid in result:raise RuntimeError('Duplicate state ID '+str(sid))
        result[sid]={'rel':rel,'text':text,'data':data}
        for province in ps(text):
            if province in membership:raise RuntimeError('City stage needs reconciled state membership: duplicate '+str(province))
            membership[province]=sid
    return result,membership
def points(text):
    values={}
    for m in re.finditer(r'victory_points\s*=\s*\{([^}]+)',mask(text)):
        nums=re.findall(r'\d+(?:\.\d+)?',m[1])
        for i in range(0,len(nums),2):
            province,value=int(nums[i]),float(nums[i+1])
            if province in values:raise RuntimeError('Duplicate victory-point definition '+str(province))
            values[province]=value
    return values
def set_point(text,province,value):
    for m in re.finditer(r'victory_points\s*=\s*\{([^}]+)',mask(text)):
        pattern=r'(?<!\d)'+str(province)+r'\s+(\d+(?:\.\d+)?)';v=re.search(pattern,m[1])
        if v:
            if float(v[1])==value:return text
            a=m.start(1)+v.start(1);b=m.start(1)+v.end(1);return text[:a]+str(int(value) if int(value)==value else value)+text[b:]
    _,_,end,_=block(text,'history');return text[:end]+'\n\t\tvictory_points = { '+str(province)+' '+str(value)+' }\n\t'+text[end:]
def plan(overlay=None):
    for rel,key in [('map/provinces.bmp','native_bitmap_sha256'),('map/definition.csv','native_definition_sha256')]:
        if digest((GAME/rel).read_bytes())!=CATALOG[key]:raise RuntimeError('Installed geographic reference changed: '+rel)
    inv,membership=inventory(overlay);texts={sid:s['text'] for sid,s in inv.items()};report={'sources':SOURCES,'coordinate_method':CATALOG['method'],'geographic_anchors':CATALOG['anchors'],'cities':[],'capital_safeguards':[],'excluded':CATALOG['excluded'],'actual_game_test':'UNVERIFIED: province-scale inferred city placement requires in-game map review.'}
    definitions={int(r[0]):r for r in csv.reader((GAME/'map/definition.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter=';') if len(r)>4 and r[0].isdigit()}
    native_names={}
    for p in (GAME/'localisation/english').glob('*victory*points*.yml'):
        for pid,name in re.findall(r'^\s*VICTORY_POINTS_(\d+):\d*\s*"([^"]+)"',p.read_text(encoding='utf-8-sig'),re.M):native_names.setdefault(int(pid),name)
    localisation=dict(RENAMES);seen=set()
    for city in CATALOG['additional_markers']:
        pid=city['province'];sid=membership.get(pid)
        if pid in seen or pid not in definitions or definitions[pid][4]!='land':raise RuntimeError('Invalid city province '+str(pid))
        seen.add(pid)
        if sid is None or owner(texts[sid])!=city['country']:raise RuntimeError('City outside its intended start country: '+city['en'])
        current=points(texts[sid]).get(pid);texts[sid]=set_point(texts[sid],pid,max(city['victory_points'],current or 0));localisation[pid]=(city['ru'],city['en'])
        entry=dict(city);entry.update({'effective_state':sid,'marker':'additional','native_localisation':native_names.get(pid),'score':points(texts[sid])[pid]});report['cities'].append(entry)
    # Country capitals are state-based; ensure a new VP cannot silently become
    # the highest-scoring province inside an existing or release capital state.
    for pid,tag in PROTECTED.items():
        sid=membership[pid];v=points(texts[sid]);old=v.get(pid)
        if old is None:raise RuntimeError('Missing original capital marker '+str(pid))
        other=max([score for p,score in v.items() if p!=pid]+[0]);required=max(old,other+1)
        texts[sid]=set_point(texts[sid],pid,required)
        report['capital_safeguards'].append({'tag':tag,'province':pid,'state':sid,'score':required,'highest_in_state':True})
    for pid,(ru,en) in RENAMES.items():
        sid=membership[pid]
        if pid not in points(texts[sid]):raise RuntimeError('A renamed native marker is missing '+str(pid))
        report['cities'].append({'province':pid,'ru':ru,'en':en,'effective_state':sid,'marker':'existing renamed','native_localisation':native_names.get(pid),'score':points(texts[sid])[pid],'provenance':'Exact native VP/localisation ID; no inferred city ID.'})
    outputs={inv[sid]['rel']:text.replace('\r\n','\n').encode('utf8') for sid,text in texts.items() if text!=inv[sid]['text']}
    # Hash every affected history even on a repeat when no bytes need changing:
    # upstream appliers must recognise the exact, known city-stage outputs.
    affected={c['effective_state'] for c in report['cities']}|{x['state'] for x in report['capital_safeguards']}
    for sid in affected:outputs[inv[sid]['rel']]=texts[sid].replace('\r\n','\n').encode('utf8')
    for lang,index in [('russian',0),('english',1)]:
        lines=['l_'+lang+':']
        for pid,pair in sorted(localisation.items()):
            if index==0 and re.search(r'[^А-Яа-яЁё 0-9().-]',pair[index]):raise RuntimeError('Nonstandard Cyrillic character in '+pair[index])
            lines.append(' VICTORY_POINTS_'+str(pid)+': '+json.dumps(pair[index],ensure_ascii=False))
        outputs['localisation/replace/aof_v03_cities_l_'+lang+'.yml']=('\n'.join(lines)+'\n').encode('utf-8-sig')
    world=json.loads(effective('docs/design_v0_3/WORLD_MANIFEST.json',overlay).decode('utf-8-sig'))
    for sid in affected:
        entry=world['states'].setdefault(str(sid),{'source_file':Path(inv[sid]['rel']).name,'name_key':'STATE_'+str(sid),'fixture_owner':owner(texts[sid])})
        entry['provinces']=ps(texts[sid]);entry['victory_points']=sorted([[pid,score] for pid,score in points(texts[sid]).items()],key=lambda x:(-x[1],x[0]))
    for tag,country in world['countries'].items():
        country['states']=sorted(sid for sid,text in texts.items() if owner(text)==tag)
        for deployment in country.get('deployment',[]):
            sid=membership[deployment['province']]
            if owner(texts[sid])!=tag:raise RuntimeError('City stage found an OOB across a border '+tag)
            deployment['state']=sid
    for tag,pid,expected_state in [('KAZ',1591,586),('TRK',1459,405)]:
        if membership[pid]!=expected_state:raise RuntimeError('Capital moved by an upstream stage: '+tag)
        world['countries'][tag]['capital_state']=expected_state;world['countries'][tag]['capital_province']=pid
    world['city_catalog']={'manifest':'docs/design_v0_3/CITY_MANIFEST.json','additional_markers':len(seen),'native_renames':len(RENAMES),'geographic_placement':'Reconstructed at province scale; review in game.'}
    oblasts={402,404,406,407,583,586,587,588,589,590,881,882,1082,1083,1084,1085,1086}
    if oblasts.issubset(inv):
        coverage={str(sid):len(points(texts[sid])) for sid in sorted(oblasts)}
        if not all(coverage.values()):raise RuntimeError('At least one Kazakhstan oblast has no settlement marker: '+str(coverage))
        report['oblast_coverage']={'each_has_a_marker':True,'victory_point_counts':coverage}
    else:report['oblast_coverage']={'each_has_a_marker':None,'note':'Inspect after the17-region stage for full coverage.'}
    outputs['docs/design_v0_3/WORLD_MANIFEST.json']=(json.dumps(world,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
    report['additional_markers']=len(seen);report['native_renames']=len(RENAMES)
    return outputs,report
def closed():
    if sys.platform=='win32':
        p=subprocess.run(['tasklist','/FI','IMAGENAME eq hoi4.exe','/FO','CSV','/NH'],capture_output=True,text=True)
        if 'hoi4.exe' in p.stdout.lower():raise RuntimeError('Close HOI4 before preparing/applying city history.')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!=BRANCH:raise RuntimeError('Use isolated map branch '+BRANCH)
def backup_path(value):
    p=Path(value).resolve()
    if p!=BACKUP.resolve() or ROOT.resolve() in p.parents:raise RuntimeError('Use approved external city backup '+str(BACKUP))
    return p
def prepare(value):
    closed();base=backup_path(value);marker=base/'city_backup_manifest.json'
    if marker.exists():raise RuntimeError('Existing city backup is preserved; reuse its --backup-dir.')
    outputs,_=plan();saved={}
    for rel in outputs:
        current=ROOT/rel
        if current.exists():
            data=current.read_bytes();target=base/'prior_mod'/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists() and target.read_bytes()!=data:raise RuntimeError('Different prior backup '+rel)
            target.write_bytes(data);saved[rel]=digest(data)
        else:saved[rel]=None
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    base.mkdir(parents=True,exist_ok=True);marker.write_text(json.dumps({'branch':BRANCH,'workspace':str(ROOT.resolve()),'base_commit':commit,'prior_mod_sha256':saved},indent=2)+'\n',encoding='utf8');print('City backup prepared:',base)
def ancestor(commit):
    return bool(commit) and subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,capture_output=True).returncode==0
def apply(value):
    closed();base=backup_path(value);saved=json.loads((base/'city_backup_manifest.json').read_text(encoding='utf8'))
    if saved.get('branch')!=BRANCH or Path(saved.get('workspace','')).resolve()!=ROOT.resolve() or not ancestor(saved.get('base_commit')):raise RuntimeError('City backup belongs to a different workspace, branch or nonancestor commit.')
    for rel,expected in saved['prior_mod_sha256'].items():
        if expected is not None and digest((base/'prior_mod'/rel).read_bytes())!=expected:raise RuntimeError('City backup damaged '+rel)
    outputs,report=plan();upstreams={}
    for name in ['CASPIAN_SPIKE_MANIFEST','KAZ_REGIONS_MANIFEST','USER_STATE_EDITS_MANIFEST']:
        p=ROOT/'docs/design_v0_3'/(name+'.json')
        if not p.exists():raise RuntimeError('Run the upstream stage before applying cities: '+name)
        upstreams[name]=json.loads(p.read_text(encoding='utf8'))
    caspian=upstreams['CASPIAN_SPIKE_MANIFEST'];regions=upstreams['KAZ_REGIONS_MANIFEST']
    previous_path=ROOT/'docs/design_v0_3/CITY_MANIFEST.json';previous=json.loads(previous_path.read_text(encoding='utf8')) if previous_path.exists() else {}
    previous_valid=(previous.get('branch')==BRANCH and Path(previous.get('workspace','')).resolve()==ROOT.resolve() and ancestor(previous.get('base_commit')) and previous.get('upstream_caspian_backup_directory')==caspian.get('backup_directory') and previous.get('upstream_caspian_base_commit')==caspian.get('base_commit') and previous.get('upstream_kaz_regions_backup_directory')==regions.get('backup_directory') and previous.get('upstream_kaz_regions_base_commit')==regions.get('base_commit'))
    known={}
    if previous_valid:
        for rel,hashed in previous.get('output_sha256',{}).items():known.setdefault(rel,set()).add(hashed.lower())
    for name,upstream in upstreams.items():
        valid=upstream.get('branch')==BRANCH
        if name!='CASPIAN_SPIKE_MANIFEST':valid=valid and upstream.get('upstream_caspian_backup_directory')==caspian.get('backup_directory') and upstream.get('upstream_caspian_base_commit')==caspian.get('base_commit')
        if not valid:raise RuntimeError('Upstream provenance mismatch: '+name)
        for rel,hashed in upstream.get('output_sha256',{}).items():known.setdefault(rel,set()).add(hashed.lower())
    for rel in outputs:
        if rel not in saved['prior_mod_sha256']:raise RuntimeError('Output was not included in the prepared city backup: '+rel)
        path=ROOT/rel;current=digest(path.read_bytes()) if path.exists() else None
        prior=saved['prior_mod_sha256'][rel];allowed=set(known.get(rel,set()))
        if prior is not None:allowed.add(prior.lower())
        if current is None and prior is None:continue
        if current not in allowed:raise RuntimeError('Independent manual city/history edit detected; preserve and reconcile before applying: '+rel)
    report.update({'branch':BRANCH,'workspace':str(ROOT.resolve()),'base_commit':saved['base_commit'],'backup_directory':str(base),'upstream_caspian_backup_directory':caspian.get('backup_directory'),'upstream_caspian_base_commit':caspian.get('base_commit'),'upstream_kaz_regions_backup_directory':regions.get('backup_directory'),'upstream_kaz_regions_base_commit':regions.get('base_commit'),'output_sha256':{rel:digest(data) for rel,data in outputs.items()}})
    # All guards and bytes are ready before the first runtime history write.
    for rel,data in outputs.items():
        p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    p=ROOT/'docs/design_v0_3/CITY_MANIFEST.json';data=(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
    if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    notes='''# City markers and local names

32 additional native VP markers and 21 existing-name corrections use ordinary Cyrillic and native province IDs. Additional towns are geographically reconstructed, not disguised as native city-localisation matches. The catalog records GeoNames coordinates, 33 installed named VP/unitstack controls, three candidate fits, alternative province matches and historical references. The game map is distorted; boundary cases and inferred placements require visual game review. No province geometry is edited and no railway, population, factory or resource is added. These are VP markers and labels, not new 3D urban terrain: cities.bmp, terrain and urban building footprints remain untouched. Naming follows the owner's local-name choices, separately from evidence that the settlement existed before 1924.

The 1924 Turkestan statistical yearbook and municipal/archive publications establish historical settlements; current GeoNames positions supply geographic coordinates, not 1924 population. Karagandy and Ekibastuz represent pre-1924 mining settlements with VP1, not later planned industrial cities. Karsakpay (province 1312) represents the documented 1913–1917 construction settlement, including a surviving 1915 engineer's house, not an copper smelter operating in 1928. Both candidate neighbouring provinces 1312 and 12177 belong to Ulytau (1085) in the approved coarse regional layout; two nonlinear fits select province 1312. This gives each of the 17 oblasts a marker without inventing a modern planned city. Kurchatov, Balkhash and modern planned Zhezkazgan are excluded. Shu was also excluded after research placed its railway-town development in 1928. Dense towns sharing a coarse province do not receive duplicate labels. Native Navoi is labelled Karmana for its nearby older settlement; this does not introduce the planned city founded in 1958.

Almaty (1591) and Tashkent (1459) remain explicit country-capital provinces. The chosen successor fixture capitals, rather than claimed historical native capitals, stay the highest-scoring VP within their state. Uzbekistan uses Samarkand (10671) in Bukhara state 830; native UZB history uses Tashkent (405), which the treaty retains for TRK. Karmana (1554) in state 585 is an ordinary existing marker, not an asserted Uzbek historical capital. The other successor fixtures use Ashgabat (12333), Bishkek (12583) and Dushanbe (1384). The world manifest's state membership and OOB deployment metadata are refreshed after regional subdivision, without relocating units or overwriting regional state-name localisation. Locale goes in localisation/replace for reliable native-name overrides.

CITY_MANIFEST.json contains individual coordinates, provenance, final effective states and output hashes. Applying requires a verified external backup, a closed game and the isolated branch. Static checks do not establish actual in-game marker quality; full restart/new-campaign inspection remains required.
'''
    p=ROOT/'docs/design_v0_3/CITY_SETUP.md';data=notes.encode('utf8')
    if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
    print('Cities generated; full restart/new campaign and geographic review required.')
def main():
    cli=argparse.ArgumentParser(description=__doc__);mode=cli.add_mutually_exclusive_group();mode.add_argument('--inspect',action='store_true');mode.add_argument('--prepare-backup');mode.add_argument('--apply',action='store_true');cli.add_argument('--backup-dir');args=cli.parse_args()
    if args.prepare_backup:prepare(args.prepare_backup)
    elif args.apply:
        if not args.backup_dir:cli.error('--apply requires --backup-dir')
        apply(args.backup_dir)
    else:
        outputs,report=plan();print(json.dumps({'mode':'READ_ONLY_NO_RUNTIME_WRITES','additional_markers':report['additional_markers'],'native_renames':report['native_renames'],'capital_safeguards':report['capital_safeguards'],'outputs':{rel:digest(data) for rel,data in outputs.items()}},indent=2))
if __name__=='__main__':main()
