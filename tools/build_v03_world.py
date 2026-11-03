"""Build a clearly provisional playable 1924 world from installed 1.19 history.
Never writes to the game installation. No map geometry or on-actions changes.
"""
from pathlib import Path
import re,json,struct,sys
from contentlib import write,localize
GAME=Path('C:/Hearts of Iron IV'); ROOT=Path(__file__).resolve().parents[1]
LOC={}; MANIFEST={'status':'PROVISIONAL PLAYTEST FIXTURE, NOT CANON','date':'1924.9.1.12','countries':{},'states':{}}
def masked(s):
    """Preserve offsets while removing comments/strings from structural parsing."""
    return re.sub(r'"(?:[^"\\]|\\.)*"|#[^\n]*',lambda m:' '*len(m[0]),s)
def span(s,key):
    m=re.search(r'\b'+re.escape(key)+r'\s*=\s*\{',masked(s));assert m,key
    start=m.end();end=start;depth=1;mask=masked(s)
    while depth:
        depth+=(mask[end]=='{')-(mask[end]=='}');end+=1
    return m.start(),start,end-1,end
def undated(s):
    while True:
        m=re.search(r'\b\d{4}\.\d+\.\d+(?:\.\d+)?\s*=\s*\{',masked(s))
        if not m:return s
        end=m.end();depth=1;mask=masked(s)
        while depth:
            depth+=(mask[end]=='{')-(mask[end]=='}');end+=1
        s=s[:m.start()]+s[end:]
def initial_owner(s):
    _,a,b,_=span(s,'history');m=re.search(r'\bowner\s*=\s*(\w+)',masked(s[a:b]));return m[1] if m else None
def provinces(s):
    _,a,b,_=span(s,'provinces');return [int(x) for x in re.findall(r'\d+',masked(s[a:b]))]
def vps(s):
    points=[]
    for m in re.finditer(r'\bvictory_points\s*=\s*\{([^}]+)\}',masked(s)):
        nums=re.findall(r'\d+(?:\.\d+)?',m[1]);points.extend((int(nums[i]),float(nums[i+1])) for i in range(0,len(nums),2))
    return sorted(points,key=lambda x:(-x[1],x[0]))
STATES={};STATE_NAMES={}
for p in sorted((GAME/'history/states').glob('*.txt')):
    text=undated(p.read_text(encoding='utf-8-sig'));sid=int(re.search(r'\bid\s*=\s*(\d+)',masked(text))[1])
    STATES[sid]={'path':p,'text':text,'owner':initial_owner(text),'cores':set(re.findall(r'\badd_core_of\s*=\s*(\w+)',masked(text))),'provinces':provinces(text),'vps':vps(text)}
for p in sorted((GAME/'localisation/english').glob('*state*names*.yml')):
    for key,name in re.findall(r'^\s*STATE_(\d+):\d*\s*"([^"]*)"',p.read_text(encoding='utf-8-sig'),re.M):
        STATE_NAMES.setdefault(int(key),name)
CUSTOM={
 'SIB':('Siberian Republic','Сибирская Республика',(87,151,104),'eastern_european'),
 'CAU':('Caucasian Federation','Кавказская Федерация',(166,113,70),'eastern_european'),
 'TRK':('Turkestan','Туркестан',(162,142,76),'middle_eastern'),
 'NAF':('North African Commonwealth','Североафриканское содружество',(177,137,82),'middle_eastern'),
 'CMT':('Commercial Administration','Коммерческое государство',(105,135,155),'western_european'),
}
installed_tags='\n'.join(p.read_text(encoding='utf-8-sig') for p in (GAME/'common/country_tags').glob('*.txt'))
for tag in CUSTOM:assert not re.search(r'^\s*'+tag+r'\s*=',installed_tags,re.M),('installed tag collision',tag)
# Owner-approved extent: only one or two genuinely bordering Turkish regions.
# Choose the minimal one-state implementation. Native provinces.bmp contacts:
# 354/230: Ardahan 10403 -> Gyumri 12441, pixels (3480,701)/(3481,701).
# 354/231: Georgia 3656 -> Ardahan 10403, pixels (3470,694)/(3471,694).
# 353 is Tunceli, despite filename '353-Erzurum.txt'; it has no CAU border.
CAU_TURKISH_BORDER_STATES=[354]
assert all(STATES[i]['owner']=='TUR' for i in CAU_TURKISH_BORDER_STATES)
MANIFEST['caucasian_turkish_border']={
 'authorization':'Owner requested only one or two adjacent Turkish border regions; minimal one-state allocation selected.',
 'allocated_states':CAU_TURKISH_BORDER_STATES,
 'restored_native_states':[353],
 'native_bitmap_adjacencies':[
  {'turkish_state':354,'caucasian_state':230,'provinces':[10403,12441],'pixels':[[3480,701],[3481,701]]},
  {'turkish_state':354,'caucasian_state':231,'provinces':[10403,3656],'pixels':[[3471,694],[3470,694]]},
 ],
 'note':'This border instruction does not approve the other provisional capitals or unspecified world geography.',
}
MANIFEST['user_authorized_state_allocations']={'KAZ':[582,652,236],'note':'Explicit owner request; province-level corrections are applied afterward by the separately backed-up state-edits generator. No other borders or capitals are approved by this allocation.'}
ASSIGN={
 'KAZ':[i for i,s in STATES.items() if s['owner']=='SOV' and 'KAZ' in s['cores']]+[582,652,236],
 'TRK':[i for i,s in STATES.items() if s['owner']=='SOV' and s['cores']&{'UZB','TMS','TAJ','KYR'}],
 'CAU':[229,230,231,232,233,234,235,821,826,827,828]+CAU_TURKISH_BORDER_STATES,
 'SIB':[40,403,516,564,565,566,567,568,569,570,571,574,575,576,577,578,579,580,654,824,876,877,878],
 'FER':[408,409,560,561,562,563,637,644,655,657,822,874,875],
 'NAF':[i for i,s in STATES.items() if s['owner'] in {'FRA','ITA'} and s['cores']&{'MOR','ALG','TUN','LBA'}],
 'CMT':[777],
 'FIN':[215,216],
 'PAK':[i for i,s in STATES.items() if s['owner']=='RAJ' and 'PAK' in s['cores'] and i not in {430,787}],
}
assigned={}
for tag,ids in ASSIGN.items():
    for sid in ids:
        assert sid in STATES,('unknown state',tag,sid)
        assert sid not in assigned,('duplicate state',sid,tag,assigned.get(sid))
        assigned[sid]=tag
        if tag in {'KAZ','TRK','SIB','FER'}:assert STATES[sid]['owner']=='SOV',(tag,sid,STATES[sid]['owner'])
