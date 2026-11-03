"""Build the complete supplied v0.3 playtest design. Run with HOI4 closed."""
from pathlib import Path
import runpy, subprocess, sys, re, json
from contentlib import write

ROOT=Path(__file__).resolve().parents[1]
BACKUPS=Path('C:/Users/maqsatto/.codex/backups/ashes_of_empires')

def stage(name,*arguments):
    subprocess.run([sys.executable,str(ROOT/'tools'/f'build_v03_{name}.py'),*arguments],check=True)

def prepare_once(name,directory,marker):
    backup=BACKUPS/directory
    if not (backup/marker).exists():
        stage(name,'--prepare-backup',str(backup))
    return backup

def main():
    if sys.platform=='win32':
        result=subprocess.run(['tasklist','/FI','IMAGENAME eq hoi4.exe','/FO','CSV','/NH'],capture_output=True,text=True)
        if 'hoi4.exe' in result.stdout.lower():
            raise SystemExit('Close HOI4 before building: idea/history reloads invalidate a live test.')
    # Snapshot the pre-edit state files before world generation replaces them.
    state_backup=prepare_once('state_edits','user-state-edits-20261103','manifest.json')
    for name in ['pacific','nations','world','diplomacy','partition','compat']:
        runpy.run_path(str(ROOT/'tools'/f'build_v03_{name}.py'),run_name='__main__')
    # World generation restores the baseline histories. Preserve the separately
    # authorized map spike and its port edits only through its guarded applier.
    spike=ROOT/'docs/design_v0_3/CASPIAN_SPIKE_MANIFEST.json'
    if spike.exists():
        backup=json.loads(spike.read_text(encoding='utf-8'))['backup_directory']
        subprocess.run([sys.executable,str(ROOT/'tools/build_v03_caspian.py'),
                        '--apply','--backup-dir',backup],check=True)
        runpy.run_path(str(ROOT/'tools/build_v03_debug.py'),run_name='__main__')
        # These stages compose on the upstream output. Their own guards reject
        # unrecorded manual changes and preserve immutable native geometry.
        stage('state_edits','--apply','--backup-dir',str(state_backup))
        regions=prepare_once('kaz_regions','kaz-regions-20261103','kaz_regions_backup_manifest.json')
        stage('kaz_regions','--apply','--backup-dir',str(regions))
        cities=prepare_once('cities','user-cities-20261103','city_backup_manifest.json')
        stage('cities','--apply','--backup-dir',str(cities))
        strategic=prepare_once('strategic','user-strategic-20261103','strategic_backup_manifest.json')
        stage('strategic','--apply','--backup-dir',str(strategic))
        visual=prepare_once('canal_visual','canal-visual-20261103-r2','canal_visual_backup.json')
        stage('canal_visual','--apply','--backup-dir',str(visual))
    # The coastal-port effect must resolve the FINAL effective province/state
    # membership, including the oblast splits, even on the first clean build.
    runpy.run_path(str(ROOT/'tools/build_v03_core.py'),run_name='__main__')
    for lang in ['english','russian']:
        for stem in ['aof','aof_kaz']:
            p=ROOT/f'localisation/{lang}/{stem}_l_{lang}.yml'
            if p.exists():
                text=p.read_text(encoding='utf-8-sig')
                text=re.sub(r'^\s+(?:KAZ_neutrality(?:_DEF)?|AOF_BROKEN_PEACE_NAME|AOF_BROKEN_PEACE_DESC):[^\n]*\n','',text,flags=re.M)
                write(p.relative_to(ROOT),text,True)
    write('common/on_actions/aof_startup.txt','# Legacy startup superseded by aof_v03_startup.txt.\n')
    tags=['KAZ','CAU','SIB','SOV','NAF','CMT','MEX','BRA','ARG','CHI','USA','JAP']
    setup='''on_actions = {
 on_startup = {
  effect = {
   if = {
    limit = { NOT = { has_global_flag = aof_v03_world_initialized } }
    set_global_flag = aof_v03_world_initialized
'''
    for tag in tags:
        initial={'USA':'aof_v03_usa_profit aof_v03_usa_contracts aof_v03_usa_universities','JAP':'aof_v03_jap_labs aof_v03_jap_obligations aof_v03_jap_commands','KAZ':'aof_v03_kaz_initial aof_v03_kaz_local_compacts aof_v03_kaz_resource_gap'}.get(tag,'aof_v03_'+tag.lower()+'_initial')
        setup+=f'    {tag} = {{ if = {{ limit = {{ exists = yes }} add_ideas = {{ {initial} }} }} }}\n'
    for tag in ['ENG','FRA','GER','AUS','SOV','BEL','ITA','CAU','SIB','TRK','NAF']:
        setup+=f'    {tag} = {{ set_country_flag = aof_war_exhausted }}\n'
    setup+='''    JAP = {
     if = { limit = { MAN = { exists = yes } } set_autonomy = { target = MAN autonomy_state = autonomy_puppet end_wars = no end_civil_wars = no } }
     if = { limit = { FER = { exists = yes } } set_autonomy = { target = FER autonomy_state = autonomy_puppet end_wars = no end_civil_wars = no } }
    }
    ENG = { if = { limit = { RAJ = { is_subject_of = ENG } } set_autonomy = { target = RAJ autonomy_state = autonomy_free end_wars = no end_civil_wars = no } } }
    RAJ = {
     if = { limit = { PAK = { exists = yes } NOT = { has_war_with = PAK } }
      declare_war_on = { target = PAK type = annex_everything }
     }
    }
    PAK = {
     add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 500 producer = PER }
     add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 500 producer = AFG }
     set_country_flag = aof_initial_persian_afghan_aid
    }
    KAZ = { country_event = { id = aof_kaz.1 hours = 6 } }
    USA = { country_event = { id = aof_v03_pacific.3 hours = 8 } }
    JAP = { country_event = { id = aof_v03_pacific.4 hours = 8 } }
   }
  }
 }
}
'''
    write('common/on_actions/aof_v03_startup.txt',setup)
    # Broad replacements are restricted to the incompatible 1936 story systems.
    # Installed laws/characters/equipment remain available to native mechanics.
    replacements=['common/bookmarks','common/national_focus','common/ai_strategy_plans','common/ai_strategy','common/on_actions','common/decisions','events']
    descriptor='version="0.3.0-playtest"\ntags={ "Alternative History" }\nname="Ashes of Empires"\nsupported_version="1.19.3.0"\n'+''.join(f'replace_path="{p}"\n' for p in replacements)
    write('descriptor.mod',descriptor)
    external=ROOT.parent/'ashes_of_empires.mod'
    text=descriptor+'path="'+ROOT.as_posix()+'"\n'
    if not external.exists() or external.read_text(encoding='utf-8')!=text:
        external.write_text(text,encoding='utf-8',newline='\n')
    legacy=ROOT/'common/national_focus/aof_generic_pilot.txt'
    archive=ROOT/'docs/legacy/aof_generic_pilot.txt'
    if legacy.exists():
        archive.parent.mkdir(parents=True,exist_ok=True)
        if archive.exists() and archive.read_bytes()!=legacy.read_bytes():
            raise SystemExit('Legacy focus archive differs: inspect rather than overwrite.')
        if not archive.exists():archive.write_bytes(legacy.read_bytes())
        legacy.unlink()
    print('Full v0.3 build complete. Start a NEW campaign; old saves are unsupported.')

if __name__=='__main__':main()
