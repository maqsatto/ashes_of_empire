"""Author optional, debug-only Caspian test fixtures. No startup ships.

--inspect is read-only. Default generation requires HOI4 closed and the applied
Caspian map override. Parent runs this with the cold-build batch, not live reload.
"""
from pathlib import Path
import argparse
import json
import re
import subprocess
import os
from contentlib import ROOT, write, localize
from build_v03_compat import parse, scalar
from build_v03_caspian import MemoryScript, children, decode, PORTS, ROUTE, STATE_FILES

GAME=Path('C:/Hearts of Iron IV')
GUARD='is_debug = yes is_ai = no'
VARIANT='AOF Debug Escort 1924'


def port_guard(state,province):
    return f'owns_state = {state} controls_province = {province} {state} = {{ is_owned_by = ROOT is_coastal = yes any_province_building_level = {{ province = {{ id = {province} }} building = naval_base level > 0 }} }}'


def validate_inputs():
    # The optional fixture must never be generated into the non-map baseline.
    definition=ROOT/'map/definition.csv'
    adjacency=ROOT/'map/adjacencies.csv'
    if not definition.exists() or not adjacency.exists(): raise RuntimeError('Apply the isolated Caspian map override before authoring its debug fleet fixture')
    rows={int(p[0]):p for line in definition.read_text(encoding='utf-8-sig').splitlines() if len(p:=line.split(';'))>=8 and p[0].isdigit()}
    for ident in (843,1050,1271,1496):
        if rows[ident][4:7]!=['sea','true','ocean']: raise ValueError(f'Caspian province{ident} is not the applied sea override')
    if '1050;8308;sea;3672;' not in adjacency.read_text(encoding='utf-8-sig'): raise ValueError('Expected accepted Grozny-Krasnodar canal adjacency is absent')
    modules=(GAME/'common/units/equipment/modules/00_ship_modules.txt').read_text(encoding='utf-8-sig')
    for ident in ['ship_light_battery_1','ship_anti_air_1','ship_fire_control_system_0','light_ship_engine_1','ship_torpedo_1']:
        if not re.search(r'\b'+ident+r'\s*=\s*\{',modules):raise ValueError(f'Installed module absent: {ident}')
    for state,tag,province,water,land,sea in PORTS:
        if rows[province][4:6]!=['land','true']:raise ValueError(f'Fixture port{province} lacks actual coastal definition')
        data=(ROOT/STATE_FILES[state]).read_bytes()
        st=children(parse(MemoryScript(decode(data),STATE_FILES[state])),'state')
        hist=children(st,'history');buildings=children(hist,'buildings')
        province_block=children(buildings,str(province))
        if scalar(hist,'owner')!=tag or int(scalar(province_block,'naval_base') or '0')<1:raise ValueError(f'Applied test base missing in state{state}')
    # These identifiers and OOB shapes were inspected in actual installed files.
    for mode,name,hull in [('mtg','ARG_1936_naval_mtg.txt','ship_hull_light_1'),('legacy','ARG_1936_naval_legacy.txt','destroyer_1')]:
        native=(GAME/'history/units'/name).read_text(encoding='utf-8-sig')
        if not re.search(r'\b'+hull+r'\s*=',native) or 'naval_base =' not in native:raise ValueError(f'Native OOB reference changed: {name}')
    gfx=(GAME/'interface/decisions.gfx').read_text(encoding='utf-8-sig')
    for icon in ['GFX_decision_category_generic_naval','GFX_decision_generic_research']:
        if icon not in gfx:raise ValueError(f'Installed decision sprite absent: {icon}')
    techfiles={p.name:p.read_text(encoding='utf-8-sig') for p in (GAME/'common/technologies').glob('*.txt')}
    alltech='\n'.join(techfiles.values())
    for tech in ['early_ship_hull_light','basic_battery','basic_torpedo','early_destroyer']:
        if not re.search(r'\b'+tech+r'\s*=\s*\{',alltech):raise ValueError(f'Installed technology absent: {tech}')