CAPITALS={'KAZ':586,'SIB':570,'CAU':230,'TRK':405,'NAF':458,'CMT':777,'FER':408,'USA':361,'JAP':282,'SOV':219,'MEX':277,'BRA':500,'ARG':278,'CHI':1035,'MAN':328,'RAJ':439,'PAK':443,'FIN':111}
INDUSTRY={'KAZ':(4,2),'SIB':(6,3),'CAU':(4,2),'NAF':(5,2),'CMT':(3,1),'FER':(3,2),'PAK':(5,3),'TRK':(4,2),'MAN':(4,2)}
AIRCRAFT={'USA':100,'JAP':80,'CHI':30,'RAJ':40,'PAK':20}
def set_number(body,key,value):
    pat=r'(?m)^(\s*)'+re.escape(key)+r'\s*=\s*\d+(?:\.\d+)?'
    if re.search(pat,body):return re.sub(pat,lambda m:m[1]+key+' = '+str(value),body,count=1)
    return '\n\t\t\t'+key+' = '+str(value)+body
def state_text(sid,tag,industry=None):
    source=STATES[sid];s=source['text'];_,a,b,_=span(s,'history');h=s[a:b]
    h=re.sub(r'\bowner\s*=\s*\w+','owner = '+tag,h,count=1)
    h=re.sub(r'\bcontroller\s*=\s*\w+','controller = '+tag,h,count=1)
    if not re.search(r'\bcontroller\s*=',masked(h)):h='\n\t\tcontroller = '+tag+h
    if tag not in source['cores']:h+='\n\t\tadd_core_of = '+tag+'\n'
    if industry:
        _,ba,bb,_=span(h,'buildings');body=h[ba:bb];added_slots=0
        for key,val in zip(['industrial_complex','arms_factory'],industry):
            old=re.search(r'\b'+key+r'\s*=\s*(\d+)',masked(body));previous=int(old[1]) if old else 0
            added_slots+=max(0,val-previous);body=set_number(body,key,max(val,previous))
        h=h[:ba]+body+h[bb:]
        if added_slots:h+='\n\t\tadd_extra_state_shared_building_slots = '+str(added_slots)+'\n'
    if tag in AIRCRAFT and CAPITALS[tag]==sid:
        _,ba,bb,_=span(h,'buildings');body=h[ba:bb]
        air=re.search(r'\bair_base\s*=\s*(\d+)',masked(body))
        if not air or int(air[1])<1:h=h[:ba]+set_number(body,'air_base',1)+h[bb:]
    s='# PROVISIONAL 1924 PLAYTEST FIXTURE; geometry and native resources preserved.\n'+s[:a]+h+s[b:]
    return s
def state_output(sid,tag,industry=None):
    source=STATES[sid];s=state_text(sid,tag,industry)
    write('history/states/'+source['path'].name,s)
    MANIFEST['states'][str(sid)]={'name_key':'STATE_'+str(sid),'installed_name':STATE_NAMES.get(sid,source['path'].stem),'installed_owner':source['owner'],'fixture_owner':tag,'source_file':source['path'].name,'provinces':source['provinces'],'victory_points':source['vps']}
    source['fixture_owner']=tag
# Remove only the exact old world-generated enclave override. Never delete an
# altered history (including somebody else's map-spike changes) by filename.
# Removing this mod override restores the installed TUR history and all its
# native cores, rather than leaving a ghost CAU core on Tunceli.
obsolete=ROOT/'history/states'/STATES[353]['path'].name
if obsolete.exists():
    assert obsolete.resolve().parent==(ROOT/'history/states').resolve()
    expected=state_text(353,'CAU').replace('\r\n','\n').encode('utf8')
    native=STATES[353]['path'].read_bytes()
    if obsolete.read_bytes() in [expected,native]:obsolete.unlink()
    else:raise RuntimeError('State353 override has independent changes: inspect before restoring native TUR history.')
for sid,tag in assigned.items():state_output(sid,tag,INDUSTRY.get(tag) if CAPITALS.get(tag)==sid else None)
for tag,industry in INDUSTRY.items():
    sid=CAPITALS[tag]
    if sid not in assigned:state_output(sid,tag,industry)
