"""Approximate modern Kazakhstan oblasts on unchanged native province geometry.

Default/--inspect builds a proposal IN MEMORY; no runtime files are written.
--prepare-backup ABSOLUTE_PATH snapshots effective upstream files with HOI4 closed.
--apply --backup-dir ABSOLUTE_PATH writes only after backup/branch/process checks.
Pipeline: world -> Caspian -> explicit six-province edits -> regions -> city VP stage.
The 17-oblast structure is an explicitly requested gameplay approximation, not
1924 canon or a claim of GIS-accurate modern borders. Three extra authorised KAZ
states 236/582/652 remain outside the oblast subdivision and byte-unchanged.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math,re,subprocess,sys
import numpy as np
from PIL import Image
from map_model_sampling import province_at_model,validate_engine_observations,validate_required_sites,STATE_SITE_TYPES,NORMAL_MODEL_TYPES
from contentlib import ROOT,q
from build_v03_state_edits import block,mask,ps,detach_attachments,attach
GAME=Path('C:/Hearts of Iron IV')
BRANCH='spike/caspian-navigation'
BODY=(402,404,406,407,583,586,587,588,589,590,881,882)
NEW=(1082,1083,1084,1085,1086)
EXTRAS=(236,582,652)
REPORT='docs/design_v0_3/KAZ_REGIONS_MANIFEST.json'
WORLD='docs/design_v0_3/WORLD_MANIFEST.json'
MODEL='map/buildings.txt'
SOURCES=[
 'https://www.gov.kz/article/19305?lang=kk',
 'https://stat.gov.kz/ru/industries/socialstatistics/demography/publications/335820/',
 'https://www.gov.kz/uploads/2025/12/29/28d1a632f23ee3e9f8c7e5c949910735_original.10102332.pdf',
 'https://primeminister.kz/assets/media/prilozhenie-rus_113.pdf',
]
NAMES={402:('Актобинская область','Aktobe Oblast'),404:('Акмешитская область','Akmeshit Oblast'),406:('Атырауская область','Atyrau Oblast'),407:('Западно-Казахстанская область','West Kazakhstan Oblast'),583:('Костанайская область','Kostanay Oblast'),586:('Алматинская область','Almaty Oblast'),587:('Мангистауская область','Mangystau Oblast'),588:('Абайская область','Abay Oblast'),589:('Восточно-Казахстанская область','East Kazakhstan Oblast'),590:('Акмолинская область','Akmola Oblast'),881:('Карагандинская область','Karaganda Oblast'),882:('Керекуская область','Kereku Oblast'),1082:('Северо-Казахстанская область','North Kazakhstan Oblast'),1083:('Жамбылская область','Zhambyl Oblast'),1084:('Жетысуская область','Zhetysu Oblast'),1085:('Улытауская область','Ulytau Oblast'),1086:('Туркестанская область','Turkestan Oblast')}
# Author-traced coarse oblast outlines in the 1800x1274 rendering of page4 of
# the official Astana Akimat/Astanagenplan2025 general-plan PDF. No third-party
# artwork or vector data is included in game assets. Borders are snapped to whole
# native HOI4 provinces, NEVER painted into provinces.bmp.
POLYGONS={
407:[(130,328),(165,223),(242,195),(341,178),(359,213),(449,234),(456,285),(443,374),(330,353),(258,387),(170,354)],
406:[(170,354),(258,387),(330,353),(443,374),(454,420),(410,466),(416,512),(370,552),(300,552),(300,476),(220,463),(185,439)],
402:[(449,234),(600,306),(708,289),(714,247),(786,278),(797,344),(750,380),(797,445),(751,500),(706,520),(648,573),(493,600),(489,537),(460,518),(446,472),(414,466),(454,420),(443,374),(456,285)],
587:[(220,554),(285,554),(318,568),(369,552),(410,513),(460,520),(493,600),(457,662),(429,828),(329,760),(245,683)],
583:[(727,109),(903,87),(918,145),(911,225),(941,273),(944,321),(912,337),(959,380),(930,435),(836,480),(797,445),(750,380),(797,344),(786,278),(714,247),(683,242),(715,210)],
1082:[(903,87),(978,67),(1061,70),(1087,113),(1176,128),(1153,160),(1072,160),(1040,143),(969,155),(932,195),(918,145)],
590:[(932,195),(969,155),(1040,143),(1072,160),(1094,181),(1114,217),(1176,215),(1202,267),(1167,302),(1152,322),(1090,351),(1020,335),(979,332),(944,321),(941,273),(911,225)],
882:[(1176,128),(1225,93),(1254,130),(1340,131),(1398,253),(1371,272),(1366,303),(1298,309),(1251,339),(1204,330),(1167,302),(1202,267),(1176,215),(1153,160)],
881:[(944,321),(979,332),(1020,335),(1090,351),(1152,322),(1204,330),(1251,339),(1298,309),(1335,349),(1320,422),(1327,466),(1290,508),(1218,511),(1200,566),(1122,594),(1129,545),(1120,493),(1125,464),(1045,448),(991,462),(958,438),(930,435),(959,380),(912,337)],
1085:[(836,480),(930,435),(958,438),(991,462),(1045,448),(1125,464),(1120,493),(1129,545),(1122,594),(929,598),(903,558),(874,549),(815,538),(797,445)],
404:[(706,520),(751,500),(836,480),(815,538),(874,549),(903,558),(929,598),(944,640),(941,689),(897,735),(881,792),(855,800),(804,751),(724,735),(677,672),(652,617),(648,573)],
1086:[(929,598),(1037,598),(1037,650),(1040,715),(997,733),(975,761),(1000,808),(1005,861),(976,904),(947,900),(932,855),(882,832),(881,792),(897,735),(941,689),(944,640)],
1083:[(1037,598),(1198,594),(1198,644),(1200,708),(1230,746),(1251,772),(1190,797),(1116,801),(1040,786),(1000,808),(975,761),(997,733),(1040,715),(1037,650)],
586:[(1198,594),(1298,577),(1312,627),(1340,667),(1382,683),(1430,673),(1479,676),(1510,722),(1493,778),(1393,774),(1365,787),(1315,759),(1251,772),(1230,746),(1200,708)],
1084:[(1290,508),(1327,466),(1372,477),(1410,498),(1482,508),(1527,519),(1557,559),(1572,595),(1542,623),(1510,641),(1479,676),(1430,673),(1382,683),(1340,667),(1312,627),(1298,577),(1218,511)],
588:[(1398,253),(1450,265),(1493,276),(1512,293),(1502,352),(1530,382),(1570,407),(1592,463),(1575,505),(1527,519),(1482,508),(1410,498),(1372,477),(1327,466),(1320,422),(1335,349),(1298,309),(1366,303),(1371,272)],
589:[(1512,293),(1552,297),(1599,316),(1649,304),(1680,329),(1711,337),(1706,389),(1670,415),(1680,458),(1640,469),(1575,505),(1592,463),(1570,407),(1530,382),(1502,352)],
}
# Exact native named-city VP anchors matched visually to the official map. A
# thin-plate interpolation corrects HOI4's distorted projection locally. It is
# authoring guidance only, not a geodetic transform or a source of new VP IDs.
ANCHORS={7341:(560,310),3618:(320,454),11537:(355,211),7597:(860,658),1591:(1364,742),12594:(1434,307),1668:(1463,449),10312:(842,153),4333:(1097,290),7708:(1297,208)}
LOCKED={7341:402,3618:406,11537:407,7597:404,1591:586,12594:588,1668:588,10312:583,4333:590,7708:882,1517:587,11457:407,7298:590,4845:1084,12397:404,1680:590,7407:881,10161:881}

def sha(b):return hashlib.sha256(b).hexdigest()
def effective(rel):
 p=ROOT/rel;return p.read_bytes() if p.exists() else (GAME/rel).read_bytes()
def text(b):return b.decode('utf-8-sig').replace('\r\n','\n')
def scalar(s,key,default=None):
 m=re.search(r'(?m)^\s*'+re.escape(key)+r'\s*=\s*([^\s#{}]+)',mask(s));return m[1] if m else default
def inventory():
 inv={};nativeids=[]
 for p in (GAME/'history/states').glob('*.txt'):
  s=p.read_text(encoding='utf-8-sig');sid=int(scalar(s,'id'));nativeids.append(sid);inv[sid]={'rel':'history/states/'+p.name,'native':s}
 if max(nativeids)!=1081 or set(NEW)&set(nativeids):raise RuntimeError('Installed state-ID audit changed; allocate explicitly after reinspection')
 observed={}
 for p in (ROOT/'history/states').glob('*.txt'):
  sid=int(scalar(p.read_text(encoding='utf-8-sig'),'id'));rel='history/states/'+p.name
  if sid in observed:raise RuntimeError('Duplicate mod state ID '+str(sid))
  observed[sid]=rel
  if sid not in inv and sid not in NEW:raise RuntimeError('Unreviewed custom state-ID allocation '+str(sid))
  expected=inv[sid]['rel'] if sid in inv else f'history/states/{sid}-AOF-KAZ-{sid}.txt'
  if rel!=expected:raise RuntimeError('State-ID/file-path collision '+str(sid)+': '+rel)
 for sid in NEW:inv[sid]={'rel':f'history/states/{sid}-AOF-KAZ-{sid}.txt','native':None}
 return inv

def phi(r):
 a=np.zeros_like(r);ok=r>0;a[ok]=r[ok]**2*np.log(r[ok]);return a

def interpolate(centroids):
 units={}
 for line in (GAME/'map/unitstacks.txt').read_text().splitlines():
  p=line.split(';')
  if len(p)==7 and p[0].isdigit() and p[1]=='0':units[int(p[0])]=(float(p[2]),2048-float(p[4]))
 keys=list(ANCHORS);x=np.array([units.get(k,centroids[k]) for k in keys])/1000.;y=np.array([ANCHORS[k] for k in keys]);n=len(keys)
 d=np.sqrt(((x[:,None,:]-x[None,:,:])**2).sum(2));p=np.column_stack([np.ones(n),x]);a=np.block([[phi(d),p],[p.T,np.zeros((3,3))]])
 coeff=np.linalg.solve(a,np.vstack([y,np.zeros((3,2))]))
 def transform(points):
  z=np.array(points)/1000.;dd=np.sqrt(((z[:,None,:]-x[None,:,:])**2).sum(2));return np.column_stack([phi(dd),np.ones(len(z)),z])@coeff
 return transform,{'method':'author-traced official schematic + exact native city anchor thin-plate warp; nearest whole-province assignment, not GIS boundaries','source_image_page':4,'source_image_render_size':[1800,1274],'anchors':{str(k):{'native_map_xy':list(units.get(k,centroids[k])),'official_reference_xy':ANCHORS[k]} for k in keys}}

def inside(point,polygon):
 x,y=point;v=False
 for (x1,y1),(x2,y2) in zip(polygon,polygon[1:]+polygon[:1]):
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:v=not v
 return v

def distance(point,polygon):
 p=np.array(point);best=float('inf')
 for aa,bb in zip(polygon,polygon[1:]+polygon[:1]):
  a=np.array(aa);b=np.array(bb);d=b-a;t=max(0,min(1,float(np.dot(p-a,d)/np.dot(d,d))));best=min(best,float(np.dot(p-a-t*d,p-a-t*d)))
 return best

def geography(inv):
 definitions={}
 for line in (GAME/'map/definition.csv').read_text(encoding='utf-8-sig').splitlines():
  p=line.split(';')
  if len(p)>=8 and p[0].isdigit():definitions[int(p[0])]=tuple(map(int,p[1:4]))
 body={p for sid in BODY for p in ps(inv[sid]['native'])};image=np.asarray(Image.open(GAME/'map/provinces.bmp').convert('RGB'));crop=image[350:900,3400:4400]
 centers={};areas={}
 for p in sorted(body):
  ys,xs=np.where(np.all(crop==definitions[p],axis=2))
  if not len(xs):raise RuntimeError('Expected Kazakhstan province absent from verified crop '+str(p))
  centers[p]=(float(xs.mean()+3400),float(ys.mean()+350));areas[p]=len(xs)
 warp,reference=interpolate(centers);keys=sorted(body);projected=dict(zip(keys,warp([centers[k] for k in keys])))
 assignment={};ambiguous=[]
 for p in keys:
  hits=[s for s,poly in POLYGONS.items() if inside(projected[p],poly)]
  target=min(hits) if hits else min(POLYGONS,key=lambda s:(distance(projected[p],POLYGONS[s]),s))
  if len(hits)!=1:ambiguous.append({'province':p,'reference_xy':list(projected[p]),'polygon_hits':hits,'assigned':target})
  assignment[p]=LOCKED.get(p,target)
 # Physical province adjacency for a separate, explicit topology audit.
 rgbids={v:k for k,v in definitions.items()};unique,idx=np.unique(crop.reshape(-1,3),axis=0,return_inverse=True);ids=np.array([rgbids[tuple(map(int,c))] for c in unique]);grid=ids[idx].reshape(crop.shape[:2]);edges=np.concatenate([np.stack([grid[:,:-1].ravel(),grid[:,1:].ravel()],1),np.stack([grid[:-1,:].ravel(),grid[1:,:].ravel()],1)]);edges=np.unique(np.sort(edges,axis=1),axis=0)
 adj=collections.defaultdict(set)
 for a,b in edges:
  if a!=b and a in body and b in body:adj[int(a)].add(int(b));adj[int(b)].add(int(a))
 def components(sid):
  left={p for p,s in assignment.items() if s==sid};result=[]
  while left:
   seed=min(left);seen={seed};todo=[seed];left.remove(seed)
   while todo:
    for v in adj[todo.pop()]&left:left.remove(v);seen.add(v);todo.append(v)
   result.append(sorted(seen))
  return result
 topology={str(s):components(s) for s in sorted(NAMES)}
 return assignment,areas,reference,ambiguous,topology,image,definitions


def closed():
 if sys.platform!='win32':raise RuntimeError('Native Windows process check required')
 r=subprocess.run(['tasklist','/FI','IMAGENAME eq hoi4.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=True)
 if 'hoi4.exe' in r.stdout.lower():raise RuntimeError('HOI4 is running; region backup/apply is prohibited')
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
 if branch!=BRANCH:raise RuntimeError('Use isolated map branch '+BRANCH)
 return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def backup_path(value):
 p=Path(value)
 if not p.is_absolute():raise RuntimeError('Explicit absolute external backup directory required')
 p=p.resolve()
 if p==Path(p.anchor) or p.is_relative_to(ROOT.resolve()) or p.is_relative_to(GAME.resolve()):raise RuntimeError('Backup must be outside workspace/game and not a drive root')
 return p

def inspect():
 outputs,report=plan()
 report.update({'mode':'READ_ONLY_PROPOSAL_NO_RUNTIME_WRITES','planned_output_sha256':{rel:sha(data) for rel,data in outputs.items()}})
 print(json.dumps(report,ensure_ascii=False,indent=2));return report


def replace_block(s,key,body):
 try:_,a,b,_=block(s,key);return s[:a]+body+s[b:]
 except AssertionError:
  _,a,_,_=block(s,'state');return s[:a]+'\n'+str(key)+' = { '+body+' }\n'+s[a:]

def replace_number(s,key,value):
 pattern=r'(?m)^(\s*)'+re.escape(key)+r'\s*=\s*[-\d.]+'
 if re.search(pattern,mask(s)):return re.sub(pattern,lambda m:m[1]+key+' = '+str(value),s,count=1)
 _,a,_,_=block(s,'state');return s[:a]+'\n'+key+' = '+str(value)+'\n'+s[a:]

def allocate(total,weights):
 """Largest remainder; integer native populations/resource totals stay exact."""
 total=int(total);den=sum(weights.values());raw={s:total*w/den for s,w in weights.items()};out={s:int(v) for s,v in raw.items()}
 for sid in sorted(raw,key=lambda sid:(-(raw[sid]-out[sid]),sid))[:total-sum(out.values())]:out[sid]+=1
 assert sum(out.values())==total
 return out

def resources(s):
 try:_,a,b,_=block(s,'resources')
 except AssertionError:return {}
 return {k:float(v) for k,v in re.findall(r'(\w+)\s*=\s*([\d.]+)',mask(s[a:b]))}

def buildings(s):
 _,ha,hb,_=block(s,'history');h=s[ha:hb];_,a,b,_=block(h,'buildings');body=h[a:b]
 for m in list(re.finditer(r'(?<!\w)\d+\s*=\s*\{',mask(body)))[::-1]:
  ident=re.search(r'\d+',m[0])[0];start,_,_,end=block(body[m.start():],ident);body=body[:m.start()+start]+body[m.start()+end:]
 return {k:float(v) for k,v in re.findall(r'(\w+)\s*=\s*([\d.]+)',mask(body))}

def known_outputs():
 known=collections.defaultdict(set)
 for rel in [REPORT,'docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json','docs/design_v0_3/USER_STATE_EDITS_MANIFEST.json','docs/design_v0_3/CITIES_MANIFEST.json','docs/design_v0_3/CITY_NAMES_MANIFEST.json','docs/design_v0_3/CITY_MANIFEST.json']:
  p=ROOT/rel
  if p.exists():
   data=json.loads(p.read_text(encoding='utf-8-sig'))
   for path,value in data.get('output_sha256',{}).items():known[path].add(value.lower())
 return known

def prepare(value):
 commit=closed();base=backup_path(value);inv=inventory();known=known_outputs()
 if base.exists() and any(base.iterdir()):raise RuntimeError('Preserve existing backup; choose a new empty external directory')
 inputs={inv[s]['rel']:effective(inv[s]['rel']) for s in BODY}
 for sid in BODY:
  data=inputs[inv[sid]['rel']]
  if set(ps(text(data)))!=set(ps(inv[sid]['native'])):raise RuntimeError('Prepare after world generation, before first region subdivision; body province baseline differs '+str(sid))
  if scalar(text(data),'owner')!='KAZ':raise RuntimeError('Non-KAZ body state '+str(sid))
 paths=[inv[s]['rel'] for s in NAMES]+[MODEL,WORLD,'localisation/russian/aof_v03_kaz_regions_l_russian.yml','localisation/english/aof_v03_kaz_regions_l_english.yml']
 prior={}
 for rel in paths:
  p=ROOT/rel;prior[rel]=sha(p.read_bytes()) if p.exists() else None
  if rel in [inv[s]['rel'] for s in NEW] and p.exists() and prior[rel] not in known[rel]:raise RuntimeError('Unrecognised custom state collision '+rel)
 inputs.update({MODEL:effective(MODEL),WORLD:effective(WORLD)})
 fixed={r:sha(effective(r)) for r in ['map/provinces.bmp','map/definition.csv','map/railways.txt','map/supply_nodes.txt']}
 extras={inv[s]['rel']:sha(effective(inv[s]['rel'])) for s in EXTRAS}
 base.mkdir(parents=True,exist_ok=True)
 for rel,data in inputs.items():
  p=base/'inputs'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 manifest={'branch':BRANCH,'base_commit':commit,'workspace':str(ROOT.resolve()),'input_sha256':{r:sha(d) for r,d in inputs.items()},'prior_output_sha256':prior,'immutable_sha256':fixed,'outside_state_sha256':extras,'native_body_sha256':{inv[s]['rel']:sha((GAME/inv[s]['rel']).read_bytes()) for s in BODY}}
 (base/'kaz_regions_backup_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
 print('External region backup prepared; no mod runtime outputs written:',base)

def ensure_state_sites(rows,image,defs,membership,groups,areas,vp):
 """Append missing native state-level visual sites, never building levels."""
 rgb={v:k for k,v in defs.items()};native=(GAME/'map/buildings.txt').read_bytes()
 templates=collections.defaultdict(list)
 for number,line in enumerate(text(native).splitlines(),1):
  row=line.split(';')
  if len(row)==7 and row[1] in STATE_SITE_TYPES:templates[row[1]].append((number,row))
 for kind in STATE_SITE_TYPES:
  if len({int(row[0]) for _,row in templates[kind]})!=1081:raise RuntimeError('Native state-site schema changed: '+kind)
 # Both gun emplacement and rockets use the same real spawn-point class.
 schema=(GAME/'common/buildings/00_buildings.txt').read_text(encoding='utf-8-sig')
 _,ga,gb,_=block(schema,'mega_gun_emplacement')
 if 'spawn_point = rocket_site_spawn' not in schema[ga:gb]:raise RuntimeError('Native gun-emplacement spawn class changed')
 valid={s:set() for s in groups};occupied=collections.defaultdict(list)
 for line in rows:
  r=line.split(';')
  if len(r)!=7 or not r[0].isdigit():continue
  s=int(r[0]);p=province_at_model(image,rgb,r[2],r[4])
  if membership.get(p)!=s:continue
  if s in valid:valid[s].add(r[1])
  if r[1]!='floating_harbor':occupied[p].append((float(r[2]),image.shape[0]-float(r[4])))
 units={}
 for line in (GAME/'map/unitstacks.txt').read_text().splitlines():
  r=line.split(';')
  if len(r)==7 and r[0].isdigit() and r[1]=='0':units[int(r[0])]=(float(r[2]),image.shape[0]-float(r[4]))
 # A few installed land provinces have no slot0 unitstack. Use their actual
 # bitmap centroid as authoring guidance; final sites still require a verified
 # five-by-five interior and exact state/province sampling.
 for province in (p for members in groups.values() for p in members):
  if province not in units:
   yy,xx=np.where(np.all(image[350:900,3400:4400]==defs[province],axis=2))
   if not len(xx):raise RuntimeError('No land pixels for site-anchor province '+str(province))
   units[province]=(float(xx.mean()+3400),float(yy.mean()+350))
 heights_raw=(GAME/'map/heightmap.bmp').read_bytes();heightmap=np.asarray(Image.open(GAME/'map/heightmap.bmp'))
 if heightmap.shape!=image.shape[:2]:raise RuntimeError('Native terrain-height dimensions differ')
 # The native height units were checked against local unitstack/model anchors:
 # terrain98 -> modelY9.80, terrain104 ->10.40, terrain106 ->10.60.
 for p in (7341,7874,10619):
  x,y=units[p];px=math.floor(x);py=image.shape[0]-1-math.floor(image.shape[0]-y)
  if not (0<=px<image.shape[1] and 0<=py<image.shape[0]):raise RuntimeError('Native site-height reference outside map')
 crop=image[350:900,3400:4400];interiors={};native_inventory=inventory();native_state={p:s for s in BODY for p in ps(native_inventory[s]['native'])}
 def pixels(province):
  if province not in interiors:
   m=np.all(crop==defs[province],axis=2);pad=np.pad(m,2,constant_values=False);inside=m.copy()
   for dy in range(5):
    for dx in range(5):inside &= pad[dy:dy+m.shape[0],dx:dx+m.shape[1]]
   yy,xx=np.where(inside);interiors[province]=list(zip((xx+3400).tolist(),(yy+350).tolist()))
  return interiors[province]
 added=[]
 for sid in sorted(groups):
  missing=[kind for kind in STATE_SITE_TYPES if kind not in valid[sid]]
  if not missing:continue
  center=(sum(units[p][0]*areas[p] for p in groups[sid])/sum(areas[p] for p in groups[sid]),sum(units[p][1]*areas[p] for p in groups[sid])/sum(areas[p] for p in groups[sid]))
  ranked=sorted(groups[sid],key=lambda p:((units[p][0]-center[0])**2+(units[p][1]-center[1])**2,p))
  scored=[]
  for p in groups[sid]:
   for point in vp.get(p,[]):
    numbers=re.findall(r'\d+(?:\.\d+)?',point)
    scored.extend((float(numbers[i+1]),p) for i in range(0,len(numbers),2))
  if scored:
   anchor=max(scored,key=lambda pair:(pair[0],-pair[1]))[1];ranked=[anchor]+[p for p in ranked if p!=anchor]
  for kind in missing:
   chosen=None
   for province in ranked:
    anchor=units[province]
    candidates=sorted(pixels(province),key=lambda xy:((xy[0]+.5-anchor[0])**2+(xy[1]+.5-anchor[1])**2,xy))
    for x,y in candidates:
     if all((x+.5-ox)**2+(y+.5-oy)**2>=9 for ox,oy in occupied[province]):chosen=(province,x,y);break
    if chosen:break
   if not chosen:raise RuntimeError('No separated interior land pixel for model site '+str(sid)+'/'+kind)
   province,x,y=chosen;mx,mz=x+.5,image.shape[0]-y-.5
   if province_at_model(image,rgb,mx,mz)!=province or membership[province]!=sid:raise RuntimeError('New site is not in its final state')
   candidates=templates[kind];reference=next(((n,r) for n,r in candidates if int(r[0])==native_state[province]),candidates[0]);refline,template=reference
   elevation=float(heightmap[y,x])/10.;row=f'{sid};{kind};{mx:.2f};{elevation:.2f};{mz:.2f};{template[5]};{template[6]}'
   rows.append(row);occupied[province].append((mx,y+.5));valid[sid].add(kind)
   added.append({'row':len(rows),'state':sid,'type':kind,'province':province,'map_xz':[mx,mz],'image_pixel':[x,y],'interior_clearance_pixels':2,'height':elevation,'native_heightmap_value':int(heightmap[y,x]),'native_rotation':template[5],'native_template_line':refline,'native_template_state':int(template[0]),'building_level_added':0,'anchor':'native VP province then native unitstack0 where present; otherwise verified bitmap centroid nearest area-weighted state centre'})
 coverage=validate_required_sites(rows,image,rgb,membership,groups,STATE_SITE_TYPES)
 normal=validate_required_sites(rows,image,rgb,membership,groups,NORMAL_MODEL_TYPES)
 return {'added_count':len(added),'added_rows':added,'required_native_state_site_types':list(STATE_SITE_TYPES),'rocket_and_gun_share':'rocket_site_spawn','coverage':coverage,'normal_model_coverage':normal,'actual_building_levels_added':0,'native_heightmap_sha256':sha(heights_raw),'height_method':'native terrain byte /10; close local native height references inspected; visual elevation still requires game review'}


def build(inputs):
 inv=inventory();assignment,areas,reference,ambiguous,topology,image,defs=geography(inv)
 if any(len(v)!=1 for v in topology.values()):raise RuntimeError('Disconnected/empty oblast proposal; inspect before apply '+str({s:v for s,v in topology.items() if len(v)!=1}))
 groups={s:sorted(p for p,t in assignment.items() if t==s) for s in NAMES}
 if assignment[1591]!=586 or assignment[1517]!=587:raise RuntimeError('Capital or dedicated Caspian base moved unexpectedly')
 source={s:text(inputs[inv[s]['rel']]) for s in BODY};stripped={};vp={};provbuild={};pop=collections.Counter();res=collections.defaultdict(collections.Counter);infra=collections.defaultdict(list)
 before_pop=0;before_resources=collections.Counter();before_factories=collections.Counter()
 for sid,s in source.items():
  if set(ps(s))!=set(ps(inv[sid]['native'])) or scalar(s,'owner')!='KAZ':raise RuntimeError('Body source membership/ownership changed '+str(sid))
  if re.search(r'\b\d{4}\.\d+\.\d+\s*=\s*\{',mask(s)):raise RuntimeError('Future-dated body history must be removed by world stage')
  weights=collections.Counter()
  for p in ps(s):weights[assignment[p]]+=areas[p]
  population=int(scalar(s,'manpower','0'));before_pop+=population
  for target,n in allocate(population,weights).items():pop[target]+=n
  for key,value in resources(s).items():
   if not value.is_integer():raise RuntimeError('Fractional native resource needs explicit allocation review '+key)
   before_resources[key]+=int(value)
   for target,n in allocate(int(value),weights).items():res[target][key]+=n
  sb=buildings(s)
  for key in ['industrial_complex','arms_factory','dockyard']:before_factories[key]+=sb.get(key,0)
  for target,weight in weights.items():infra[target].append((sb.get('infrastructure',1),weight))
  current=s
  for p in ps(s):
   current,points,pbuild=detach_attachments(current,p)
   if points:vp[p]=points
   if pbuild:provbuild[p]=pbuild
  stripped[sid]=current
 outputs={};after_factories=collections.Counter()
 for sid in sorted(NAMES):
  if sid in BODY:s=stripped[sid]
  else:
   infrastructure=round(sum(v*w for v,w in infra[sid])/sum(w for v,w in infra[sid]))
   s=f'state = {{\n id = {sid}\n name = "aof_kaz_region_{sid}"\n manpower = 0\n state_category = pastoral\n resources = {{ }}\n history = {{ owner = KAZ controller = KAZ add_core_of = KAZ add_core_of = SOV buildings = {{ infrastructure = {infrastructure} }} }}\n provinces = {{ }}\n local_supplies = 0.0\n}}\n'
  s=replace_block(s,'provinces','\n '+' '.join(map(str,groups[sid]))+'\n ')
  s=replace_number(s,'manpower',pop[sid]);s=replace_block(s,'resources','\n '+' '.join(k+' = '+str(v) for k,v in sorted(res[sid].items()) if v)+'\n ')
  s=re.sub(r'\bname\s*=\s*"[^"]*"',f'name = "aof_kaz_region_{sid}"',s,count=1)
  points=[entry for p in groups[sid] for entry in vp.get(p,[])];attachments='\n'.join(provbuild[p] for p in groups[sid] if p in provbuild)
  s=attach(s,points,attachments or None)
  if set(ps(s))!=set(groups[sid]):raise RuntimeError('State province output mismatch')
  for key in ['industrial_complex','arms_factory','dockyard']:after_factories[key]+=buildings(s).get(key,0)
  outputs[inv[sid]['rel']]=('# Approximate owner-requested oblast, native province geometry unchanged.\n'+s).encode('utf8')
 if sum(pop.values())!=before_pop or sum(res.values(),collections.Counter())!=before_resources or before_factories!=after_factories:raise RuntimeError('Population/resources/shared factory conservation failed')
 # Validate the final composed state inventory, replacing our known five old
 # custom files rather than treating transitional rebuild duplicates as foreign.
 membership={}
 for sid,entry in inv.items():
  data=outputs.get(entry['rel'])
  if data is None:data=inputs.get(entry['rel'])
  if data is None:data=effective(entry['rel'])
  for province in ps(text(data)):
   if province in membership:raise RuntimeError('Final composed duplicate province '+str(province)+' in '+str(membership[province])+'/'+str(sid))
   membership[province]=sid
 # Observed engine sampling is floor(X), H-1-floor(Z). At integer Z the
 # former floor(H-Z) looked one pixel south; centred +.5 ports are unchanged.
 # Restrict repairs to the owner-authorised oblast/six-province footprint.
 rgb={v:k for k,v in defs.items()};modelrows=text(inputs[MODEL]).splitlines();reindexed=[]
 observation_count=validate_engine_observations(image,rgb)
 user_moves={4265,10185,1334,3265,4324,227}
 affected_states=set(BODY)|set(NEW)|{236,251,573,582,651,652}
 unrelated=[];floating_mismatches=[]
 for i,line in enumerate(modelrows):
  row=line.split(';')
  if len(row)<7 or not row[0].isdigit():continue
  province=province_at_model(image,rgb,row[2],row[4]);target=membership.get(province)
  if target is None or int(row[0])==target:continue
  entry={'line':i+1,'province':province,'from_state':int(row[0]),'to_state':target,'type':row[1]}
  if row[1]=='floating_harbor':
   # Native floating-harbour storage/placeholder positions can deliberately sit
   # outside their listed state. They produced no observed engine error here.
   floating_mismatches.append(entry);continue
  if int(row[0]) not in affected_states and province not in assignment and province not in user_moves:
   unrelated.append(entry);continue
  row[0]=str(target);modelrows[i]=';'.join(row);reindexed.append(entry)
 # Meaningful postcondition on every affected physical row, using the same
 # sampling that reproduced all nine actual engine province reports.
 for i,line in enumerate(modelrows):
  row=line.split(';')
  if len(row)<7 or not row[0].isdigit() or row[1]=='floating_harbor':continue
  province=province_at_model(image,rgb,row[2],row[4]);target=membership.get(province)
  relevant=int(row[0]) in affected_states or province in assignment or province in user_moves
  if relevant and target is not None and int(row[0])!=target:raise RuntimeError('Affected model still has wrong state at row '+str(i+1))
 site_report=ensure_state_sites(modelrows,image,defs,membership,groups,areas,vp)
 outputs[MODEL]='\n'.join(modelrows).encode('utf8') # NO terminal blank record
 world=json.loads(text(inputs[WORLD]));all_members={p:s for s,data in world['states'].items() for p in data.get('provinces',[]) if p not in assignment};all_members.update(assignment)
 for sid in sorted(NAMES):
  points=[]
  for p in groups[sid]:
   for entry in vp.get(p,[]):
    ns=re.findall(r'\d+(?:\.\d+)?',entry);points.extend([[int(ns[i]),float(ns[i+1])] for i in range(0,len(ns),2)])
  entry=world['states'].setdefault(str(sid),{})
  entry.update({'name_key':'aof_kaz_region_'+str(sid),'installed_name':NAMES[sid][1] if sid in NEW else entry.get('installed_name',NAMES[sid][1]),'fixture_owner':'KAZ','source_file':Path(inv[sid]['rel']).name,'provinces':groups[sid],'victory_points':points,'explicit_custom_state':sid in NEW,'region_reference_status':'Approximate modern oblast snapped to existing provinces, not 1924 canon'})
 country=world['countries']['KAZ'];country['states']=sorted(set(country['states'])|set(NEW));country['capital_state']=586;country['capital_province']=1591
 for tag,country in world['countries'].items():
  for deployment in country.get('deployment',[]):
   if deployment['province'] in assignment:
    if tag!='KAZ':raise RuntimeError('Non-KAZ OOB uses an oblast province '+tag)
    deployment['state']=assignment[deployment['province']]
 world['kazakhstan_oblasts']={'states':sorted(NAMES),'outside_authorised_states_unchanged':list(EXTRAS),'custom_ids_registered':list(NEW),'province_geometry_unchanged':True,'official_reference_sources':SOURCES}
 outputs[WORLD]=(json.dumps(world,ensure_ascii=False,indent=2)+'\n').encode('utf8')
 for lang,index in [('russian',0),('english',1)]:outputs[f'localisation/{lang}/aof_v03_kaz_regions_l_{lang}.yml']=(f'l_{lang}:\n'+''.join(' aof_kaz_region_'+str(s)+': '+q(NAMES[s][index])+'\n' for s in sorted(NAMES))).encode('utf-8-sig')
 report={'source_native_max_state_id':1081,'custom_state_ids':list(NEW),'id_audit':{'installed_max':1081,'installed_count':1081,'new_ids_contiguous_after_installed_max':True,'custom_definitions':{str(s):inv[s]['rel'] for s in NEW},'not_assumed_native_ids':True},'official_sources':SOURCES,'reference':reference,'ambiguous_snapping':ambiguous,'region_connected_components':topology,'province_to_state':{str(p):s for p,s in sorted(assignment.items())},'regions':{str(s):{'name':NAMES[s][0],'file':inv[s]['rel'],'provinces':groups[s],'manpower':pop[s],'resources':dict(res[s])} for s in sorted(NAMES)},'conservation':{'manpower_before_after':[before_pop,sum(pop.values())],'resources_before_after':[dict(before_resources),dict(sum(res.values(),collections.Counter()))],'factories_before_after':[dict(before_factories),dict(after_factories)]},'capital_preserved':{'state':586,'province':1591},'dedicated_port_preserved':{'state':587,'province':1517},'outside_states_unchanged':list(EXTRAS),'no_TRK_transfer':True,'model_state_reindex':reindexed,'state_model_sites':site_report,'model_sampling':{'formula':'x=floor(X); image_y=H-1-floor(Z)','actual_engine_observations_matched':observation_count,'floating_harbor_mismatches_preserved':floating_mismatches,'unrelated_mismatches_preserved':unrelated},'map_model_coordinates_unchanged':True,'transport_geometry_unchanged':True,'actual_game_test':'UNVERIFIED; full restart and new campaign required'}
 return outputs,report

def plan(overlay=None):
 """Compose with upstream in-memory outputs; never write runtime files."""
 inv=inventory();overlay=overlay or {};paths=[inv[s]['rel'] for s in BODY]+[MODEL,WORLD]
 inputs=dict(overlay)
 for rel in paths:
  if rel not in inputs:inputs[rel]=effective(rel)
 return build(inputs)

def apply(value):
 closed();base=backup_path(value);saved=json.loads((base/'kaz_regions_backup_manifest.json').read_text(encoding='utf8'));inv=inventory();known=known_outputs()
 if saved['branch']!=BRANCH or saved['workspace']!=str(ROOT.resolve()):raise RuntimeError('Backup workspace/branch mismatch')
 subprocess.run(['git','merge-base','--is-ancestor',saved['base_commit'],'HEAD'],cwd=ROOT,check=True)
 inputs={}
 for rel,digest in saved['input_sha256'].items():
  data=(base/'inputs'/rel).read_bytes()
  if sha(data)!=digest:raise RuntimeError('Damaged immutable region backup '+rel)
  inputs[rel]=data
 for rel,digest in saved['native_body_sha256'].items():
  if sha((GAME/rel).read_bytes())!=digest:raise RuntimeError('Installed body history changed '+rel)
 for rel,digest in saved['immutable_sha256'].items():
  if sha(effective(rel))!=digest:raise RuntimeError('Province geometry/transport changed after region backup '+rel)
 for rel,digest in saved['outside_state_sha256'].items():
  if sha(effective(rel))!=digest:raise RuntimeError('Authorised outside state changed '+rel)
 for sid in list(BODY)+list(NEW):
  rel=inv[sid]['rel'];p=ROOT/rel;current=sha(p.read_bytes()) if p.exists() else None
  if current not in {saved['prior_output_sha256'][rel],*known[rel]}:raise RuntimeError('Unreviewed manual state edit/collision '+rel)
 # Upstream stages may have rebuilt model indices and world metadata. Consume
 # their current values rather than resurrecting old canal/explicit-border rows.
 for rel in [MODEL,WORLD]:
  current=effective(rel)
  if sha(current) not in {saved['prior_output_sha256'][rel],*known[rel]}:raise RuntimeError('Unreviewed model/world edit '+rel)
  inputs[rel]=current
 outputs,report=build(inputs)
 for rel,data in outputs.items():
  if rel in [MODEL,WORLD]:continue # upstream-owned composition, checked above
  p=ROOT/rel;current=sha(p.read_bytes()) if p.exists() else None
  if current not in {saved['prior_output_sha256'].get(rel),*known[rel],sha(data)}:raise RuntimeError('Unreviewed regional output edit '+rel)
 # Every byte and validation is ready before the first runtime write.
 for rel,data in outputs.items():
  p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True)
  if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
 report.update({'backup_directory':str(base),'branch':BRANCH,'base_commit':saved['base_commit'],'input_sha256':{rel:sha(data) for rel,data in inputs.items()},'backup_input_sha256':saved['input_sha256'],'output_sha256':{rel:sha(data) for rel,data in outputs.items()}})
 caspian=ROOT/'docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json'
 if caspian.exists():
  upstream=json.loads(caspian.read_text(encoding='utf8'));report.update({'upstream_caspian_backup_directory':upstream.get('backup_directory'),'upstream_caspian_base_commit':upstream.get('base_commit')})
 p=ROOT/REPORT;data=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8')
 if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
 print('UNVERIFIED 17-oblast region outputs applied. Run city stage, then full restart/new campaign.')

def main():
 sys.stdout.reconfigure(encoding='utf8')
 cli=argparse.ArgumentParser(description=__doc__);mode=cli.add_mutually_exclusive_group();mode.add_argument('--inspect',action='store_true');mode.add_argument('--prepare-backup');mode.add_argument('--apply',action='store_true');cli.add_argument('--backup-dir');args=cli.parse_args()
 if args.prepare_backup:prepare(args.prepare_backup)
 elif args.apply:
  if not args.backup_dir:cli.error('--apply requires --backup-dir')
  apply(args.backup_dir)
 else:inspect()
if __name__=='__main__':main()
