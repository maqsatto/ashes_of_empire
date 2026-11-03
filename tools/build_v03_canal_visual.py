"""Source-only authoring of a river-rendered Caucasian canal; default inspection.

No province pixels/IDs or naval adjacencies are edited. --inspect --report-dir
writes only a labelled data-preview PNG/report. Mutating map/rivers.bmp requires
an explicit new external backup, isolated branch and closed HOI4, then restart.
"""
from pathlib import Path
from io import BytesIO
from collections import Counter
import argparse, hashlib, json, os, struct, subprocess
import numpy as np
from PIL import Image, ImageDraw
from contentlib import ROOT

GAME=Path('C:/Hearts of Iron IV')
BRANCH='spike/caspian-navigation'
RIVER_SHA='4491190a65771592ebffdb3479eae519b3b5623bfaca41500b1e2e4a38caba71'
GROZNY=(3518,662)       # Native unitstack slot0, province3672, image origin top-left.
KRASNODAR=(3415,624)    # Native unitstack slot0, province3734.
EAST_SOURCE=(3473,661)
WEST_SOURCE=(3468,661)
CASPIAN_END=(3560,650)
BLACK_END=(3385,628)

def sha(data): return hashlib.sha256(data).hexdigest()
def neighbours(p):
    x,y=p;return [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]
def component(a,p):
    seen={p};stack=[p]
    while stack:
        for n in neighbours(stack.pop()):
            if 0<=n[0]<a.shape[1] and 0<=n[1]<a.shape[0] and a[n[1],n[0]]<12 and n not in seen:seen.add(n);stack.append(n)
    return seen
def simple_path(a,start):
    comp=component(a,start);degree={p:sum(n in comp for n in neighbours(p)) for p in comp}
    if Counter(degree.values())!={1:2,2:len(comp)-2}:raise ValueError('Native candidate is not a simple orthogonal one-pixel river; do not guess a merge')
    seq=[start];prev=None
    while True:
        ns=[n for n in neighbours(seq[-1]) if n in comp and n!=prev]
        if not ns:break
        if len(ns)!=1:raise ValueError('Ambiguous river direction')
        prev=seq[-1];seq.append(ns[0])
    if len(seq)!=len(comp):raise ValueError('River cycle detected')
    return seq
def line(points):
    out=[points[0]]
    for b in points[1:]:
        x,y=out[-1]
        if x!=b[0] and y!=b[1]:raise ValueError('Artificial connectors must be orthogonal')
        while (x,y)!=b:
            x+=(b[0]>x)-(b[0]<x);y+=(b[1]>y)-(b[1]<y);out.append((x,y))
    return out