for tag in AIRCRAFT:
    sid=CAPITALS[tag]
    if str(sid) not in MANIFEST['states'] and not re.search(r'\bair_base\s*=\s*[1-9]',masked(STATES[sid]['text'])):state_output(sid,tag)

families=['democratic','aof_social_democracy','communism','aof_conservatism','neutrality','fascism']
GOV={'KAZ':'democratic','SIB':'democratic','CAU':'democratic','TRK':'neutrality','NAF':'neutrality','CMT':'neutrality','FER':'neutrality','USA':'democratic','JAP':'aof_conservatism','SOV':'communism','MEX':'democratic','BRA':'democratic','ARG':'democratic','CHI':'neutrality','MAN':'neutrality','RAJ':'democratic','PAK':'neutrality','FIN':'democratic'}
DIVS={'USA':30,'JAP':26,'SOV':30,'KAZ':8,'SIB':12,'CAU':8,'TRK':7,'NAF':10,'CMT':2,'FER':7,'MAN':9,'PAK':12,'RAJ':18,'MEX':12,'BRA':12,'ARG':10,'CHI':24,'FIN':8}
SLOTS={'USA':4,'JAP':4,'SOV':3,'KAZ':2,'SIB':3,'CAU':2,'TRK':2,'NAF':2,'CMT':2,'FER':2,'MAN':2,'PAK':2,'RAJ':3,'MEX':3,'BRA':3,'ARG':3,'CHI':3,'FIN':3}
LEADERS={'democratic':('Гражданский кабинет','Civilian Cabinet','aof_constitutional_federalism'),'aof_social_democracy':('Совет социальных реформ','Social Reform Council','aof_parliamentary_socialism'),'communism':('Совет народных комиссаров','Council of People’s Commissars','aof_soviet_centralism'),'aof_conservatism':('Конституционный кабинет','Constitutional Cabinet','aof_parliamentary_conservatism'),'neutrality':('Временная государственная администрация','Interim State Administration','aof_bureaucratic_technocracy'),'fascism':('Национальный исполнительный совет','National Executive Council','aof_national_revolution')}
for tag,(en,ru,color,culture) in CUSTOM.items():
    write('common/countries/AOF '+tag+'.txt','graphical_culture = '+culture+'_gfx\ngraphical_culture_2d = '+culture+'_2d\ncolor = { '+' '.join(map(str,color))+' }\n')
    for family in families:
        LOC[tag+'_'+family]=(ru,en);LOC[tag+'_'+family+'_DEF']=(ru,en);LOC[tag+'_'+family+'_ADJ']=(ru,en)
    LOC[tag]=(ru,en);LOC[tag+'_DEF']=(ru,en);LOC[tag+'_ADJ']=(ru,en)
write('common/country_tags/aof_v03_world.txt',''.join(tag+' = "countries/AOF '+tag+'.txt"\n' for tag in CUSTOM))
# Alash is the approved name; remaining geography and institutional labels are fixtures.
for f in families:
    for suffix in ['','_DEF']:
        LOC['KAZ_'+f+suffix]=('Алаш Республикасы','Alash Republic')
    LOC['KAZ_'+f+'_ADJ']=('Алашский','Alash')
for tag,ru,en,adj_ru,adj_en in [
    ('SOV','Советская Россия','Soviet Russia','Российский','Russian'),
    ('RAJ','Индия','India','Индийский','Indian'),
]:
    for suffix in ['','_DEF']:LOC[tag+suffix]=(ru,en)
    LOC[tag+'_ADJ']=(adj_ru,adj_en)
    for family in families:
        for suffix in ['','_DEF']:LOC[tag+'_'+family+suffix]=(ru,en)
        LOC[tag+'_'+family+'_ADJ']=(adj_ru,adj_en)

BASE_TECH='infantry_weapons = 1 tech_support = 1 tech_engineers = 1 tech_recon = 1 gw_artillery = 1'
NAVAL_TECH='early_ship_hull_light = 1 early_ship_hull_heavy = 1 basic_battery = 1 basic_torpedo = 1 basic_fire_control_system = 1 mtg_transport = 1'
LEGACY_TECH='early_destroyer = 1 early_battleship = 1 transport = 1'
def country_file(tag):
    files=list((GAME/'history/countries').glob(tag+' - *.txt'));assert len(files)==1,(tag,files)
    return files[0].name