def build():
    validate_inputs()
    out={};loc={}
    category='aof_debug_caspian_fixture'
    loc[category]=('Тест Каспия: флот и канал','Caspian test: fleet and canal')
    loc[category+'_desc']=('Только отладка. Не исторический стартовый флот. Появление решения и запрос загрузки не доказывают работоспособность: проверьте корабль, базу, маршрут и журнал.','Debug only. These are not historical starting fleets. Decision visibility and a load request do not prove operation: inspect the ship, base, route and log.')
    out['common/decisions/categories/aof_debug_caspian_fixture.txt']=f'{category} = {{ icon = generic_naval allowed = {{ OR = {{ tag = KAZ tag = CAU }} }} visible = {{ {GUARD} OR = {{ tag = KAZ tag = CAU }} }} }}\n'
    text=category+' = {\n'
    for state,tag,province,water,land,sea in PORTS:
        ident='aof_debug_caspian_ship_'+tag.lower()
        flag='aof_debug_caspian_ship_requested_'+tag.lower()
        eligible=f'{GUARD} tag = {tag} NOT = {{ has_country_flag = {flag} }} '+port_guard(state,province)
        mtg_oob='aof_debug_caspian_'+tag.lower()+'_mtg'
        legacy_oob='aof_debug_caspian_'+tag.lower()+'_legacy'
        for mode,hull,version in [('mtg','ship_hull_light_1',' version_name = "'+VARIANT+'"'),('legacy','destroyer_1','')]:
            oob=mtg_oob if mode=='mtg' else legacy_oob
            out['history/units/'+oob+'.txt']=f'''# Debug-only fixture loaded by a guarded decision, never assigned in history.
units = {{ fleet = {{ name = "AOF Caspian Debug Fleet" naval_base = {province}
 task_force = {{ name = "AOF Test Escort" location = {province}
  ship = {{ name = "{tag} DEBUG Escort" definition = destroyer start_experience_factor = 0
   equipment = {{ {hull} = {{ amount = 1 owner = {tag}{version} }} }} }}
 }} }} }}
'''
        modules='fixed_ship_battery_slot = ship_light_battery_1 fixed_ship_anti_air_slot = ship_anti_air_1 fixed_ship_fire_control_system_slot = ship_fire_control_system_0 fixed_ship_engine_slot = light_ship_engine_1 fixed_ship_torpedo_slot = ship_torpedo_1'
        # Same early escort module choices as world.naval_variants, unique debug
        # variant name; do not import that module because it generates histories.
        effect=f'''if = {{ limit = {{ {eligible} }}
 if = {{ limit = {{ has_dlc = "Man the Guns" }}
  set_technology = {{ early_ship_hull_light = 1 basic_battery = 1 basic_torpedo = 1 }}
  create_equipment_variant = {{ name = "{VARIANT}" type = ship_hull_light_1 modules = {{ {modules} }} }}
  load_oob = "{mtg_oob}"
 }} else = {{ set_technology = {{ early_destroyer = 1 }} load_oob = "{legacy_oob}" }}
 set_country_flag = {flag}
 log = "AOF Caspian DEBUG: requested one {tag} escort at port {province}; verify actual fleet and docking."
}}'''
        text+=f''' {ident} = {{ icon = generic_research cost = 0
 allowed = {{ tag = {tag} }}
 visible = {{ {GUARD} tag = {tag} NOT = {{ has_country_flag = {flag} }} }}
 available = {{ {eligible} }}
 complete_effect = {{ {effect} }} ai_will_do = {{ factor = 0 }}
 }}
'''
        loc[ident]=(f'Тест: один эсминец у базы {province}',f'Test: one destroyer at base {province}')
        loc[ident+'_desc']=(f'Однократно запросить один ранний тестовый эсминец {tag} у принадлежащей и подконтрольной базы {province}. Режим MTG создаёт модульный эскорт; без DLC используется ранний обычный эсминец. Решение даёт только необходимые ранние технологии и корабль. Флаг означает запрос, не подтверждение появления. Это не канон и не проверка судоходства.',f'Request one early {tag} test destroyer once at the owned and controlled base {province}. MTG creates a modular escort; otherwise an early legacy destroyer is used. Grants only the needed early technologies and one ship. Its flag records the request, not confirmed spawning. This is neither canon nor proof of navigation.')
    loc['aof_debug_caspian_convoys']=('Тест: 20 конвоев для торгового маршрута','Test: 20 convoys for a trade route')
    loc['aof_debug_caspian_convoys_desc']=('Однократное отладочное пополнение. Затем оформите настоящий импорт и проверьте линию маршрута, расход конвоев и порт. Не подтверждает судоходство автоматически.','One debug-only allocation. Then place a real import order and inspect the route, convoy use and port. Does not automatically verify navigation.')
    text+=''' aof_debug_caspian_convoys = {
 icon = generic_research cost = 0 allowed = { tag = KAZ }
 visible = { is_debug = yes is_ai = no tag = KAZ NOT = { has_country_flag = aof_debug_convoys_requested } }
 available = { is_debug = yes is_ai = no tag = KAZ }
 complete_effect = { if = { limit = { is_debug = yes is_ai = no tag = KAZ NOT = { has_country_flag = aof_debug_convoys_requested } } add_equipment_to_stockpile = { type = convoy_1 amount = 20 producer = KAZ } set_country_flag = aof_debug_convoys_requested } }
 ai_will_do = { factor = 0 }
 }
'''
    corridor=' '.join('owns_state = '+str(s) for s in sorted(set(ROUTE.values())))+' '+' '.join('controls_province = '+str(p) for p in ROUTE)
    for closed in [False,True]:
        ident='aof_debug_caspian_'+('open_canal' if closed else 'close_canal')
        status='has_global_flag = aof_caucasian_canal_closed' if closed else 'NOT = { has_global_flag = aof_caucasian_canal_closed }'
        effect=('clr_global_flag' if closed else 'set_global_flag')+' = aof_caucasian_canal_closed'
        guard=f'{GUARD} tag = CAU {corridor}'
        text+=f''' {ident} = {{ icon = generic_research cost = 0 days_re_enable = 1
 allowed = {{ tag = CAU }}
 visible = {{ {GUARD} tag = CAU {status} }}
 available = {{ {guard} }}
 complete_effect = {{ if = {{ limit = {{ {guard} {status} }} {effect} log = "AOF Caspian DEBUG: canal {'open' if closed else 'closed'} flag requested; verify actual routing." }} }}
 ai_will_do = {{ factor = 0 }} }}
'''
        loc[ident]=(('Тест: открыть канал — сейчас закрыт','Test: open canal — currently closed') if closed else ('Тест: закрыть канал — сейчас открыт','Test: close canal — currently open'))
        loc[ident+'_desc']=(f'Изменяет только отладочный флаг закрытия нативного прохода. Все {len(ROUTE)} провинций коридора должны принадлежать и подчиняться Кавказу. Статус названия отражает флаг, а не проверенный маршрут. После изменения проверьте фактическое прохождение флота и торговли.',f'Changes only the native passage closure flag. The Caucasus must own and control all {len(ROUTE)} corridor provinces. The title reflects the flag, not a proven route. Check actual fleet and trade passage after changing it.')
    out['common/decisions/aof_debug_caspian_fixture.txt']=text+'}\n'
    for rel,content in out.items():
        parse(MemoryScript(content,rel))
        if 'set_global_flag = aof_caspian_navigation_verified' in content:raise ValueError('Debug fixture must never mark navigation verified')
    return out,loc


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect',action='store_true');args=parser.parse_args()
    out,loc=build()
    print(json.dumps({'mode':'READ_ONLY_INSPECTION' if args.inspect else 'GENERATE_WITH_GAME_CLOSED','runtime_script_outputs':list(out),'ships_per_tag':1,'tags':['KAZ','CAU'],'oob_modes':['mtg','legacy'],'decisions':5,'localisation_keys_per_language':len(loc),'navigation_verified':False},indent=2))
    if args.inspect:
        print('Validated in memory only; no runtime files written. Actual spawning/docking remains UNVERIFIED.');return
    if os.name!='nt':raise RuntimeError('Windows process check required')
    result=subprocess.run(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name hoi4 -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True,check=True)
    if int(result.stdout.strip()):raise RuntimeError('Close HOI4 before generating new debug fixture files')
    for rel,content in out.items():write(rel,content)
    localize('aof_debug_caspian_fixture',loc)


if __name__=='__main__':main()
