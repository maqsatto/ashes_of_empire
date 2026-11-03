"""Isolated, UNVERIFIED Caspian map-spike authoring; default is read-only.

--inspect: construct/validate proposed bytes in memory only (also the default).
--prepare-backup ABSOLUTE_PATH: on the isolated branch with HOI4 closed, snapshot
inputs and prior mod outputs outside the repository, without changing the mod.
--apply --backup-dir ABSOLUTE_PATH: require that snapshot and the same isolated
branch, then generate the deterministic map/history overrides for a full restart.
Never sets aof_caspian_navigation_verified. Never writes the installed game.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import re
import subprocess

import numpy as np
from PIL import Image
from io import BytesIO
from contentlib import ROOT
from build_v03_compat import TOKEN, parse, scalar

GAME = Path('C:/Hearts of Iron IV')
BRANCH = 'spike/caspian-navigation'
WATER = (843, 1050, 1271, 1496)
SHORE = {
    229: (1536, 4458, 4473, 7495, 7661, 12434),
    232: (700, 3668, 4463, 6701, 6748, 7624),
    236: (757, 11736), 237: (3726, 6758),
    266: (4580, 7602, 10385, 10768),
    406: (464, 615, 3618, 3622, 9453, 11578),
    420: (4609, 4637, 4901),
    584: (1593, 4563, 7477, 7563, 10406, 12359),
    587: (475, 642, 1517, 3593, 11701),
}
# Unique control set, in first pixel appearance order along the accepted visible
# channel. This is NOT a linear province graph: the river repeatedly crosses
# province borders. The complete ordered pixel trace is verified in build().
ROUTE = {700:232,6701:232,3682:232,6730:232,683:232,3672:821,
         11632:232,6702:235,9647:828,6733:235,685:827,6718:235,
         11633:235,9649:233,6674:827,11664:233,6692:233,714:235,
         11678:235,9694:234,11696:235,735:234,9726:235,9709:234,
         11681:234,6768:234,3734:234,9696:234,3760:234,11729:234,6741:234}
CANAL_FROM, CANAL_TO, CANAL_THROUGH = 1050, 8308, 3672
PORTS = [
    # state, owner, land province, water province, measured adjacent land/water X/Z
    (587, 'KAZ', 1517, 1050, (3612, 1385), (3612, 1384)),
    (232, 'CAU', 3668, 1050, (3553, 1380), (3554, 1380)),
]
STATE_FILES = {587: 'history/states/587-Western Kazakstan.txt',
               232: 'history/states/232-Grozny.txt'}
MAP_OUTPUTS = ('map/definition.csv', 'map/adjacencies.csv', 'map/adjacency_rules.txt',
               'map/strategicregions/70-Caspian Sea.txt', 'map/buildings.txt', 'map/unitstacks.txt')
OUTPUTS = MAP_OUTPUTS + tuple(STATE_FILES.values())
NATIVE_HASHES = {
    'map/default.map': 'AF7037B4BE45C903FC3E136462DCE7071EB468EAC9A50F9D81C48DBF7D6A16F2',
    'map/definition.csv': '86846BE71198D6772C651638AA22E3656133198DE9B7C49C6234ED48CF33D87B',
    'map/provinces.bmp': 'E131D30E5DCB13D9C2A8598F820A2DE0AE9828F3A24F2BDDC1BCFFF40F71660A',
    'map/adjacencies.csv': '26A26C3F42A4B01FB905C99659024E857FFC05E3172FCD9953395321FB76ED64',
    'map/adjacency_rules.txt': '9D430DEB495F4F4AD20CE4C773A36AED0E2083C7987CF29559FA5ED86A846452',
    'map/strategicregions/70-Caspian Sea.txt': '4ADA0E072169BE1EE571E9C1BED9309CFF0321E55FC7F3627B5C39932F4AF7EA',
}
UNCERTAINTIES = [
    'This is unplayed map authoring, not verified navigation. Keep the verified-navigation flag unset.',
    'A long sea-to-sea shortcut follows native canal syntax; its fleet/trade/mission routing and visual line need actual tests.',
    'Port spawn height9.50 and rotation0 follow native numeric format but their models/docking need nudge/visual inspection.',
    'New sea unitstack coordinates are projected from native8334 slot metadata onto verified water pixels; their icon spacing remains unverified.',
    'KAZ1517 has no existing railway/supply-node attachment found in the spike inspection. No invented railway or supply network is generated.',
    'No dockyard, fleet, convoy, technology, country boundary, ownership, supply-node or railway is gifted by this spike.',
    'Neutral passage follows Suez-like open navy/trade permissions for the physical test; final treaty-specific military rights are separate.',
    'Existing lake terrain/heightmap pixels are retained. Sea rendering after definition conversion is unverified.',
]


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


class MemoryScript:
    def __init__(self, text, name): self.text, self.name = text, name
    def read_text(self, **kwargs): return self.text
    def __str__(self): return self.name


def decode(data):
    return data.decode('utf-8-sig').replace('\r\n', '\n')


def encode(text, original=b''):
    return text.replace('\r\n', '\n').encode('utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf-8')


def metadata(data, name):
    return parse(MemoryScript(decode(data), name))


def children(nodes, key):
    matches = [v for k, op, v in nodes if k == key and isinstance(v, list)]
    if len(matches) != 1: raise ValueError(f'Expected one {key} block; found {len(matches)}')
    return matches[0]


def state_info(data, name):
    state = children(metadata(data, name), 'state')
    history = children(state, 'history')
    # Province lists are bare atoms, so extract only this actual native list block.
    text = decode(data)
    ps = re.search(r'\bprovinces\s*=\s*\{([^}]+)\}', re.sub(r'#[^\n]*', '', text))
    if not ps: raise ValueError(f'No province list in {name}')
    return int(scalar(state, 'id')), scalar(history, 'owner'), set(map(int, re.findall(r'\d+', ps[1])))


def current_validation_state(state):
    candidates=[p for p in (ROOT/'history/states').glob('*.txt') if re.match(str(state)+r'\D',p.name)]
    if not candidates:
        candidates=[p for p in (GAME/'history/states').glob('*.txt') if re.match(str(state)+r'\D',p.name)]
    if len(candidates)!=1: raise ValueError(f'Cannot uniquely locate validation-only state{state}')
    return candidates[0].read_bytes()


def input_bytes():
    # Map inputs intentionally come from the inspected installation, not a mixture
    # of a previously generated map and later partial outputs.
    inputs = {}
    for rel in set(MAP_OUTPUTS) | set(NATIVE_HASHES):
        data = (GAME / rel).read_bytes()
        if rel in NATIVE_HASHES and digest(data) != NATIVE_HASHES[rel]:
            raise ValueError(f'Installed map changed since spike inspection: {rel}; inspect the new version first')
        inputs[rel] = data
    for rel in STATE_FILES.values():
        inputs[rel] = (ROOT / rel).read_bytes()
    # Additional current ownership metadata is validation only, not an output.
    for state in sorted(set(ROUTE.values()) | set(SHORE)):
        candidates = [p for p in (ROOT / 'history/states').glob('*.txt') if re.match(str(state) + r'\D', p.name)]
        if not candidates:
            candidates = [p for p in (GAME / 'history/states').glob('*.txt') if re.match(str(state) + r'\D', p.name)]
        if len(candidates) != 1: raise ValueError(f'Cannot uniquely locate state{state}: {candidates}')
        inputs['validation_states/' + str(state) + '.txt'] = candidates[0].read_bytes()
    return inputs


def block_span(text, key, start=0, end=None):
    tokens = [m for m in TOKEN.finditer(text, start, len(text) if end is None else end) if not m.group().startswith('#')]
    for i, m in enumerate(tokens[:-2]):
        if m.group() == str(key) and tokens[i+1].group() == '=' and tokens[i+2].group() == '{':
            depth = 1
            for close in tokens[i+3:]:
                depth += (close.group() == '{') - (close.group() == '}')
                if depth == 0: return tokens[i+2].end(), close.start()
            raise ValueError(f'Unclosed {key} block')
    return None


def port_history(data, rel, state_id, owner, province):
    observed_id, observed_owner, provinces = state_info(data, rel)
    if (observed_id, observed_owner) != (state_id, owner) or province not in provinces:
        raise ValueError(f'Port state fixture differs: {rel}')
    text = decode(data)
    history = block_span(text, 'history')
    building = block_span(text, 'buildings', *history)
    if not building: raise ValueError(f'Expected native buildings block in {rel}')
    existing = block_span(text, province, *building)
    if existing:
        if re.search(r'\bnaval_base\s*=', text[existing[0]:existing[1]]):
            raise ValueError(f'Port{province} already has naval-base data in backup input; do not stack spikes')
        at = existing[1]
        text = text[:at] + '\n\t\t\t\tnaval_base = 1\n' + text[at:]
    else:
        at = building[1]
        text = text[:at] + f'\n\t\t\t{province} = {{ naval_base = 1 }} # isolated Caspian test base\n\t\t' + text[at:]
    return encode(text, data)


def build(inputs):
    out = {}
    defs = {}
    rows = decode(inputs['map/definition.csv']).splitlines()
    for line in rows:
        row = line.split(';')
        if len(row) >= 8 and row[0].isdigit(): defs[int(row[0])] = row
    for ident in WATER:
        if defs[ident][4:8] != ['lake', 'false', 'lakes', '0']: raise ValueError(f'Unexpected native lake row{ident}')
    shore = {p for ids in SHORE.values() for p in ids}
    state_meta = {}
    for state in set(SHORE) | set(ROUTE.values()):
        state_meta[state] = state_info(inputs['validation_states/' + str(state) + '.txt'], str(state))
        if state_meta[state][0] != state: raise ValueError(f'State ID mismatch{state}')
    for province, state in ROUTE.items():
        if state_meta[state][1] != 'CAU' or province not in state_meta[state][2]:
            raise ValueError(f'Canal control corridor not CAU fixture: province{province}, state{state}')
    for state, provinces in SHORE.items():
        if not set(provinces) <= state_meta[state][2]: raise ValueError(f'Shore/state membership changed: {state}')
    image = np.asarray(Image.open(BytesIO(inputs['map/provinces.bmp'])).convert('RGB'))
    if image.shape != (2048, 5632, 3): raise ValueError('Unexpected province bitmap dimensions')
    colors = {i: np.array(list(map(int, row[1:4])), dtype=np.uint8) for i, row in defs.items()}
    rgb_ids = {tuple(map(int, c)): i for i, c in colors.items()}
    pixels = {}
    observed_shore = set()
    shore_contacts = {} # exact adjacent land/water pixel pairs, not guessed port centres
    for ident in WATER:
        ys, xs = np.where(np.all(image == colors[ident], axis=2))
        pixels[ident] = (xs, 2048-ys)
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            adjacent = image[ys+dy, xs+dx]
            for color in np.unique(adjacent, axis=0):
                neighbour = rgb_ids[tuple(map(int, color))]
                if defs[neighbour][4] != 'land': continue
                observed_shore.add(neighbour)
                contact = np.all(adjacent == color, axis=1)
                # image y grows downward; map Z grows upward from bitmap bottom.
                pairs = zip(xs[contact]+dx, 2048-(ys[contact]+dy),
                            xs[contact], 2048-ys[contact])
                shore_contacts.setdefault(neighbour, set()).update(
                    (int(lx),int(lz),ident,int(wx),int(wz)) for lx,lz,wx,wz in pairs)
    if observed_shore != shore: raise ValueError('Actual lake coastline differs from the forty inspected land provinces')
    # Validate the actual accepted 278-pixel visible channel without writing it.
    # Unique first-appearance IDs cannot be treated as adjacent: 71 land runs
    # include repeated crossings of the same border. Use the real ordered pixels.
    from build_v03_canal_visual import construct, simple_path, CASPIAN_END
    visual=construct()
    channel=simple_path(visual[3],CASPIAN_END)
    trace=[]
    for x,y in channel:
        ident=rgb_ids[tuple(map(int,image[y,x]))]
        if not trace or trace[-1]!=ident: trace.append(ident)
    land_runs=[i for i in trace if defs[i][4]=='land']
    if len(channel)!=278 or len(land_runs)!=71 or set(land_runs)!=set(ROUTE):
        raise ValueError('Visible canal/control set changed; derive a new reviewed province trace')
    if 3672 not in land_runs or 3734 not in land_runs or trace[0]!=CANAL_FROM or trace[-1]!=6741:
        raise ValueError('Canal no longer passes Grozny/Krasnodar and the accepted shores')
    for ident,xy in [(1050,(3551,650)),(700,(3550,650)),(6741,(3385,628)),(8308,(3385,629))]:
        if rgb_ids[tuple(map(int,image[xy[1],xy[0]]))]!=ident:raise ValueError('Accepted sea/land endpoint pixel changed')
    for state, owner, province, water, land_xy, water_xy in PORTS:
        for ident, (x,z) in [(province,land_xy),(water,water_xy)]:
            if not np.array_equal(image[2048-z, x], colors[ident]): raise ValueError(f'Port coordinate no longer in province{ident}')
        if sum(abs(a-b) for a,b in zip(land_xy,water_xy)) != 1: raise ValueError('Port points are not neighbouring pixels')
        out[STATE_FILES[state]] = port_history(inputs[STATE_FILES[state]], STATE_FILES[state], state, owner, province)
    new_rows = []
    for line in rows:
        row = line.split(';')
        if row[0].isdigit():
            ident = int(row[0])
            if ident in WATER: row[4:7] = ['sea','true','ocean']
            elif ident in shore:
                if row[4] != 'land': raise ValueError(f'Coast row{ident} no longer land')
                row[5] = 'true'
            line = ';'.join(row)
        new_rows.append(line)
    out['map/definition.csv'] = encode('\n'.join(new_rows)+'\n', inputs['map/definition.csv'])
    region = decode(inputs['map/strategicregions/70-Caspian Sea.txt'])
    native_region = children(metadata(inputs['map/strategicregions/70-Caspian Sea.txt'], 'region70'), 'strategic_region')
    if scalar(native_region,'id') != '70': raise ValueError('Wrong strategic region')
    ps = re.search(r'provinces\s*=\s*\{([^}]+)',region)
    if set(map(int,re.findall(r'\d+',ps[1]))) != set(WATER): raise ValueError('Unexpected region70 membership')
    if 'naval_terrain' in region: raise ValueError('Native Caspian naval terrain changed; re-inspect')
    where = block_span(region,'strategic_region')[0]
    region = region[:where]+'\n\tnaval_terrain = water_shallow_sea # isolated gameplay terrain proposal\n'+region[where:]
    out['map/strategicregions/70-Caspian Sea.txt'] = encode(region, inputs['map/strategicregions/70-Caspian Sea.txt'])
    adjacency = decode(inputs['map/adjacencies.csv'])
    lines = adjacency.splitlines()
    terminators = [i for i,line in enumerate(lines) if line.startswith('-1;-1;')]
    if len(terminators) != 1 or any('AOF_CAUCASIAN_CANAL' in line for line in lines): raise ValueError('Unexpected adjacency baseline')
    lines.insert(terminators[0], '1050;8308;sea;3672;3551.5;1397.5;3385.5;1418.5;AOF_CAUCASIAN_CANAL;AoE Grozny-Krasnodar river-canal spike')
    out['map/adjacencies.csv'] = encode('\n'.join(lines)+'\n', inputs['map/adjacencies.csv'])
    rule = '''
# Isolated AoE physical-routing test; not final treaty policy.
adjacency_rule = {
 name = "AOF_CAUCASIAN_CANAL"
 contested = { army = no navy = no submarine = no trade = no }
 enemy = { army = no navy = no submarine = no trade = no }
 friend = { army = yes navy = yes submarine = yes trade = yes }
 neutral = { army = yes navy = yes submarine = yes trade = yes }
 required_provinces = { AOF_REVIEWED_CANAL_CONTROL_SET }
 is_disabled = { OR = { has_global_flag = aof_caucasian_canal_closed has_country_flag = aof_caucasian_canal_blocked_for_country } }
 icon = 3672
 offset = { 0 0 0 }
}
'''.replace('AOF_REVIEWED_CANAL_CONTROL_SET',' '.join(map(str,ROUTE)))
    out['map/adjacency_rules.txt'] = encode(decode(inputs['map/adjacency_rules.txt']).rstrip()+'\n'+rule, inputs['map/adjacency_rules.txt'])
    buildings = decode(inputs['map/buildings.txt']).rstrip()+'\n'
    # The engine needs a nudger spawn for EVERY newly coastal land province,
    # including coasts without a constructed naval base. These map placements do
    # not add naval-base levels to history. State IDs/owners come from effective
    # mod-over-native state history already validated against province lists.
    province_states = {}
    for state, (observed_id, owner, provinces) in state_meta.items():
        for province in provinces & shore:
            if province in province_states: raise ValueError(f'Duplicate shore province state membership: {province}')
            province_states[province] = (observed_id,owner)
    if set(province_states) != shore: raise ValueError('Incomplete effective state mapping for coastal land')
    dedicated = {p[2]:p for p in PORTS}
    placements = []
    for province in sorted(shore):
        state,owner = province_states[province]
        contacts = sorted(shore_contacts[province])
        if province in dedicated:
            expected_state,expected_owner,_,water,land_xy,water_xy = dedicated[province]
            if (state,owner)!=(expected_state,expected_owner): raise ValueError('Dedicated port ownership changed')
            chosen=(*land_xy,water,*water_xy)
            if chosen not in shore_contacts[province]: raise ValueError('Dedicated port is not an observed shore contact')
        else:
            # Select a real contact nearest the mean of this province's shoreline;
            # deterministic tuple tie-breaking preserves byte-identical output.
            cx=sum(c[0] for c in contacts)/len(contacts)
            cz=sum(c[1] for c in contacts)/len(contacts)
            chosen=min(contacts,key=lambda c:((c[0]-cx)**2+(c[1]-cz)**2,c))
        x,z,water,wx,wz=chosen
        if not np.array_equal(image[2048-z,x],colors[province]): raise ValueError('Spawn land pixel mismatch')
        if not np.array_equal(image[2048-wz,wx],colors[water]): raise ValueError('Spawn water pixel mismatch')
        if abs(x-wx)+abs(z-wz)!=1: raise ValueError('Spawn contact pixels not adjacent')
        placements.append({'state':state,'owner':owner,'province':province,'water_province':water,
                           'land_xz':[x,z],'water_xz':[wx,wz],'spawn_xz':[x+0.5,z-0.5],'dedicated_history_port':province in dedicated})
    # Native states can also possess Black Sea/Persian Gulf spawn rows. Preserve
    # those; reject only a duplicate placement on the same actual shore province.
    existing_shore_spawns = set()
    for line in buildings.splitlines():
        fields=line.split(';')
        if len(fields)<7 or fields[1]!='naval_base_spawn': continue
        px,pz=int(float(fields[2])),int(float(fields[4]))
        py=image.shape[0]-pz
        if not (0<=px<image.shape[1] and 0<=py<image.shape[0]): continue
        province=rgb_ids.get(tuple(map(int,image[py,px])))
        if province in shore:
            if province in existing_shore_spawns: raise ValueError(f'Duplicate native spawn for coastal province{province}')
            existing_shore_spawns.add(province)
    # The inspected native lake coasts have no spawn rows. Refuse a changed input
    # instead of silently retaining an unreviewed position/water target.
    if existing_shore_spawns: raise ValueError(f'Native Caspian coast already has spawn placements: {sorted(existing_shore_spawns)}')
    for placement in placements:
        # Centre the verified pixel: integer edge positions can be sampled as
        # neighbouring sea by the engine's bottom-origin map coordinates.
        x,z=placement['spawn_xz']
        buildings += f"{placement['state']};naval_base_spawn;{x:.2f};9.50;{z:.2f};0.00;{placement['water_province']}\n"
    if len(placements)!=len(shore) or len({p['province'] for p in placements})!=len(shore):
        raise ValueError('Expected one unique nudger port spawn per coastal land province')
    # Native buildings.txt has no trailing newline. A terminal blank record is
    # parsed as an invalid argument row by the observed engine build.
    out['map/buildings.txt'] = encode(buildings.rstrip('\n'), inputs['map/buildings.txt'])
    stack_rows = decode(inputs['map/unitstacks.txt']).splitlines()
    ref = [line.split(';') for line in stack_rows if line.startswith('8334;')]
    if not ref or any(len(row) != 7 for row in ref): raise ValueError('Unexpected native sea unitstack format')
    if any(line.split(';')[0] in set(map(str,WATER)) for line in stack_rows): raise ValueError('Caspian already has unitstacks in baseline')
    ref_types = [row[1] for row in ref]
    if len(ref_types) != len(set(ref_types)): raise ValueError('Duplicate source sea unitstack slot')
    ry,rx = np.where(np.all(image == colors[8334], axis=2));rz = 2048-ry
    cx,cz = float(rx.mean()),float(rz.mean())
    for ident in WATER:
        xs,zs = pixels[ident];tx,tz=float(xs.mean()),float(zs.mean())
        scale = 0.65*min((float(xs.max()-xs.min())-4)/(rx.max()-rx.min()),(float(zs.max()-zs.min())-4)/(rz.max()-rz.min()))
        for row in ref:
            desired_x = tx+(float(row[2])-cx)*scale
            desired_z = tz+(float(row[4])-cz)*scale
            index = int(np.argmin((xs-desired_x)**2+(zs-desired_z)**2))
            x,z=int(xs[index]),int(zs[index])
            # Height, rotation and icon scale are native sea metadata; X/Z are
            # newly computed, deterministic, actual Caspian water pixel centres.
            stack_rows.append(f'{ident};{row[1]};{x:.2f};{row[3]};{z:.2f};{row[5]};{row[6]}')
    out['map/unitstacks.txt'] = encode('\n'.join(stack_rows)+'\n', inputs['map/unitstacks.txt'])
    for rel,data in out.items():
        if rel.endswith('.txt'): metadata(data,rel)
        if b'set_global_flag = aof_caspian_navigation_verified' in data: raise ValueError('Never mark an unplayed spike verified')
    if set(out) != set(OUTPUTS): raise ValueError('Unexpected output path set')
    return out, {'water_provinces': list(WATER), 'coastal_land_provinces': sorted(shore),
                 'canal_land_corridor': list(ROUTE), 'canal_ordered_province_runs':trace,
                 'canal_ordered_land_runs':land_runs,'canal_sea_endpoints':[CANAL_FROM,CANAL_TO],
                 'canal_through_and_icon':CANAL_THROUGH,'canal_control_states':sorted(set(ROUTE.values())),
                 'canal_visual_draft_changed_bytes':visual[1]['changed_pixel_count'],
                 'port_levels': {str(p[2]):1 for p in PORTS},
                 'coastal_nudger_spawn_count':len(placements), 'coastal_nudger_spawns':placements,
                 'new_sea_unitstack_slots_per_province':len(ref), 'uncertainties':UNCERTAINTIES}


def command(args):
    return subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()


def require_closed_branch():
    if os.name != 'nt': raise RuntimeError('Windows HOI4 process check required for mutation')
    count = command(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name hoi4 -ErrorAction SilentlyContinue).Count'])
    if int(count): raise RuntimeError('HOI4 is running; no backup/apply mutation permitted')
    branch = command(['git','branch','--show-current'])
    if branch != BRANCH: raise RuntimeError(f'Use the separately prepared {BRANCH} branch; current branch is {branch!r}')
    return command(['git','rev-parse','HEAD'])


def backup_path(text):
    path=Path(text)
    if not path.is_absolute(): raise ValueError('Backup directory must be an explicit absolute path')
    path=path.resolve()
    if path.is_relative_to(ROOT.resolve()) or path.is_relative_to(GAME.resolve()) or path==Path(path.anchor):
        raise ValueError('Backup must be outside both repository and installed game, and not a drive root')
    return path


def prepare_backup(directory):
    commit=require_closed_branch();base=backup_path(directory)
    if base.exists() and any(base.iterdir()): raise ValueError('Use a new empty backup directory; existing backups are never overwritten')
    inputs=input_bytes();out,report=build(inputs)
    base.mkdir(parents=True,exist_ok=True)
    manifest={'branch':BRANCH,'base_commit':commit,'workspace':str(ROOT.resolve()),'inputs':{},'prior_mod':{},'report':report}
    for rel,data in inputs.items():
        path=base/'inputs'/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        manifest['inputs'][rel]=digest(data)
    for rel in OUTPUTS:
        current=ROOT/rel
        if current.exists():
            data=current.read_bytes();path=base/'prior_mod'/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            manifest['prior_mod'][rel]=digest(data)
        else: manifest['prior_mod'][rel]=None
    (base/'caspian_backup_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Backup prepared; NO mod runtime output written:',base)


def known_poststage_outputs(base,manifest):
    """Recognise only owner-authorised poststages with the same upstream backup.

    This is permission to rebuild the preceding Caspian stage, not to omit later
    stages: user-state edits, KAZ regions and city/VP edits must be reapplied afterwards.
    Unknown/manual output bytes still fail the normal intervening-edit guard.
    """
    known={};reports=[]
    for name in ['USER_STATE_EDITS_MANIFEST.json','KAZ_REGIONS_MANIFEST.json','CITY_MANIFEST.json']:
        path=ROOT/'docs/design_v0_3'/name
        if not path.exists(): continue
        saved=json.loads(path.read_text(encoding='utf-8'))
        upstream=saved.get('upstream_caspian_backup_directory')
        if saved.get('branch')!=BRANCH or not upstream: continue
        if str(Path(upstream).resolve()).casefold()!=str(base.resolve()).casefold(): continue
        if saved.get('upstream_caspian_base_commit')!=manifest['base_commit']: continue
        hashes=saved.get('output_sha256',{})
        if not isinstance(hashes,dict): raise ValueError('Invalid known poststage output-hash report: '+name)
        for rel,value in hashes.items():
            rel=rel.replace('\\','/')
            if rel in OUTPUTS:
                if not isinstance(value,str) or not re.fullmatch(r'[0-9A-Fa-f]{64}',value): raise ValueError('Invalid poststage SHA256: '+name)
                known.setdefault(rel,set()).add(value.upper())
        reports.append(name)
    return known,reports


def load_backed_inputs(base,manifest):
    inputs={}
    for rel,expected in manifest['inputs'].items():
        data=(base/'inputs'/rel).read_bytes()
        if digest(data)!=expected: raise ValueError(f'Backup input damaged: {rel}')
        inputs[rel]=data
    additions={}
    for state in sorted(set(ROUTE.values())|set(SHORE)):
        rel='validation_states/'+str(state)+'.txt'
        if rel not in inputs:
            inputs[rel]=current_validation_state(state)
            additions[rel]=digest(inputs[rel])
    return inputs,additions


def apply(directory):
    require_closed_branch();base=backup_path(directory)
    manifest=json.loads((base/'caspian_backup_manifest.json').read_text(encoding='utf-8'))
    if manifest['branch']!=BRANCH or manifest['workspace']!=str(ROOT.resolve()): raise ValueError('Backup belongs to another branch/workspace')
    subprocess.run(['git','merge-base','--is-ancestor',manifest['base_commit'],'HEAD'],cwd=ROOT,check=True)
    # The original eight-province spike backup predates the accepted 31-province
    # visual route. Extra CAU state files are read ONLY as validation metadata;
    # no state ownership/geometry/history output is authored for these files.
    inputs,validation_additions=load_backed_inputs(base,manifest)
    for rel,expected in NATIVE_HASHES.items():
        if digest((GAME/rel).read_bytes())!=expected: raise ValueError(f'Installed reference changed: {rel}')
    out,report=build(inputs)
    previous_report=ROOT/'docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json'
    previous={}
    if previous_report.exists():
        saved=json.loads(previous_report.read_text(encoding='utf-8'))
        if saved.get('backup_directory')==str(base) and saved.get('base_commit')==manifest['base_commit']:
            previous=saved.get('output_sha256',{})
    known_stages,stage_reports=known_poststage_outputs(base,manifest)
    for rel,data in out.items():
        current=ROOT/rel;existing=digest(current.read_bytes()) if current.exists() else None
        allowed={manifest['prior_mod'][rel],digest(data),previous.get(rel)}|known_stages.get(rel,set())
        if existing not in allowed:
            raise ValueError(f'Mod output changed after backup: {rel}; preserve/reconcile it before applying the spike')
    # All checks and all bytes are ready before the first mod write.
    for rel,data in out.items():
        target=ROOT/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or target.read_bytes()!=data: target.write_bytes(data)
    report.update({'backup_directory':str(base),'branch':BRANCH,'base_commit':manifest['base_commit'],
                   'output_sha256':{rel:digest(data) for rel,data in out.items()},'navigation_verified':False,
                   'validation_only_additional_state_inputs':validation_additions,
                   'recognised_poststage_reports':stage_reports,
                   'pipeline_notice':'Reapply USER_STATE_EDITS, KAZ_REGIONS and CITY stages after Caspian; their approved histories/building-state remaps are later stages.'})
    target=ROOT/'docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json';data=(json.dumps(report,indent=2)+'\n').encode('utf-8')
    if not target.exists() or target.read_bytes()!=data: target.write_bytes(data)
    print('UNVERIFIED isolated map spike generated. Full restart/new game required. Navigation flag remains unset.')


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    mode=cli.add_mutually_exclusive_group()
    mode.add_argument('--inspect',action='store_true')
    mode.add_argument('--prepare-backup',metavar='ABSOLUTE_PATH')
    mode.add_argument('--apply',action='store_true')
    cli.add_argument('--backup-dir',metavar='ABSOLUTE_PATH')
    args=cli.parse_args()
    if args.prepare_backup: prepare_backup(args.prepare_backup)
    elif args.apply:
        if not args.backup_dir: cli.error('--apply requires --backup-dir from an explicit prepared backup')
        apply(args.backup_dir)
    else:
        if args.backup_dir:
            base=backup_path(args.backup_dir)
            saved=json.loads((base/'caspian_backup_manifest.json').read_text(encoding='utf-8'))
            if saved['workspace']!=str(ROOT.resolve()) or saved['branch']!=BRANCH: raise ValueError('Wrong inspection backup workspace/branch')
            inputs,extra=load_backed_inputs(base,saved)
        else:
            inputs=input_bytes();extra={}
        out,report=build(inputs)
        report['validation_only_additional_state_inputs']=extra
        report['mode']='READ_ONLY_INSPECTION_NO_RUNTIME_FILES'
        report['required_branch']=BRANCH
        report['proposed_outputs']={rel:{'bytes':len(data),'sha256':digest(data)} for rel,data in out.items()}
        print(json.dumps(report,indent=2))
        print('Constructed/validated in memory only. No backup, map, history, manifest or verified flag written.')


if __name__=='__main__': main()
