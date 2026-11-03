"""Keep every effective land state inside one native strategic region.

SOURCE-only by default: --inspect/plan() construct bytes in memory, never write.
Apply AFTER user state edits, Kazakhstan oblasts and cities, before canal visuals.
Whole-state target = majority of installed-native strategic province counts;
ties choose the lowest existing strategic ID. Weather, terrain, names and IDs
are preserved. Water membership and Caspian strategic region70 are unchanged.
"""
from pathlib import Path
import argparse,collections,hashlib,json,re,subprocess,sys
from contentlib import ROOT
from build_v03_state_edits import block,mask,ps
from build_v03_kaz_regions import closed,backup_path
GAME=Path('C:/Hearts of Iron IV')
BRANCH='spike/caspian-navigation'
REPORT='docs/design_v0_3/STRATEGIC_REGIONS_MANIFEST.json'
BACKUP=Path('C:/Users/maqsatto/.codex/backups/ashes_of_empires/user-strategic-20261103')

def sha(data):return hashlib.sha256(data).hexdigest()
def text(data):return data.decode('utf-8-sig').replace('\r\n','\n')
def encode(s,original):return s.encode('utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf8')
def ident(s):
 m=re.search(r'\bid\s*=\s*(\d+)',mask(s))
 if not m:raise RuntimeError('Definition missing ID')
 return int(m[1])
def read(rel,overlay):
 if rel in overlay:return overlay[rel]
 p=ROOT/rel
 return p.read_bytes() if p.exists() else (GAME/rel).read_bytes()
def files(folder,overlay):
 paths={p.name:folder+'/'+p.name for p in (GAME/folder).glob('*.txt')}
 paths.update({p.name:folder+'/'+p.name for p in (ROOT/folder).glob('*.txt')})
 paths.update({Path(rel).name:rel for rel in overlay if rel.startswith(folder+'/') and rel.endswith('.txt')})
 return {rel:read(rel,overlay) for rel in sorted(paths.values())}
def province_map(regions):
 result={}
 for rid,entry in regions.items():
  for p in ps(text(entry['data'])):
   if p in result:raise RuntimeError('Province in multiple strategic regions '+str(p))
   result[p]=rid
 return result

def inventory(overlay=None):
 overlay=overlay or {};native={}
 for p in (GAME/'map/strategicregions').glob('*.txt'):
  data=p.read_bytes();rid=ident(text(data))
  if rid in native:raise RuntimeError('Native strategic ID duplicate '+str(rid))
  native[rid]={'rel':'map/strategicregions/'+p.name,'data':data}
 effective={}
 for rel,data in files('map/strategicregions',overlay).items():
  rid=ident(text(data))
  if rid not in native or rel!=native[rid]['rel']:raise RuntimeError('Unreviewed strategic ID/path '+rel)
  if rid in effective:raise RuntimeError('Effective strategic ID duplicate '+str(rid))
  effective[rid]={'rel':rel,'data':data}
 states={}
 for rel,data in files('history/states',overlay).items():
  sid=ident(text(data))
  if sid in states:raise RuntimeError('Effective state ID duplicate '+str(sid))
  states[sid]={'rel':rel,'data':data,'provinces':ps(text(data))}
 kinds={}
 for line in text((GAME/'map/definition.csv').read_bytes()).splitlines():
  row=line.split(';')
  if len(row)>=8 and row[0].isdigit():kinds[int(row[0])]=row[4]
 return native,effective,states,kinds

