"""Native, transactional peaceful partition of the provisional TRK fixture."""
from pathlib import Path
import json,re
from contentlib import write,localize
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('C:/Hearts of Iron IV')
manifest=json.loads((ROOT/'docs/design_v0_3/WORLD_MANIFEST.json').read_text(encoding='utf8'))
FIXTURE=[405,584,585,732,742,823,830,831,832]
PARTS={'UZB':[585,823,830,831],'TMS':[584,832],'TAJ':[742],'KYR':[732]}
CAPS={'UZB':585,'TMS':584,'TAJ':742,'KYR':732}
assert set(manifest['countries']['TRK']['states'])==set(FIXTURE),'Partition fixture changed: review territorial agreement first'
for tag,ids in PARTS.items():
    for sid in ids:
        native=(GAME/'history/states'/manifest['states'][str(sid)]['source_file']).read_text(encoding='utf-8-sig')
        assert re.search(r'\badd_core_of\s*=\s*'+tag+r'\b',native),(tag,sid,'missing installed core')
absent=' '.join('NOT = { country_exists = '+tag+' }' for tag in PARTS)
ownership=' '.join(str(sid)+' = { is_owned_and_controlled_by = ROOT }' for sid in FIXTURE)
cores='405 = { is_core_of = UZB } '+' '.join(str(sid)+' = { is_core_of = '+tag+' }' for tag,ids in PARTS.items() for sid in ids)
# Native release works on ALL owned core territory. Refuse the transaction if
# later conquests would release an unnegotiated state, including a lost core.
outside=[]
for tag,ids in PARTS.items():
    permitted=ids+([405] if tag=='UZB' else [])
    outside.append('NOT = { any_owned_state = { is_core_of = '+tag+' NOT = { OR = { '+' '.join('state = '+str(sid) for sid in permitted)+' } } } }')
GUARD='tag = TRK has_war = no is_subject = no NOT = { has_country_flag = aof_partition_completed } '+absent+' '+ownership+' '+cores+' '+' '.join(outside)
LOC={
 'aof_partition.1.t':('Соглашение о мирном разделе','A negotiated peaceful partition'),
 'aof_partition.1.d':('Это конкретный договор для временной игровой карты, а не утверждение исторических границ. Узбекистан получает Навои, Каракалпакстан, Бухару и Хиву; Туркменистан — Ашхабад и Ташауз; Таджикистан — Сталинабад; Кыргызстан — Памир. Ташкент (область 405) остаётся за правопреемственным кабинетом Туркестана, поэтому текущий игрок продолжит партию. Новые страны становятся независимыми. Их национальные права сохраняются, включая узбекское право на Ташкент; владение городом остаётся отдельным временным компромиссом. Перед исполнением все условия будут проверены повторно.',
 'This is a specific treaty for the provisional playtest map, not a declaration of historical boundaries. Uzbekistan receives Navoi, Karakalpakstan, Bukhara and Khiva; Turkmenistan receives Ashkhabad and Tashauz; Tajikistan receives Stalinabad; Kyrgyzstan receives Pamir. Tashkent (state 405) remains with the Turkestani continuity cabinet so the current player can continue. The new states become independent. Their national rights are preserved, including the Uzbek core on Tashkent; possession of that city remains a separate provisional compromise. Every condition is checked again immediately before execution.'),
 'aof_partition.1.a':('Исполнить договор и сохранить кабинет в Ташкенте','Execute the treaty and retain the Tashkent cabinet'),
 'aof_partition.1.b':('Сохранить общее государство','Preserve the common state'),
 'aof_partition.2.t':('Четыре независимых правительства','Four independent governments'),
 'aof_partition.2.d':('Согласованные территории переданы четырём независимым правительствам. Туркестан сохраняет Ташкент, свой существующий политический курс и государственные учреждения. Это правопреемственный кабинет, а не исчезновение страны или автоматическое признание одной версии исторической карты. Ни один участник не обязан вступать в военный союз. Договор не создаёт новых претензий и не уничтожает прежние национальные права.',
 'The agreed territories have passed to four independent governments. Turkestan retains Tashkent, its existing political course and its institutions. This is a continuity cabinet, not the disappearance of the country or automatic endorsement of one historical map. No participant is compelled to join an alliance. The treaty creates no new claims and does not erase existing national rights.'),
 'aof_partition.2.a':('Продолжить работу правопреемственного кабинета','Continue the work of the continuity cabinet'),
 'aof_partition.3.t':('Договор нельзя исполнить в нынешних условиях','The treaty cannot be executed under present conditions'),
 'aof_partition.3.d':('Ничего не изменено. Договор требует независимого Туркестана в мирное время; отсутствия уже существующих Узбекистана, Туркменистана, Таджикистана и Кыргызстана; владения и контроля всех девяти согласованных областей (405, 584, 585, 732, 742, 823, 830, 831, 832). Национальные права участников на согласованные области должны сохраняться. Нельзя передавать дополнительные захваченные области с национальными правами одного из новых государств. Уже исполненный раздел повторить нельзя. Верните необходимые условия или сохраните союз; переговоры можно открыть заново.',
 'Nothing has changed. The treaty requires an independent Turkestan at peace; Uzbekistan, Turkmenistan, Tajikistan and Kyrgyzstan must not already exist; all nine agreed states (405, 584, 585, 732, 742, 823, 830, 831, 832) must be owned and controlled by Turkestan. The participants’ cores on the agreed states must remain intact. Additional conquered states with one successor’s cores cannot be transferred outside the treaty. A completed partition cannot be repeated. Restore the required conditions or preserve the union; negotiations may be reopened.'),
 'aof_partition.3.a':('Сохранить нынешние границы','Keep the current boundaries'),
 'aof_partition_treaty_tt':('При соблюдении всех условий: создать четыре независимые страны на согласованных областях, сохранить область 405 за Туркестаном. Текущий игрок продолжает управлять Туркестаном.','If every condition holds: create four independent countries on the agreed states and retain state 405 for Turkestan. The current player continues to govern Turkestan.'),
 'aof_partition_reopen':('Вернуться к договору о мирном разделе','Return to the peaceful partition treaty'),
 'aof_partition_reopen_desc':('Повторно открыть конкретный договор о четырёх независимых правительствах и ташкентском правопреемственном кабинете. Владение всеми девятью областями, контроль над ними и отсутствие войны проверяются перед исполнением.','Reopen the specific treaty for four independent governments and a Tashkent continuity cabinet. Ownership, control of all nine states and peace are rechecked before execution.'),
}
FAMILIES={'democratic':'aof_constitutional_federalism','aof_social_democracy':'aof_parliamentary_socialism','communism':'aof_soviet_centralism','aof_conservatism':'aof_parliamentary_conservatism','neutrality':'aof_bureaucratic_technocracy','fascism':'aof_national_revolution'}
def institutions(tag):
    out=''
    for family,ideology in FAMILIES.items():
        key='aof_partition_'+tag+'_'+family+'_cabinet'
        LOC[key]=('Правопреемственный кабинет' if tag=='TRK' else 'Учредительный кабинет','Continuity Cabinet' if tag=='TRK' else 'Constituent Cabinet')
        out+='create_country_leader = { name = "'+key+'" desc = "" expire = "1960.1.1" ideology = '+ideology+' traits = { } } '
    return out