def country_history(tag):
    family=GOV[tag];cap=CAPITALS[tag];text='# PROVISIONAL 1924 PLAYTEST SETUP; institutions replace unapproved named leaders.\n'
    text+=f'capital = {cap}\noob = "aof_v03_{tag}_1924"\nset_research_slots = {SLOTS[tag]}\nset_stability = 0.55\nset_war_support = 0.25\n'
    text+='set_popularities = { '+' '.join(f+' = '+str(70 if f==family else 6) for f in families)+' }\n'
    text+='set_politics = { ruling_party = '+family+' elections_allowed = '+('yes' if family in ['democratic','aof_social_democracy','aof_conservatism'] else 'no')+' last_election = "1924.9.1" election_frequency = 48 }\n'
    text+='set_technology = { '+BASE_TECH+(' infantry_weapons1 = 1 basic_machine_tools = 1' if tag in ['USA','JAP','SOV','FIN'] else '')+' }\n'
    # Institutions for all six families avoid auto-generated historical personalities after a route changes government.
    for f,(ru,en,ideology) in LEADERS.items():
        key='aof_world_'+tag+'_'+f+'_cabinet';LOC[key]=(ru,en)
        text+='create_country_leader = { name = "'+key+'" desc = "" picture = "gfx/leaders/leader_unknown.dds" expire = "1960.1.1" ideology = '+ideology+' traits = { } }\n'
    text+='set_grand_doctrine = grand_battleplan\nstarting_train_buffer = 5\nset_fuel_ratio = 0.7\n'
    if tag in ['USA','JAP']:
        text+='if = { limit = { has_dlc = "Man the Guns" } set_technology = { '+NAVAL_TECH+' } }\n'
        text+=naval_variants(tag)
        text+='if = { limit = { has_dlc = "Man the Guns" } set_naval_oob = "aof_v03_'+tag+'_naval_mtg" }\n'
        text+='if = { limit = { NOT = { has_dlc = "Man the Guns" } } set_technology = { '+LEGACY_TECH+' } set_naval_oob = "aof_v03_'+tag+'_naval_legacy" }\n'
    if tag in AIRCRAFT:
        text+=early_air_setup(tag)
        text+='if = { limit = { NOT = { has_dlc = "By Blood Alone" } } set_technology = { early_fighter = 1 } set_air_oob = "aof_v03_'+tag+'_air_legacy" }\n'
    if tag in ['USA','SOV']:
        text+='if = { limit = { has_dlc = "No Step Back" } set_technology = { gwtank_chassis = 1 basic_light_tank_chassis = 1 } }\nif = { limit = { NOT = { has_dlc = "No Step Back" } } set_technology = { gwtank = 1 basic_light_tank = 1 } }\n'
    if tag=='SOV':
        # Compatibility version zero, not a late historical Soviet design.
        # All modules are enabled by native 1918 chassis / Great War artillery.
        modules='main_armament_slot = tank_small_cannon turret_type_slot = tank_light_one_man_tank_turret suspension_type_slot = tank_bogie_suspension armor_type_slot = tank_riveted_armor engine_type_slot = tank_gasoline_engine'
        text+='if = { limit = { has_dlc = "No Step Back" } create_equipment_variant = { name = "AOF Light Armour 1924" type = light_tank_chassis_1 modules = { '+modules+' } }'
        # Native TUR_1936_nsb.txt:162 identifies a Soviet export by NAME,
        # not by numeric version zero. Preserve that lookup using obsolete
        # early equipment, without importing its 1933 modules or MIO.
        text+=' create_equipment_variant = { name = "T-26TU mod. 1933" type = light_tank_chassis_1 obsolete = yes modules = { '+modules+' } } }\n'
    filename=country_file(tag) if tag not in CUSTOM else tag+' - AOF '+tag+'.txt'
    write('history/countries/'+filename,text)

def army(tag):
    states=[i for i,s in STATES.items() if s.get('fixture_owner',s['owner'])==tag];assert CAPITALS[tag] in states,(tag,'lost capital')
    cap=CAPITALS[tag];locations=[]
    for sid in [cap]+[x for x in states if x!=cap]:
        s=STATES[sid];locations.append((sid,s['vps'][0][0] if s['vps'] else s['provinces'][0]))
    count=DIVS[tag];text='division_template = { name = "AOF Territorial Infantry" regiments = { '
    text+=' '.join('infantry = { x = '+str(x)+' y = '+str(y)+' }' for x in range(2) for y in range(3))+' } }\nunits = {\n'
    deployed=[]
    for i in range(count):
        sid,prov=locations[i%len(locations)];assert prov in STATES[sid]['provinces']
        text+=' division = { name = "'+tag+' '+str(i+1)+'" location = '+str(prov)+' division_template = "AOF Territorial Infantry" start_experience_factor = 0.15 start_equipment_factor = 0.85 }\n';deployed.append({'state':sid,'province':prov})
    text+='}\n';write('history/units/aof_v03_'+tag+'_1924.txt',text)
    MANIFEST['countries'][tag]={'states':states,'capital_state':cap,'capital_province':locations[0][1],'divisions':count,'deployment':deployed,'government':GOV[tag],'research_slots':SLOTS[tag],'provisional':True}

def naval_variants(tag):
    out='if = { limit = { has_dlc = "Man the Guns" }\n'
    for key,hull,battery,engine,armor in [('Escort','ship_hull_light_1','ship_light_battery_1','light_ship_engine_1',None),('Capital','ship_hull_heavy_1','ship_heavy_battery_1','heavy_ship_engine_1','ship_armor_bb_1')]:
        modules='fixed_ship_battery_slot = '+battery+' fixed_ship_anti_air_slot = ship_anti_air_1 fixed_ship_fire_control_system_slot = ship_fire_control_system_0 fixed_ship_engine_slot = '+engine
        if armor:modules+=' fixed_ship_armor_slot = '+armor
        else:modules+=' fixed_ship_torpedo_slot = ship_torpedo_1'
        out+='create_equipment_variant = { name = "AOF '+key+' 1924" type = '+hull+' modules = { '+modules+' } }\n'
    return out+'}\n'