def plan(overlay=None):
 native,effective,states,kinds=inventory(overlay);original=province_map(native);current=province_map(effective)
 if set(original)!=set(current):raise RuntimeError('Effective strategic province universe differs from native')
 proposed={rid:set(ps(text(entry['data']))) for rid,entry in native.items()};decisions={};state_provinces={};moving=[]
 for sid,entry in sorted(states.items()):
  land=[]
  for p in entry['provinces']:
   if p in state_provinces:raise RuntimeError('Province belongs to multiple effective states '+str(p))
   state_provinces[p]=sid
   if p not in kinds or p not in original:raise RuntimeError('Unknown native province/strategic membership '+str(p))
   if kinds[p]=='land':land.append(p)
  if not land:continue
  votes=collections.Counter(original[p] for p in land);target=min(votes,key=lambda rid:(-votes[rid],rid));decisions[sid]={'target_region':target,'native_votes':dict(sorted(votes.items())),'land_province_count':len(land),'state_file':entry['rel']}
  for p in land:
   if original[p]!=target:
    proposed[original[p]].remove(p);proposed[target].add(p);moving.append({'province':p,'state':sid,'from_region':original[p],'to_region':target})
 output={};changed=[]
 for rid,entry in sorted(native.items()):
  native_ids=ps(text(entry['data']))
  if proposed[rid]==set(native_ids):continue
  base=effective[rid]['data'];s=text(base);_,a,b,_=block(s,'provinces');order=[p for p in native_ids if p in proposed[rid]]+sorted(proposed[rid]-set(native_ids));new=s[:a]+'\n\t\t'+' '.join(map(str,order))+'\n\t'+s[b:]
  # Verify all metadata outside the province-list body is byte-equivalent after
  # normalising original CRLF, including every weather and naval-terrain block.
  _,na,nb,_=block(new,'provinces')
  if s[:a]+s[b:]!=new[:na]+new[nb:]:raise RuntimeError('Unexpected strategic metadata change')
  output[entry['rel']]=encode(new,base);changed.append(rid)
 final={}
 for rid,members in proposed.items():
  for p in members:
   if p in final:raise RuntimeError('Final strategic province duplicate '+str(p))
   final[p]=rid
 if set(final)!=set(original):raise RuntimeError('Strategic province lost or added')
 water=[p for p in original if kinds[p]!='land']
 if any(final[p]!=original[p] for p in water):raise RuntimeError('Water province strategic region changed')
 if 70 in changed:raise RuntimeError('Caspian strategic region70 must remain untouched')
 for sid,entry in states.items():
  regions={final[p] for p in entry['provinces'] if kinds[p]=='land'}
  if len(regions)>1:raise RuntimeError('State still spans strategic regions '+str(sid))
 changed_states={str(s):v for s,v in decisions.items() if len(v['native_votes'])>1}
 report={'assignment_method':'Whole effective land state to majority of installed-native strategic membership by province count; ties lowest existing region ID','branch':BRANCH,'effective_state_count':len(states),'land_states_checked':len(decisions),'native_strategic_region_count':len(native),'global_strategic_province_count':len(final),'water_provinces_unchanged':len(water),'caspian_region70_unchanged':True,'changed_strategic_region_ids':changed,'changed_region_files':[native[r]['rel'] for r in changed],'changed_states':changed_states,'moved_provinces':moving,'state_to_strategic_region':{str(s):v['target_region'] for s,v in decisions.items()},'all_land_states_in_one_strategic_region':True,'province_uniqueness_preserved':True,'weather_and_other_metadata_preserved':True,'actual_game_test':'UNVERIFIED; cold restart/new campaign and fresh error.log required'}
 return output,report

def validate_effective(overlay=None):
 """Read-only hook for check_mod.py; raise on actual current effective spans."""
 native,effective,states,kinds=inventory(overlay);membership=province_map(effective);original=province_map(native);failures={};seen={}
 if set(membership)!=set(original):raise RuntimeError('Effective strategic province universe differs from native')
 for p,region in original.items():
  if kinds[p]!='land' and membership[p]!=region:raise RuntimeError('Water strategic membership changed '+str(p))
 for sid,entry in states.items():
  regions=set()
  for p in entry['provinces']:
   if p in seen:raise RuntimeError('Effective state province duplicate '+str(p))
   seen[p]=sid
   if p not in kinds or p not in membership:raise RuntimeError('Unknown effective province '+str(p))
   if kinds[p]=='land':regions.add(membership[p])
  if len(regions)>1:failures[sid]=sorted(regions)
 if failures:raise RuntimeError('Effective states span strategic regions: '+str(failures))
 return {'states_checked':len(states),'strategic_regions':len(effective),'global_provinces':len(membership)}