commit='set_country_flag = aof_partition_case_validated\n405 = { remove_core_of = UZB }\n'
for tag,ids in PARTS.items():
    commit+='release_autonomy = { target = '+tag+' autonomy_state = autonomy_puppet freedom_level = 0.0 }\n'
    commit+='set_autonomy = { target = '+tag+' autonomy_state = autonomy_free }\n'
    cap=CAPS[tag];province=next(p for p,_ in manifest['states'][str(cap)]['victory_points'])
    commit+=tag+' = { if = { limit = { is_in_faction = yes } leave_faction = yes } set_capital = { state = '+str(cap)+' remember_old_capital = no } '+institutions(tag)+' set_country_flag = aof_partition_successor set_stability = 0.55 set_technology = { infantry_weapons = 1 } add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 200 producer = '+tag+' } '
    # Small local guard, using a verified province in the new capital state.
    commit+='division_template = { name = "AOF Local Guard" regiments = { infantry = { x = 0 y = 0 } infantry = { x = 0 y = 1 } infantry = { x = 0 y = 2 } } } '
    commit+='create_unit = { owner = '+tag+' prioritize_location = '+str(province)+' allow_spawning_on_enemy_provs = no division = "name = \\"Local Guard\\" division_template = \\"AOF Local Guard\\" start_experience_factor = 0.1 start_equipment_factor = 0.7" } }\n'
commit+='405 = { add_core_of = UZB }\nset_capital = { state = 405 remember_old_capital = no }\n'+institutions('TRK')
commit+='set_country_flag = aof_partition_completed set_country_flag = aof_partition_trk_continuity clr_country_flag = aof_v03_separation_negotiations add_stability = 0.03 country_event = { id = aof_partition.2 days = 1 }\n'
events='add_namespace = aof_partition\n'
events+='country_event = { id = aof_partition.1 title = aof_partition.1.t desc = aof_partition.1.d picture = GFX_aof_event_kazakhstan_development is_triggered_only = yes\n'
events+='option = { name = aof_partition.1.a ai_chance = { factor = 1 } custom_effect_tooltip = aof_partition_treaty_tt if = { limit = { '+GUARD+' } '+commit+' } else = { country_event = { id = aof_partition.3 days = 1 } } }\n'
events+='option = { name = aof_partition.1.b ai_chance = { factor = 3 } add_stability = 0.04 } }\n'
for number in [2,3]:
    events+='country_event = { id = aof_partition.'+str(number)+' title = aof_partition.'+str(number)+'.t desc = aof_partition.'+str(number)+'.d picture = GFX_aof_event_world_peace_1924 is_triggered_only = yes option = { name = aof_partition.'+str(number)+'.a } }\n'
write('events/aof_v03_partition.txt',events)
decisions='aof_v03_diplomacy_category = { aof_partition_reopen = { icon = generic_political_discourse cost = 0 days_re_enable = 30 visible = { tag = TRK has_country_flag = aof_v03_separation_negotiations NOT = { has_country_flag = aof_partition_completed } } available = { '+GUARD+' } complete_effect = { country_event = { id = aof_partition.1 days = 1 } } ai_will_do = { factor = 0 } } }\n'
write('common/decisions/aof_v03_partition.txt',decisions)
localize('aof_v03_partition',LOC)
if __name__=='__main__':print('Partition:3events;1decision;4independent successors;TRK405continuity;allinstalledcoresverified')