def early_air_setup(tag):
    fighter='fixed_main_weapon_slot = light_mg_2x engine_type_slot = engine_1_1x special_type_slot_1 = empty'
    out='if = { limit = { has_dlc = "By Blood Alone" } set_technology = { iw_small_airframe = 1 engines_1 = 1 aa_lmg = 1 aircraft_construction = 1'+(' early_bombs = 1' if tag=='USA' else '')+' }\n'
    if tag=='USA':
        # Foreign native OOBs request these exact names. They are obsolete
        # compatibility aliases using early modules, not approved 1924 names.
        for name in ['P-6','P-26A']:
            out+='create_equipment_variant = { name = "'+name+'" type = small_plane_airframe_0 modules = { '+fighter+' } obsolete = yes }\n'
        out+='create_equipment_variant = { name = "O2U" type = small_plane_cas_airframe_0 modules = { fixed_main_weapon_slot = bomb_locks fixed_auxiliary_weapon_slot_1 = light_mg_2x engine_type_slot = engine_1_1x } obsolete = yes }\n'
    out+='create_equipment_variant = { name = "AOF Scout Fighter 1924" type = small_plane_airframe_0 modules = { '+fighter+' } }\nset_air_oob = "aof_v03_'+tag+'_air_bba" }\n'
    return out

def navy(tag):
    # Native base provinces read from the installed fleet, then checked for ownership.
    native=(GAME/'history/units'/(f'{tag}_1936_naval_mtg.txt' if tag=='USA' else 'JAP_1936_naval.txt')).read_text(encoding='utf-8-sig')
    base=int(re.search(r'naval_base\s*=\s*(\d+)',native)[1])
    sid=next(i for i,s in STATES.items() if base in s['provinces']);assert STATES[sid].get('fixture_owner',STATES[sid]['owner'])==tag
    for mode in ['mtg','legacy']:
        ships=[]
        for kind,count in [('destroyer',20 if tag=='USA' else 16),('battleship',6 if tag=='USA' else 5)]:
            hull=('ship_hull_light_1' if kind=='destroyer' else 'ship_hull_heavy_1') if mode=='mtg' else ('destroyer_1' if kind=='destroyer' else 'battleship_1')
            variant=' version_name = "AOF '+('Escort' if kind=='destroyer' else 'Capital')+' 1924"' if mode=='mtg' else ''
            for j in range(count):ships.append('ship = { name = "'+tag+' '+kind+' '+str(j+1)+'" definition = '+kind+' start_experience_factor = 0.2 equipment = { '+hull+' = { amount = 1 owner = '+tag+variant+' } } }')
        text='units = { fleet = { name = "1924 Training Fleet" naval_base = '+str(base)+' task_force = { name = "Home Squadron" location = '+str(base)+' '+'\n'.join(ships)+' } } }\n'
        write('history/units/aof_v03_'+tag+'_naval_'+mode+'.txt',text)
    MANIFEST['countries'][tag]['naval_base']={'province':base,'state':sid};MANIFEST['countries'][tag]['naval_fixture']='26 ships' if tag=='USA' else '21 ships'

for tag in CAPITALS:army(tag);country_history(tag)
for tag in ['USA','JAP']:navy(tag)
for tag,number in AIRCRAFT.items():
    sid=CAPITALS[tag]
    for mode,equipment in [('bba','small_plane_airframe_0'),('legacy','fighter_equipment_0')]:
        variant=' version_name = "AOF Scout Fighter 1924"' if mode=='bba' else ''
        text='air_wings = { '+str(sid)+' = { '+equipment+' = { owner = "'+tag+'" amount = '+str(number)+variant+' } } }\n'
        write('history/units/aof_v03_'+tag+'_air_'+mode+'.txt',text)
    MANIFEST['countries'][tag]['air_fixture']={'state':sid,'early_fighters':number,'modes':['bba','legacy']}

# Procedural recruits need explicit pools for new tags even when every cabinet
# is an anonymous institution. Copy only native personal-name fields, not
# operations or any historical country leader. These are technical defaults.
NAME_POOL_SOURCES={'SIB':'SOV','CAU':'GEO','TRK':'UZB','NAF':'MOR','CMT':'TOG'}
def procedural_names():
    native=(GAME/'common/names/00_names.txt').read_text(encoding='utf-8-sig')
    out='# Provisional procedural-name pools from this same game installation; not historical leaders or approved ethnic composition.\n'
    for tag,source in NAME_POOL_SOURCES.items():
        _,a,b,_=span(native,source);body=native[a:b];out+=tag+' = {\n'
        for field in ['male','female','surnames','callsigns']:
            if re.search(r'\b'+field+r'\s*=\s*\{',masked(body)):
                start,_,_,end=span(body,field);out+=body[start:end]+'\n'
        out+='}\n'
    return out
write('common/names/aof_v03_world.txt',procedural_names())

