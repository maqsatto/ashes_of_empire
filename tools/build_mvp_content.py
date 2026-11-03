"""Author the small MVP content set. Run with native Python; no dependencies."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if (ROOT/'common/on_actions/aof_v03_startup.txt').exists():
    raise SystemExit('Legacy MVP generator retired. Use tools/build_v03.py with HOI4 closed.')
def write(path, text, loc=False):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    encoding = 'utf-8-sig' if loc else 'utf-8'
    data = text.encode(encoding)
    if not p.exists() or p.read_bytes() != data:
        p.write_bytes(data)

# ID, prerequisite, coordinates, reward, English/Russian name and description.
rows = [
('local_workshops','industrial_study',2,2,'capital_scope = { add_extra_state_shared_building_slots = 1 add_building_construction = { type = industrial_complex level = 1 instant_build = yes } }','Local workshops','Местные мастерские','Expand civilian production around the capital.','Расширим гражданское производство в столичном регионе.'),
('transport_links','industrial_study',4,2,'capital_scope = { add_building_construction = { type = infrastructure level = 1 instant_build = yes } }','Transport links','Транспортные связи','Improve the roads connecting production and settlements.','Улучшим дороги между производством и населёнными пунктами.'),
('technical_school','industrial_study',6,2,'add_tech_bonus = { name = aof_technical_school bonus = 0.5 uses = 2 category = industry }','Technical education','Техническое образование','Train technicians for the next industrial projects.','Подготовим специалистов для будущих промышленных проектов.'),
('public_services','civic_cooperation',0,2,'add_stability = 0.05 add_political_power = 25','Public services','Государственные службы','Strengthen everyday administration and public confidence.','Укрепим повседневную работу учреждений и доверие населения.'),
('small_arms','army_training',9,1,'add_tech_bonus = { name = aof_small_arms bonus = 0.5 uses = 1 category = infantry_weapons }','Infantry equipment','Пехотное вооружение','Standardize infantry equipment and its maintenance.','Унифицируем пехотное вооружение и его обслуживание.'),
('officer_courses','army_training',11,1,'army_experience = 15','Officer courses','Офицерские курсы','Develop staff training without committing the country to war.','Улучшим подготовку командиров и штабов.'),
('defence_workshops','small_arms',9,2,'capital_scope = { add_extra_state_shared_building_slots = 1 add_building_construction = { type = arms_factory level = 1 instant_build = yes } }','Defence workshops','Оборонные мастерские','Establish a modest domestic arms industry.','Создадим небольшую собственную оружейную промышленность.'),
('civil_research','technical_school',6,3,'add_ideas = aof_technical_network','Research network','Научная сеть','Connect schools and workshops to support research.','Свяжем учебные заведения и мастерские для совместной научной работы.'),
('production_standards','local_workshops',2,3,'add_ideas = aof_production_standards_spirit','Production standards','Производственные стандарты','Improve factory organization and equipment output.','Улучшим организацию заводов и выпуск снаряжения.'),
('kaz_resource_survey','transport_links',4,3,'country_event = { id = aof_kaz.2 hours = 1 }','Survey the resource potential','Изучить ресурсный потенциал','Kazakhstan has great undeveloped resources. Begin a practical survey before investing in extraction.','Казахстан обладает большим недоосвоенным ресурсным потенциалом. Начнём с обследования, прежде чем вкладываться в добычу.'),
('kaz_development_programme','kaz_resource_survey',4,4,'country_event = { id = aof_kaz.3 hours = 1 }','Development programme','Программа развития','Choose how to put the first development programme into practice.','Определим, как осуществить первую программу развития.'),
('kaz_consolidate','kaz_development_programme',4,5,'add_stability = 0.05 add_political_power = 75 country_event = { id = aof_kaz.4 hours = 1 }','A foundation for the future','Основа будущего','Complete the first stage of independent development.','Завершим первый этап самостоятельного развития.'),
]
path = ROOT/'common/national_focus/aof_generic_pilot.txt'
text = path.read_text(encoding='utf-8')
# Regeneration replaces only the generated suffix.
if '    # MVP extension' in text:
    text = text.split('    # MVP extension')[0].rstrip()
else:
    text = text.rstrip()[:-1]
text += '\n    # MVP extension\n'
for ident, pre, x, y, reward, *_ in rows:
    condition = 'allow_branch = { tag = KAZ } available = { tag = KAZ }' if ident.startswith('kaz_') else ''
    icons = {'transport_links':'GFX_goal_generic_construct_infrastructure', 'small_arms':'GFX_goal_generic_small_arms', 'officer_courses':'GFX_goal_generic_allies_build_infantry', 'defence_workshops':'GFX_goal_generic_construct_mil_factory', 'public_services':'GFX_goal_generic_political_pressure'}
    icon = icons.get(ident, 'GFX_goal_generic_construct_civ_factory')
    tooltip = ''
    if reward.startswith('capital_scope = {'):
        tooltip_key = {'local_workshops':'aof_capital_civilian_factory',
                       'defence_workshops':'aof_capital_military_factory',
                       'transport_links':'aof_capital_infrastructure'}[ident]
        # Keep automatic country-name localisation out of the state effect scope.
        reward = f'custom_effect_tooltip = {tooltip_key} hidden_effect = {{ {reward} }}'
    text += f'''    focus = {{
        id = aof_{ident}
        icon = {icon}
        prerequisite = {{ focus = aof_{pre} }}
        x = {x}
        y = {y}
        cost = 5
        {condition}
        ai_will_do = {{ factor = 1 }}
        {tooltip}
        completion_reward = {{ {reward} }}
    }}
'''
write('common/national_focus/aof_generic_pilot.txt', text+'}\n')
for lang, name_i, desc_i in [('english',0,2),('russian',1,3)]:
    loc = f'l_{lang}:\n'
    for ident,pre,x,y,reward,*words in rows:
        loc += f' aof_{ident}: "{words[name_i]}"\n aof_{ident}_desc: "{words[desc_i]}"\n'
    write(f'localisation/{lang}/aof_mvp_focus_l_{lang}.yml',loc,True)
write('common/ideas/aof_development.txt','''ideas = {
    country = {
        aof_technical_network = {
            picture = generic_research_bonus
            allowed = { always = no }
            removal_cost = -1
            modifier = { research_speed_factor = 0.03 }
        }
        aof_production_standards_spirit = {
            picture = generic_build_infrastructure
            allowed = { always = no }
            removal_cost = -1
            modifier = { industrial_capacity_factory = 0.05 }
        }
    }
}
''')
write('events/aof_kazakhstan.txt','''add_namespace = aof_kaz
country_event = {
 id = aof_kaz.1 title = aof_kaz.1.t desc = aof_kaz.1.d
 picture = GFX_aof_event_kazakhstan_development
 fire_only_once = yes
 is_triggered_only = yes
 option = { name = aof_kaz.1.a add_political_power = 25 }
}
country_event = {
 id = aof_kaz.2 title = aof_kaz.2.t desc = aof_kaz.2.d
 picture = GFX_aof_event_kazakhstan_development is_triggered_only = yes
 option = { name = aof_kaz.2.a add_tech_bonus = { name = aof_resource_survey bonus = 0.5 uses = 1 category = industry } }
}
country_event = {
 id = aof_kaz.3 title = aof_kaz.3.t desc = aof_kaz.3.d
 picture = GFX_aof_event_kazakhstan_development is_triggered_only = yes
 option = { name = aof_kaz.3.a ai_chance = { factor = 60 } custom_effect_tooltip = aof_capital_civilian_factory hidden_effect = { capital_scope = { add_extra_state_shared_building_slots = 1 add_building_construction = { type = industrial_complex level = 1 instant_build = yes } } } }
 option = { name = aof_kaz.3.b ai_chance = { factor = 40 } custom_effect_tooltip = aof_capital_military_factory hidden_effect = { capital_scope = { add_extra_state_shared_building_slots = 1 add_building_construction = { type = arms_factory level = 1 instant_build = yes } } } }
}
country_event = {
 id = aof_kaz.4 title = aof_kaz.4.t desc = aof_kaz.4.d
 picture = GFX_aof_event_kazakhstan_development is_triggered_only = yes
 option = { name = aof_kaz.4.a add_political_power = 25 }
}
''')
write('common/on_actions/aof_startup.txt','''on_actions = {
 on_startup = {
  effect = {
   KAZ = { country_event = { id = aof_kaz.1 hours = 6 } }
  }
 }
}
''')
stories = {
 'aof_kaz.1.t': ('The broken peace', 'Хрупкий мир'),
 'aof_kaz.1.d': ('The Great War of 1914–1924 has ended. Kazakhstan enters this uncertain world as an independent country. Its considerable resource potential remains underdeveloped. Administration, transport and practical education will lay the foundation for the years ahead.', 'Великая война 1914–1924 годов завершилась. Казахстан вступает в этот неопределённый мир самостоятельной страной. Его значительный ресурсный потенциал остаётся недостаточно освоенным. Государственное управление, транспорт и практическое образование заложат основу будущего развития.'),
 'aof_kaz.1.a': ('Begin the work.', 'Приступим к работе.'),
 'aof_kaz.2.t': ('Before the first investment', 'Перед первыми вложениями'),
 'aof_kaz.2.d': ('Resource potential alone cannot supply workshops. Surveys, technical training and transport must precede large extraction projects. The first findings will support our industrial research.', 'Одного ресурсного потенциала недостаточно для снабжения мастерских. Перед крупными добывающими проектами нужны обследования, подготовка специалистов и транспорт. Первые результаты помогут промышленным исследованиям.'),
 'aof_kaz.2.a': ('Support industrial research.', 'Поддержать промышленные исследования.'),
 'aof_kaz.3.t': ('The first development programme', 'Первая программа развития'),
 'aof_kaz.3.d': ('The groundwork is ready. Limited resources require a clear priority: civilian workshops for long-term growth, or arms production to equip the army. Both choices support independent development.', 'Подготовительная работа завершена. Ограниченные средства требуют ясного приоритета: гражданские предприятия для долгосрочного роста или оружейное производство для снабжения армии. Оба пути служат самостоятельному развитию.'),
 'aof_kaz.3.a': ('Expand civilian production.', 'Расширить гражданское производство.'),
 'aof_kaz.3.b': ('Equip our own army.', 'Снабдить собственную армию.'),
 'aof_kaz.4.t': ('A foundation for the future', 'Основа будущего'),
 'aof_kaz.4.d': ('The first programme has brought administration, training and production into a common effort. Independence now has a stronger material foundation. The world beyond our borders remains uncertain; further development is our next task.', 'Первая программа объединила работу учреждений, подготовку специалистов и производство. Независимость получила более прочную материальную основу. Мир за нашими границами остаётся неопределённым; дальнейшее развитие — наша следующая задача.'),
 'aof_kaz.4.a': ('Continue building.', 'Продолжить созидание.'),
 'aof_technical_network': ('Research network', 'Научная сеть'),
 'aof_technical_network_desc': ('Cooperation between technical schools and workshops supports practical research.', 'Сотрудничество технических школ и мастерских помогает практическим исследованиям.'),
 'aof_production_standards_spirit': ('Production standards', 'Производственные стандарты'),
 'aof_production_standards_spirit_desc': ('Common standards improve equipment production.', 'Единые стандарты улучшают выпуск снаряжения.'),
 'aof_resource_survey': ('Resource survey', 'Обследование ресурсов'),
 'aof_capital_civilian_factory': ('Adds one building slot and one civilian factory in the capital state.', 'Добавляет одну ячейку строительства и одну гражданскую фабрику в столичной области.'),
 'aof_capital_military_factory': ('Adds one building slot and one military factory in the capital state.', 'Добавляет одну ячейку строительства и один военный завод в столичной области.'),
 'aof_capital_infrastructure': ('Adds one infrastructure level in the capital state.', 'Добавляет один уровень инфраструктуры в столичной области.'),
}
for lang, index in [('english',0),('russian',1)]:
    write(f'localisation/{lang}/aof_story_l_{lang}.yml',f'l_{lang}:\n'+''.join(f' {key}: "{value[index]}"\n' for key,value in stories.items()),True)