def construct(river_bytes=None):
    data=river_bytes if river_bytes is not None else (GAME/'map/rivers.bmp').read_bytes()
    if sha(data)!=RIVER_SHA:raise ValueError('River input differs from inspected installed1.19 bitmap; diagnose instead of stacking unknown edits')
    if data[:2]!=b'BM':raise ValueError('Not a BMP')
    offset=struct.unpack_from('<I',data,10)[0]
    dib,w,h,planes,bits,compression=struct.unpack_from('<IiiHHI',data,14)
    if (dib,w,h,planes,bits,compression)!=(40,5632,2048,1,8,0):raise ValueError('Expected actual native 8-bit indexed BITMAPINFOHEADER/uncompressed BMP')
    stride=((w*bits+31)//32)*4
    im=Image.open(BytesIO(data))
    if im.mode!='P':raise ValueError('Indexed palette required')
    original=np.asarray(im).copy();a=original.copy();palette=im.getpalette()
    for index,color in {0:(0,255,0),1:(255,0,0),2:(255,252,0),3:(0,225,255),7:(0,0,255),254:(122,122,122),255:(255,255,255)}.items():
        if tuple(palette[index*3:index*3+3])!=color:raise ValueError(f'Native palette differs at index{index}')
    defs={};rgb={}
    for row in (GAME/'map/definition.csv').read_text(encoding='utf-8-sig').splitlines():
        p=row.split(';')
        if len(p)>=8 and p[0].isdigit():defs[int(p[0])]=p;rgb[tuple(map(int,p[1:4]))]=int(p[0])
    prov=np.asarray(Image.open(GAME/'map/provinces.bmp').convert('RGB'))
    pid=lambda p:rgb[tuple(map(int,prov[p[1],p[0]]))]
    if pid(GROZNY)!=3672 or pid(KRASNODAR)!=3734:raise ValueError('Verified city anchor/province mismatch')
    east=simple_path(a,EAST_SOURCE);west=simple_path(a,WEST_SOURCE)
    if len(east)!=119 or len(west)!=147 or east[-1]!=CASPIAN_END or west[-1]!=BLACK_END:raise ValueError('Inspected two native river paths changed')
    if any(a[y,x]<3 for x,y in east[1:]+west[1:]):raise ValueError('Unexpected native merge/split marker inside simple path')
    # Maximum native reuse: join the two existing headwaters through four white
    # land pixels. A single rendering source is moved to the Caspian endpoint.
    bridge=line([WEST_SOURCE,EAST_SOURCE])
    for x,y in bridge:
        if defs[pid((x,y))][4]!='land':raise ValueError('Headwater canal connector is not land')
        if a[y,x] not in (0,3,255):raise ValueError('Unexpected headwater pixel')
        a[y,x]=3
    # Native Terek has no river pixel in Grozny3672. Divert one short unbranched
    # stretch through the actual city anchor; record erased native pixels openly.
    hook_a=(3516,655);hook_b=(3524,658)
    ia=east.index(hook_a);ib=east.index(hook_b)
    if ia>=ib:raise ValueError('Grozny hook order changed')
    erased=east[ia+1:ib]
    for x,y in erased:
        if defs[pid((x,y))][4]!='land':raise ValueError('Cannot erase a river segment over non-land')
        a[y,x]=255
    detour=line([hook_a,(3516,662),GROZNY,(3524,662),hook_b])
    for x,y in detour:
        if defs[pid((x,y))][4]!='land' or a[y,x] not in (3,255):raise ValueError('Grozny connector crosses unexpected water/marker/river')
        a[y,x]=3
    a[CASPIAN_END[1],CASPIAN_END[0]]=0
    seq=simple_path(a,CASPIAN_END)
    if seq[-1]!=BLACK_END or GROZNY not in seq:raise ValueError('Channel failed continuous city-to-city simple-path check')
    comp=set(seq)
    if sum(a[y,x]==0 for x,y in comp)!=1:raise ValueError('Exactly one rendering-source marker required')
    if not any(pid(p)==3734 for p in comp):raise ValueError('Channel misses Krasnodar')
    if pid(CASPIAN_END)!=1050 or pid((3385,629))!=8308:raise ValueError('Native mouth water bodies differ')
    province_runs=[]
    for point in seq:
        ident=pid(point)
        if not province_runs or province_runs[-1]!=ident:province_runs.append(ident)
    land_runs=[i for i in province_runs if defs[i][4]=='land']
    required_land=list(dict.fromkeys(land_runs))
    ys,xs=np.where(a!=original);changes=[(int(x),int(y),int(original[y,x]),int(a[y,x])) for x,y in zip(xs,ys)]
    # Patch only the native indexed pixel bytes. Preserve all BMP headers,
    # colour table entries, resolution, row layout and two native trailing bytes.
    patched=bytearray(data)
    for x,y,old,new in changes:
        address=offset+(h-1-y)*stride+x
        if patched[address]!=old:raise ValueError('BMP row-orientation mismatch')
        patched[address]=new
    result=bytes(patched)
    if result[:offset]!=data[:offset] or result[offset+h*stride:]!=data[offset+h*stride:] or len(result)!=len(data):raise ValueError('BMP encoding/palette changed')
    decoded=Image.open(BytesIO(result))
    if decoded.mode!='P' or decoded.getpalette()!=palette or not np.array_equal(np.asarray(decoded),a):raise ValueError('Patched BMP failed exact palette/pixel round trip')
    report={
        'status':'UNVERIFIED_ARTIFICIAL_CANAL_RENDERING_PROPOSAL',
        'native_rivers_sha256':sha(data),'proposed_rivers_sha256':sha(result),
        'bmp':{'width':w,'height':h,'bits':bits,'compression':compression,'pixel_offset':offset,'row_stride':stride,'native_trailing_bytes':len(data)-offset-h*stride,'entire_header_and_palette_preserved':True},
        'city_image_anchors':{'Grozny3672':GROZNY,'Krasnodar3734':KRASNODAR},
        'existing_river_lengths':[len(east),len(west)],'reused_native_channel_pixels':sum(p in set(east+west) for p in seq),
        'headwater_artificial_connector':bridge,'Grozny_artificial_detour':detour,'erased_native_Grozny_bypass':erased,
        'continuous_channel_pixels':len(seq),'changed_pixel_count':len(changes),'changed_pixels_xy_old_new':changes,
        'technical_source_relocated':{'from':[EAST_SOURCE,WEST_SOURCE],'to':CASPIAN_END},
        'water_endpoints':{'Caspian':1050,'native_Kuban_mouth_adjacent_Black_Sea':8308},
        'ordered_pixel_province_runs':province_runs,'ordered_land_runs':land_runs,
        'required_land_ids':required_land,
        'palette':{str(i):palette[i*3:i*3+3] for i in [0,1,2,3,4,6,7,9,10,11,254,255]},
        'risks':[
            'These were two distinct rivers. The headwater bridge and Grozny diversion are newly authored canal works, not an existing natural continuous river.',
            'Native river encoding affects river rendering and potentially combat/supply; this is not a guaranteed cosmetic overlay.',
            'The technical single green source is moved to the Caspian end to maintain one unbranched render graph. It is not a claim of natural flow from the sea.',
            'No new red/yellow merge/split markers are needed; all unrelated native markers are untouched.',
            'Actual ships still depend on the separately authored sea adjacency; painting a river does not make land navigable.',
            'The accepted separate naval adjacency must match Caspian1050 to BlackSea8308 through Grozny3672; actual fleet/trade passage remains untested.',
            'No installed river-format specification was found; the official wiki request was unauthorized. Native palette and simple-path source topology were verified directly; actual rendering remains untested.',
        ]}
    return result,report,original,a,prov,defs,rgb

def preview(directory,built):
    data,report,old,new,prov,defs,rgb=built
    base=Path(directory).resolve()
    if base.is_relative_to((ROOT/'map').resolve()) or base.is_relative_to(GAME.resolve()):raise ValueError('Preview artifacts must not be in runtime map or installed game')
    base.mkdir(parents=True,exist_ok=True)
    x0,y0,x1,y1=3370,610,3575,675;scale=5
    crop=prov[y0:y1+1,x0:x1+1];canvas=np.zeros(crop.shape,dtype=np.uint8)
    for yy in range(crop.shape[0]):
        for xx in range(crop.shape[1]):
            ident=rgb[tuple(map(int,crop[yy,xx]))];water=defs[ident][4] in ('sea','lake')
            canvas[yy,xx]=(176,211,225) if water else (230,226,207)
    edges=np.any(crop[:,1:]!=crop[:,:-1],axis=2);canvas[:,1:][edges]=(188,186,170)
    edges=np.any(crop[1:,:]!=crop[:-1,:],axis=2);canvas[1:,:][edges]=(188,186,170)
    a=old[y0:y1+1,x0:x1+1];b=new[y0:y1+1,x0:x1+1]
    canvas[a<12]=(38,109,170)
    canvas[(a!=b)&(b<12)]=(232,119,28)
    canvas[(a<12)&(b>=12)]=(195,49,70)
    body=Image.fromarray(canvas).resize((canvas.shape[1]*scale,canvas.shape[0]*scale),Image.Resampling.NEAREST)
    out=Image.new('RGB',(body.width,body.height+96),'#faf8ef');out.paste(body,(0,72));draw=ImageDraw.Draw(out)
    draw.text((12,8),'MAP-DATA PREVIEW: proposed artificial canal, NOT an in-game screenshot',fill='#242424')
    draw.text((12,26),'Blue: existing rivers | Orange: authored/changed channel | Red: replaced native bypass',fill='#242424')
    draw.text((12,44),'Province pixels/IDs unchanged. River renderer is not naval navigation. Full restart test required.',fill='#242424')
    for name,(x,y) in [('Grozny3672',GROZNY),('Krasnodar3734',KRASNODAR)]:
        xx=(x-x0)*scale;yy=(y-y0)*scale+72
        draw.ellipse((xx-5,yy-5,xx+5,yy+5),outline='#ac1458',width=2);draw.text((xx+8,yy-16),name,fill='#631139')
    draw.text((12,out.height-18),f'Changed pixels: {report["changed_pixel_count"]}; native BMP header/palette/trailing bytes preserved.',fill='#242424')
    out.save(base/'canal_data_overlay.png')
    (base/'canal_visual_inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return str(base/'canal_data_overlay.png')

def checked_branch():
    if os.name!='nt':raise RuntimeError('Windows process check required')
    count=subprocess.run(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name hoi4 -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True,check=True)
    if int(count.stdout.strip()):raise RuntimeError('HOI4 is running: no backup/apply mutation permitted')
    git=lambda *a:subprocess.run(['git',*a],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    if git('branch','--show-current')!=BRANCH:raise RuntimeError('Prepare isolated '+BRANCH+' branch before mutation')
    return git('rev-parse','HEAD')
def external(text):
    p=Path(text)
    if not p.is_absolute():raise ValueError('Explicit absolute external backup path required')
    p=p.resolve()
    if p.is_relative_to(ROOT.resolve()) or p.is_relative_to(GAME.resolve()) or p==Path(p.anchor):raise ValueError('Backup outside repository/installation and not a drive root required')
    return p
def prepare(directory):
    commit=checked_branch();base=external(directory)
    if base.exists() and any(base.iterdir()):raise ValueError('A fresh backup directory is required')
    current=ROOT/'map/rivers.bmp'
    built=construct()
    if current.exists() and sha(current.read_bytes()) not in (RIVER_SHA,sha(built[0])):raise ValueError('Existing mod river override is neither native nor the exact inspected canal output; inspect/reconcile first')
    base.mkdir(parents=True,exist_ok=True)
    files={str(p.relative_to(ROOT)):p for p in (ROOT/'map').rglob('*') if p.is_file()}
    files.update({rel:ROOT/rel for rel in ['history/states/232-Grozny.txt','history/states/587-Western Kazakstan.txt']})
    meta={'branch':BRANCH,'commit':commit,'workspace':str(ROOT.resolve()),'prior_mod_rivers_sha256':sha(current.read_bytes()) if current.exists() else None,'mod_snapshot':{},'native_inputs':{}}
    for rel,p in files.items():
        data=p.read_bytes();dest=base/'mod_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);meta['mod_snapshot'][rel]=sha(data)
    for rel in ['map/rivers.bmp','map/provinces.bmp','map/definition.csv','map/default.map']:
        data=(GAME/rel).read_bytes();dest=base/'native_inputs'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);meta['native_inputs'][rel]=sha(data)
    (base/'canal_visual_backup.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print('Full current mod map snapshot plus native river/province inputs backed up; no mod runtime changed:',base)
def apply(directory):
    checked_branch();base=external(directory);meta=json.loads((base/'canal_visual_backup.json').read_text(encoding='utf-8'))
    if meta['branch']!=BRANCH or meta['workspace']!=str(ROOT.resolve()):raise ValueError('Backup belongs to another workspace/branch')
    subprocess.run(['git','merge-base','--is-ancestor',meta['commit'],'HEAD'],cwd=ROOT,check=True)
    for rel,expected in meta['mod_snapshot'].items():
        original=(base/'mod_snapshot'/rel).read_bytes()
        if sha(original)!=expected:raise ValueError('Damaged backup: '+rel)
        if rel!='map/rivers.bmp' and (not (ROOT/rel).exists() or sha((ROOT/rel).read_bytes())!=expected):raise ValueError('Map/history changed after backup: '+rel)
    for rel,expected in meta['native_inputs'].items():
        if sha((base/'native_inputs'/rel).read_bytes())!=expected or sha((GAME/rel).read_bytes())!=expected:raise ValueError('Native input/backup changed: '+rel)
    data,report,*_=construct((base/'native_inputs/map/rivers.bmp').read_bytes());target=ROOT/'map/rivers.bmp'
    current=sha(target.read_bytes()) if target.exists() else None
    if current not in [meta['prior_mod_rivers_sha256'],sha(data)]:raise ValueError('Intervening river edit must be preserved/reconciled')
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() or target.read_bytes()!=data:target.write_bytes(data)
    report['backup']=str(base)
    (ROOT/'docs/design_v0_3/CANAL_VISUAL_APPLIED.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('UNVERIFIED river-rendered canal bitmap written. No province/adjacency edit or navigation verification flag. Full restart required.')
def main():
    cli=argparse.ArgumentParser(description=__doc__);g=cli.add_mutually_exclusive_group();g.add_argument('--inspect',action='store_true');g.add_argument('--prepare-backup');g.add_argument('--apply',action='store_true');cli.add_argument('--backup-dir');cli.add_argument('--report-dir');a=cli.parse_args()
    if a.prepare_backup:prepare(a.prepare_backup)
    elif a.apply:
        if not a.backup_dir:cli.error('--apply requires a fresh --backup-dir')
        apply(a.backup_dir)
    else:
        built=construct();r=built[1];print(json.dumps({k:r[k] for k in ['status','bmp','existing_river_lengths','reused_native_channel_pixels','continuous_channel_pixels','changed_pixel_count','water_endpoints','risks']},indent=2))
        if a.report_dir:print('Labelled data preview:',preview(a.report_dir,built))
        print('No runtime map or installed-game file written.')
if __name__=='__main__':main()