# Original geometric placeholders: uncompressed 32-bit BGRA TGA, opaque alpha.
# The engine rejected 24-bit flags during the first actual boot. Change the
# authoring function only while a debug game is open; regenerate on cold build.
def tga(width,height,colors):
    header=struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,width,height,32,40)
    data=bytearray()
    for y in range(height):
        for x in range(width):
            rgb=colors[(y*3)//height]
            if width//2-width//14 <= x <= width//2+width//14:rgb=(235,225,185)
            data.extend(reversed(rgb))
            data.append(255)
    return header+data
def binary(path,data):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists() or p.read_bytes()!=data:p.write_bytes(data)
for tag,(_,_,color,_) in CUSTOM.items():
    colors=[tuple(max(0,c-35) for c in color),color,tuple(min(255,c+35) for c in color)]
    for folder,w,h in [('',82,52),('medium/',41,26),('small/',10,7)]:
        data=tga(w,h,colors)
        for suffix in ['']+['_'+f for f in families]:binary('gfx/flags/'+folder+tag+suffix+'.tga',data)
# Native same-installation flags for added ideology families. All tags, including
# releasables, need a fallback because six-family governments can change in play.
for folder in ['', 'medium/', 'small/']:
    native=GAME/'gfx/flags'/folder
    tags={p.name[:3] for p in native.glob('???_democratic.tga')}
    for tag in tags:
        source=native/(tag+'_democratic.tga')
        if source.exists():
            for family in ['aof_social_democracy','aof_conservatism']:binary('gfx/flags/'+folder+tag+'_'+family+'.tga',source.read_bytes())

LOC['AOF_BROKEN_PEACE_NAME']=('Хрупкий мир: 1924','A Fragile Peace: 1924')
LOC['AOF_BROKEN_PEACE_DESC']=('Десять лет Великой войны истощили старые державы и дали новым государствам шанс на самостоятельность. Европа ищет путь к восстановлению, США решают судьбу военной прибыли, Япония — будущее своей сферы влияния. Молодым республикам предстоит превратить независимость в работающие учреждения, промышленность и способность защищать свой выбор. Мир заключён, но его порядок ещё только предстоит создать.','Ten years of the Great War exhausted the old powers and gave new states a chance at independence. Europe seeks recovery, the United States decides how to use its wartime wealth, and Japan must settle the future of its sphere. Young republics must turn independence into working institutions, industry and the ability to defend their choices. Peace has been signed; its order remains to be built.')
CAMPAIGN_STORIES={
 'KAZ':('Независимость нужно построить. Свяжите центры Алаш дорогами, подготовьте учителей и инженеров, превратите известные недра в собственное машиностроение. Республика договора, земельный компромисс или чрезвычайный мандат определят внутренний курс; выбор промышленных партнёров и внешних маршрутов — цену самостоятельности.','Independence must be built. Connect Alash’s centres by road, train teachers and engineers, and turn known deposits into domestic machine building. A constitutional compact, land reform or emergency mandate will shape government; industrial partners and external routes will determine the price of autonomy.'),
 'SIB':('Огромной стране нужно общее расписание. Восстановите магистраль, договоритесь с регионами и найдите надёжный выход к внешним рынкам. Постройте гражданскую Сибирь, предложите российским республикам добровольный договор или доверьте охрану коммуникаций военной директории.','A vast country needs a common timetable. Restore the trunk line, reach terms with the regions and secure access to foreign markets. Build a civilian Siberia, offer the Russian republics a voluntary compact, or entrust the communications network to a military directorate.'),
 'CAU':('Стратегический путь делает федерацию нужной соседям и уязвимой перед их требованиями. Разделите полномочия и доходы между участниками или укрепите единый центр. Собственная охрана и ясные правила транзита должны позволить Кавказу торговать, не превращаясь в чужую базу.','A strategic route makes the federation valuable to its neighbours and vulnerable to their demands. Share powers and revenues among its members or strengthen the centre. Domestic security and clear transit rules must let the Caucasus trade without becoming another power’s base.'),
 'TRK':('Общий союз нуждается в новом договоре участников. Определите полномочия местных правительств, согласуйте оборону и решите, что удерживает страну вместе. Можно укрепить союз или договориться о мирном разделе, сохранив правопреемственный кабинет в Ташкенте.','The union needs a new compact among its members. Define local governments’ powers, coordinate defence and decide what holds the country together. Strengthen the union or negotiate a peaceful separation while retaining a continuity cabinet in Tashkent.'),
 'NAF':('Общая победа над колониальным угнетением ещё должна стать повседневной свободой. Восстановите дороги, школы и гражданское управление, сохраняя равноправие участников. Защищённый нейтралитет и посредничество дадут содружеству собственный голос, но просьбы о военной помощи испытают пределы этого курса.','Victory over colonial oppression must become everyday freedom. Restore roads, schools and civil administration while preserving equality among members. Armed neutrality and mediation can give the commonwealth its own voice, but requests for military aid will test that policy’s limits.'),
 'CMT':('Страну создали для военных поставок, но война закончилась. Кто теперь представляет её жителей и кому служат склады, дороги и предприятия? Постройте гражданскую республику, сохраните коммерческий устав или ищите внешнюю гарантию — каждый путь потребует расплатиться по старым обязательствам.','The country was created for wartime supply, but the war has ended. Who now represents its residents, and whom do its warehouses, roads and workshops serve? Build a civilian republic, preserve the commercial charter or seek an external guarantee: every route must reckon with old obligations.'),
 'FER':('Владивосток может стать торговыми воротами между соперниками, а не только военным плацдармом. Подготовьте собственные кадры, расширьте связи с Сибирью и пересмотрите условия японской гарантии. Договорная самостоятельность требует встречного согласия; отказ оставляет выбор нового курса за местным правительством.','Vladivostok can become a trading gateway between rivals rather than merely a military foothold. Train local personnel, expand links with Siberia and revisit the Japanese guarantee. Negotiated autonomy requires agreement; refusal leaves the local government to choose its next course.'),
 'USA':('Кому достанется прибыль десятилетия войны? Превратите научное и промышленное преимущество в гражданский достаток, долгие внешние контракты или влияние в Западном полушарии. Споры о труде, крупных корпорациях и пределах президентской власти определят, какой республикой станет Америка после войны.','Who will receive the profits of a decade of war? Turn scientific and industrial strength into civilian prosperity, long foreign contracts or influence in the Western Hemisphere. Disputes over labour, large corporations and presidential power will determine America’s postwar republic.'),
 'JAP':('Две зависимости, два договора и всё новые требования командования. Выберите устойчивую договорную сферу, материковый военный мандат или морской приоритет. Отношения с Маньчжурией, Владивостоком и китайскими правительствами покажут, способна ли империя удерживать влияние без бесконечного расширения обязательств.','Two dependencies, two treaties and mounting demands from the field commands. Choose a stable treaty sphere, a continental military mandate or maritime priorities. Relations with Manchuria, Vladivostok and Chinese governments will test whether the empire can maintain influence without endlessly expanding its commitments.'),
 'SOV':('Революция должна научиться жить. Гражданская война закончилась, но хозяйство и государственные учреждения ещё несут её наследие. Сделайте ставку на жизнеспособную республику, предложите соседям добровольный союз или вернитесь к внешнему революционному давлению — и определите место местных советов в новой системе.','The revolution must learn to live. The civil war has ended, but production and institutions still bear its legacy. Prioritise a viable republic, offer neighbours a voluntary union or renew revolutionary pressure abroad, while deciding the place of local councils in the new order.'),
 'MEX':('Нефть принадлежит земле, но кто пишет договор? Согласуйте земельную реформу, права труда и условия иностранного заказа. Предсказуемый пересмотр контрактов, собственная переработка или офицерское собирание государства дадут разные ответы; спор с США допускает компромисс, но не гарантирует его.','Oil belongs to the land, but who writes the contract? Reconcile land reform, labour rights and foreign orders. Predictable contract revision, domestic refining or officer-led consolidation offer different answers. The dispute with the United States permits compromise without guaranteeing it.'),
 'BRA':('Экспорт принёс доход, но ещё не объединил республику. Свяжите внутренние рынки и решите, кому служит федеральное правительство: гражданам, программе офицерской модернизации или договору регионов. На южноамериканской конференции предложите равноправную оборону либо попытайтесь установить собственные правила.','Exports brought income without uniting the republic. Connect internal markets and decide whether federal government serves civilian reform, officer-led modernisation or a compact of regions. At a South American conference, offer equal defence cooperation or try to impose your own rules.'),
 'ARG':('Накормить мир недостаточно, чтобы влиять на него. Когда старый покупатель слабеет, экспортную выручку можно направить в переработку и машины, лигу равных республик или южноатлантический флот. Сотрудничество с Бразилией остаётся возможным, но первенство на континенте не принадлежит никому по праву.','Feeding the world is not enough to influence it. As the old buyer weakens, export earnings can fund processing and machines, a league of equal republics or a South Atlantic fleet. Cooperation with Brazil remains possible, but no country possesses a natural right to continental leadership.'),
 'CHI':('Единство не должно достаться за чужую цену. Согласуйте фронт и снабжение, разберите иностранные обязательства и определите отношения с региональными правительствами. Договорная республика, единая армия или земельная реформа предлагают разные дороги к общему государству.','Unity must not come at a foreign price. Coordinate the front and supplies, examine external obligations and settle relations with regional governments. A negotiated republic, a unified army or land reform offer different roads to a common state.'),
 'MAN':('Промышленность и железные дороги дают возможности, но условия японской опеки ограничивают самостоятельность. Подготовьте местных специалистов и собственную промышленную службу, затем обсудите полномочия гарнизонов. Договор о правах правительства должен стать реальным соглашением, а не обещанием покровителя.','Industry and railways bring opportunity, while Japanese protection limits autonomy. Train local specialists and build an industrial administration before negotiating garrison powers. Government rights must become an actual agreement rather than a patron’s promise.'),
 'RAJ':('Война с Пакистаном требует снабжения фронта, но не должна навсегда определять устройство Индии. Удержите гражданское управление, проверьте условия перемирия и решите, какие обязательства страна готова принять после войны. Мир возможен лишь при встречном согласии.','War with Pakistan demands front-line supply without permanently determining India’s government. Preserve civilian administration, examine armistice terms and decide which obligations the country should accept after the fighting. Peace requires agreement on both sides.'),
 'PAK':('Выживание не должно означать постоянную опеку. Свяжите армию с тылом, согласуйте помощь Ирана и Афганистана и выработайте общие правила снабжения. Добейтесь самостоятельного мира с Индией или подготовьте региональное оборонное сотрудничество.','Survival must not mean permanent tutelage. Connect the army to its hinterland, coordinate Iranian and Afghan aid and agree common supply rules. Seek an independent peace with India or prepare regional defence cooperation.'),
 'FIN':('Контроль над Карелией требует повседневного управления, а не только пограничных частей. Дайте местным общинам представительство, восстановите дороги и школы и укрепите признанную границу. Финляндия может защищать свои интересы, не превращая соседство с Россией в обязательную новую войну.','Control of Karelia requires everyday government as well as border troops. Give local communities representation, restore roads and schools and strengthen a recognised frontier. Finland can defend its interests without turning its proximity to Russia into an inevitable new war.'),
}
bookmark='bookmarks = { bookmark = { name = "AOF_BROKEN_PEACE_NAME" desc = "AOF_BROKEN_PEACE_DESC" date = 1924.9.1.12 picture = "GFX_select_date_1936" default_country = "KAZ" default = yes filters = { continent } scrollable_country_list = yes\n'
for tag in CAPITALS:
    key='aof_world_'+tag+'_bookmark';LOC[key]=CAMPAIGN_STORIES[tag]
    bookmark+='"'+tag+'" = { history = "'+key+'" ideology = '+GOV[tag]+' version = base_game }\n'
write('common/bookmarks/aof_broken_peace.txt',bookmark+'} }\n')
localize('aof_v03_world',LOC)
write('docs/design_v0_3/WORLD_MANIFEST.json',json.dumps(MANIFEST,ensure_ascii=False,indent=2)+'\n')
world_notes='''# Provisional 1924 playtest world

These are explicitly provisional fixtures, not approved historical geography, capitals, flags or personnel. The immutable lore is represented through separate independent Kazakhstan, Siberia, Caucasus and Turkestan; distinct Japanese dependencies are configured by the startup owner. No map geometry is changed.

The generator reads installed state history and preserves native resources, population, geometry and infrastructure. Only owner/controller, additional fixture-country cores, minimum capital industry and matching additional building slots change; Nanjing and Sind additionally receive one airbase level for their early fighter wings. Future-dated state blocks are removed from changed states so 1939 history cannot silently reverse the fixture. Detailed state IDs, installed names, source owners, capital provinces and troop placements are in WORLD_MANIFEST.json.

KAZ uses installed Soviet-owned Kazakh-core states. TRK uses installed Soviet-owned Uzbek, Turkmen, Tajik and Kyrgyz cores. CAU includes states 229–235, 821, 826–828 and one Turkish border region, state 354 (Trabzon). The owner explicitly limited the Turkish allocation to one or two adjacent border regions; the generator chooses the minimal one. Native provinces.bmp confirms that state 354 directly borders both Armenia 230 and Georgia 231: Ardahan province 10403 touches Gyumri 12441 and Georgian province 3656. State 354 contains Trabzon 9932, Kars 10472, Gümüşhane 3979 and Erzurum 11853. The previous state 353 allocation was an erroneous enclave: its filename says Erzurum, but its actual state name and victory points are Tunceli, Xarpêt and Erzîngan. The cold builder removes only its exact unmodified prior generated override, restoring native Turkish ownership and removing the added CAU core; independent edits cause a safe abort. State 355 is Samsun and does not border the Caucasian fixture. This limited-border instruction does not approve other provisional capitals or unspecified geography. SIB and FER use the reviewed explicit lists. Finland additionally owns Onega and Olonets, never Leningrad; Murmansk is retained by Soviet Russia because it is not Karelia. NAF combines French/Italian-owned Moroccan, Algerian, Tunisian and Libyan core territory, excludes Egypt and Spanish possessions. CMT temporarily occupies Togo state 777. Pakistan receives western native Pakistani cores; East Bengal 430 and contested North Kashmir 787 remain with India.

Eighteen named countries receive native six-battalion infantry formations placed in owned states; numbers and readiness are balance fixtures. Named 1936 historical leaders are replaced by localised generic institutional cabinets for all six political families. Initial research uses early native technology and small research-slot counts. USA receives the 1924 light tank technology, not a fabricated model designation. USA/Japan have compact original early naval fixtures with separate MTG/legacy definitions; these deliberately do not reproduce historical fleet sizes or import later-era ships. USA, Japan, China, India and Pakistan receive respectively 100, 80, 30, 40 and 20 early fighters, with separate BBA and legacy OOBs. Named equipment variants precede their OOB loads. All other countries retain installed history/OOB until separately curated.

Native foreign air OOBs still request USA variants P-6, P-26A and O2U: obsolete aliases with early modules preserve those references without endorsing their names as 1924 canon. Soviet Russia has a basic early light-chassis design and an obsolete same-module compatibility alias named "T-26TU mod. 1933", required by native Turkish OOB lookup; its name is not a 1924 historical assertion, and no 1933 improved modules or design bureau are imported. Procedural names for the five custom tags borrow native SOV/GEO/UZB/MOR/TOG personal-name pools; these technical defaults neither appoint historical leaders nor determine an approved population composition.

The owner separately authorised states 582 (Magnitogorsk), 652 (Orenburg) and 236 (Astrakhan) for Alash. Province corrections 4265/10185 to Ufa 651, 1334 to Zlatoust 573, and 3265/4324/227 to Kuybyshev 251 are applied by the isolated, backed-up state-edits stage after the world and Caspian generators. No other geography or capital is approved by that request. Astrakhan is distinct from Stavropol 235 and is outside the current canal corridor. Province IDs, railways and supply-node identities are retained.

Five custom tags use original geometric placeholder TGA flags in all sizes and political variants. Added ideology-family flags for native tags copy the corresponding democratic flag from this same local game installation; these are compatibility fallbacks, not approved vexillology. No third-party artwork or mods are used.

Parent startup owns national spirits, diplomatic dependencies, war setup and scenario-wide adjustments. This builder never edits on-actions. World files require a full game restart; no actual launch, load or error-log verification has been performed by this builder.
'''
world_notes+='\n| Tag | Capital state | Infantry divisions | Research slots |\n|---|---:|---:|---:|\n'
world_notes+=''.join(f'| {tag} | {CAPITALS[tag]} | {DIVS[tag]} | {SLOTS[tag]} |\n' for tag in CAPITALS)
world_notes+='\nStatic verification confirmed valid installed technology identifiers, province membership and owned capitals, unchanged state geometry/infrastructure, balanced braces, six-family popularity totals and flag dimensions. Repeated generation preserved bytes and modification times. These checks are not an in-game test.\n'
write('docs/design_v0_3/WORLD_SETUP.md',world_notes)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('World:',len(CAPITALS),'countries;',len(MANIFEST['states']),'changed states;',sum(DIVS.values()),'divisions')
    print('Assignments:',json.dumps(ASSIGN,ensure_ascii=True))