def prepare(value):
 commit=closed();base=backup_path(value)
 if base.exists() and any(base.iterdir()):raise RuntimeError('Use a new empty external backup; never overwrite prior backup')
 native,effective,states,kinds=inventory();out,report=plan();inputs={e['rel']:e['data'] for e in effective.values()};inputs.update({e['rel']:e['data'] for e in states.values()});inputs['map/definition.csv']=read('map/definition.csv',{})
 base.mkdir(parents=True,exist_ok=True)
 for rel,data in inputs.items():
  p=base/'inputs'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 prior={rel:sha((ROOT/rel).read_bytes()) if (ROOT/rel).exists() else None for rel in out}
 native_hash={e['rel']:sha(e['data']) for e in native.values()}
 for rid,e in native.items():
  p=base/'native'/e['rel'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(e['data'])
 manifest={'branch':BRANCH,'base_commit':commit,'workspace':str(ROOT.resolve()),'input_sha256':{r:sha(d) for r,d in inputs.items()},'native_strategic_sha256':native_hash,'prior_output_sha256':prior,'proposal':report}
 (base/'strategic_backup_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');print('External strategic backup prepared; no runtime outputs written:',base)

def apply(value):
 closed();base=backup_path(value);saved=json.loads((base/'strategic_backup_manifest.json').read_text(encoding='utf8'))
 if saved['branch']!=BRANCH or saved['workspace']!=str(ROOT.resolve()):raise RuntimeError('Backup branch/workspace mismatch')
 subprocess.run(['git','merge-base','--is-ancestor',saved['base_commit'],'HEAD'],cwd=ROOT,check=True)
 for rel,digest in saved['input_sha256'].items():
  if sha((base/'inputs'/rel).read_bytes())!=digest:raise RuntimeError('Damaged strategic backup input '+rel)
 for rel,digest in saved['native_strategic_sha256'].items():
  if sha((GAME/rel).read_bytes())!=digest or sha((base/'native'/rel).read_bytes())!=digest:raise RuntimeError('Installed strategic baseline changed '+rel)
 known=collections.defaultdict(set)
 for rel in [REPORT,'docs/design_v0_3/CITY_MANIFEST.json','docs/design_v0_3/KAZ_REGIONS_MANIFEST.json','docs/design_v0_3/USER_STATE_EDITS_MANIFEST.json','docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json']:
  p=ROOT/rel
  if p.exists():
   for path,digest in json.loads(p.read_text(encoding='utf8')).get('output_sha256',{}).items():known[path].add(digest.lower())
 native,effective,states,kinds=inventory()
 for entry in list(effective.values())+list(states.values()):
  rel=entry['rel'];digest=sha(entry['data'])
  if digest not in {saved['input_sha256'].get(rel),*known[rel]}:raise RuntimeError('Unreviewed strategic/state edit '+rel)
 if sha(read('map/definition.csv',{}))!=saved['input_sha256']['map/definition.csv']:raise RuntimeError('Map province classification changed after backup')
 out,report=plan()
 for rel,data in out.items():
  p=ROOT/rel;current=sha(p.read_bytes()) if p.exists() else None
  if current not in {saved['prior_output_sha256'].get(rel),*known[rel],sha(data)}:raise RuntimeError('Unreviewed strategic override '+rel)
 for rel,data in out.items():
  p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
 validate_effective()
 report.update({'backup_directory':str(base),'base_commit':saved['base_commit'],'input_sha256':saved['input_sha256'],'output_sha256':{r:sha(d) for r,d in out.items()}})
 for upstream,key in [('CASPIAN_SPIKE_MANIFEST.json','caspian'),('KAZ_REGIONS_MANIFEST.json','kaz_regions'),('CITY_MANIFEST.json','city')]:
  p=ROOT/'docs/design_v0_3'/upstream
  if p.exists():
   data=json.loads(p.read_text(encoding='utf8'));report['upstream_'+key+'_backup_directory']=data.get('backup_directory');report['upstream_'+key+'_base_commit']=data.get('base_commit')
 p=ROOT/REPORT;data=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8')
 if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
 print('Strategic membership outputs written; cold game verification remains UNVERIFIED.')

def main():
 sys.stdout.reconfigure(encoding='utf8');cli=argparse.ArgumentParser(description=__doc__);m=cli.add_mutually_exclusive_group();m.add_argument('--inspect',action='store_true');m.add_argument('--prepare-backup');m.add_argument('--apply',action='store_true');cli.add_argument('--backup-dir');a=cli.parse_args()
 if a.prepare_backup:prepare(a.prepare_backup)
 elif a.apply:
  if not a.backup_dir:cli.error('--apply requires --backup-dir')
  apply(a.backup_dir)
 else:
  out,report=plan();report['mode']='READ_ONLY_NO_RUNTIME_WRITES';report['proposed_output_sha256']={r:sha(d) for r,d in out.items()};print(json.dumps(report,indent=2))
if __name__=='__main__':main()
