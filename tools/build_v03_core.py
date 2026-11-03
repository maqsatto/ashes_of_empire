"""Author the v0.3 common framework against the installed 1.19 database.
Only explicitly selected start_year values are changed in native technology files.
"""
from pathlib import Path
import re, json
from contentlib import ROOT, write, localize, render_tree, capital_building
from ideaicons import idea_picture

GAME=Path('C:/Hearts of Iron IV')
# The scenario descriptor replaces common/ai_strategy: avoid native 1936
# diplomatic plots and advisor triggers while retaining ordinary production.
write('common/ai_strategy/aof_v03_baseline.txt','''# Native, country-neutral production guidance; no historical diplomatic plot.
aof_v03_baseline_production = {
 allowed = { always = yes }
 enable = { always = yes }
 abort_when_not_enabled = yes
 ai_strategy = { type = role_ratio id = infantry value = 80 }
 ai_strategy = { type = role_ratio id = armor value = 5 }
 ai_strategy = { type = role_ratio id = garrison value = 10 }
 ai_strategy = { type = unit_ratio id = fighter value = 70 }
 ai_strategy = { type = unit_ratio id = cas value = 20 }
 ai_strategy = { type = unit_ratio id = tactical_bomber value = 10 }
}
''')
L={}; N=[]
def focus(key,ru,en,x,y,pre=(),effect='add_political_power = 35',**kw):
    ident='aof_v03_g_'+key
    n=dict(id=ident,ru=ru,en=en,x=x,y=y,pre=['aof_v03_g_'+p for p in pre],effect=effect,**kw)
    N.append(n)
    return ident
def bonus(cat,n=1):
    return f'add_tech_bonus = {{ name = aof_v03_research_bonus bonus = 0.5 uses = {n} category = {cat} }}'
def doctrine(cat):
    return f'add_doctrine_cost_reduction = {{ name = aof_v03_doctrine_bonus cost_reduction = 0.35 uses = 2 category = {cat}_doctrine }}'
def government(family):
    elections='yes' if family in ['democratic','aof_social_democracy','aof_conservatism'] else 'no'
    return f'set_politics = {{ ruling_party = {family} elections_allowed = {elections} }} add_popularity = {{ ideology = {family} popularity = 0.15 }}'
def coastal_port_effect():
    """Select ONE real eligible province with native weighted-list metadata.

    Installed1.19 has no documented random_province scope. Native explicit
    province construction + random_list modifiers avoid inventing that scope,
    adding a base to an inland capital, or granting every coast a free base.
    Effective state membership is read from the current full-build fixture.
    """
    definition=ROOT/'map/definition.csv'
    if not definition.exists(): definition=GAME/'map/definition.csv'
    coast=set()
    for line in definition.read_text(encoding='utf-8-sig').splitlines():
        row=line.split(';')
        if len(row)>=8 and row[0].isdigit() and row[4]=='land' and row[5]=='true':coast.add(int(row[0]))
    # These are inspected native Caspian shores. Runtime coastal triggers still
    # forbid using them until the separate map actually makes the state coastal.
    from build_v03_caspian import SHORE
    coast.update(p for ids in SHORE.values() for p in ids)
    paths={p.name:p for p in (GAME/'history/states').glob('*.txt')}
    paths.update({p.name:p for p in (ROOT/'history/states').glob('*.txt')})
    membership={}
    for path in paths.values():
        text=re.sub(r'#[^\n]*','',path.read_text(encoding='utf-8-sig'))
        sid=re.search(r'\bid\s*=\s*(\d+)',text)
        provinces=re.search(r'\bprovinces\s*=\s*\{([^}]+)\}',text)
        if not sid or not provinces:continue
        for value in re.findall(r'\d+',provinces[1]):
            p=int(value)
            if p in coast:
                if p in membership:raise ValueError(f'Duplicate coastal province membership: {p}')
                membership[p]=int(sid[1])
    if set(membership)!=coast:raise ValueError('Missing actual state membership for coastal-port candidates')
    body='# Native1.19 explicit province construction; one eligible weighted entry only.\n'
    body+='aof_v03_build_one_civilian_port = { random_list = {\n'
    for province,state in sorted(membership.items()):
        eligible=f'owns_state = {state} controls_province = {province} {state} = {{ is_controlled_by = ROOT is_coastal = yes any_province_building_level = {{ province = {{ id = {province} limit_to_coastal = yes }} building = naval_base level < 10 }} }}'
        body+=f' 1 = {{ modifier = {{ factor = 0 NOT = {{ AND = {{ {eligible} }} }} }} {state} = {{ add_building_construction = {{ type = naval_base province = {province} level = 1 instant_build = yes }} }} }}\n'
    return body+'} }\n',len(membership)
def chain(items,x,pre=(),effects=None,**kw):
    for y,(key,ru,en) in enumerate(items):
        focus(key,ru,en,x,y,pre,effect=(effects or {}).get(key,'add_political_power = 30'),**kw)
        pre=(key,)

chain([('priorities','Приоритеты государства','State priorities'),('census','Перепись хозяйства','Economic census'),('service','Единая гражданская служба','A common civil service'),('local','Договор с местной властью','Compact with local government'),('budget','Бюджет без чрезвычайщины','An ordinary budget')],0,effects={'service':'add_stability = 0.05','local':'add_stability = 0.05','budget':'add_ideas = aof_v03_civil_service'})
damaged='OR = { has_war = yes has_country_flag = aof_war_exhausted any_owned_state = { has_state_flag = aof_war_damaged } }'
chain([('home','Вернуть людей домой','Bring people home'),('debris','Разобрать военные завалы','Clear the wartime debris'),('supply','Восстановить узлы снабжения','Restore supply junctions'),('jobs','Работа для демобилизованных','Work for demobilised soldiers'),('emergency','Снять чрезвычайные ограничения','End emergency restrictions')],4,branch=damaged,effects={'home':'add_stability = 0.03','debris':capital_building('infrastructure'),'supply':bonus('logistics_tech'),'jobs':capital_building(),'emergency':'add_stability = 0.05'})
chain([('orders','Пересчитать мирные заказы','Reassess peacetime orders'),('civilian','Гражданская продукция','Civilian production'),('market','Внутренний рынок','The domestic market'),('exports','Экспорт без военного контракта','Exports beyond war contracts')],7,branch='NOT = { '+damaged+' }',effects={'orders':'add_stability = 0.03','civilian':capital_building(),'market':bonus('industry'),'exports':'add_ideas = aof_v03_export_orders'})
chain([('roads','Соединить производящие районы','Connect producing districts'),('workshops','Ремонтные мастерские','Repair workshops'),('power','Надёжное электроснабжение','Reliable electricity')],10,effects={'roads':capital_building('infrastructure'),'workshops':bonus('industry'),'power':bonus('industry')})
focus('raw','Быстрый экспорт сырья','Immediate raw-material exports',9,3,['power'],effect='add_political_power = 75 add_ideas = aof_v03_export_orders',excludes=['aof_v03_g_processing'])
focus('processing','Собственная переработка','Domestic processing',11,3,['power'],effect=capital_building(),excludes=['aof_v03_g_raw'],cost=10)
focus('centre','Национальный промышленный центр','A national industrial centre',9,4,['raw'],effect=capital_building('arms_factory'),excludes=['aof_v03_g_network'])
focus('network','Распределённая сеть мастерских','A dispersed workshop network',11,4,['processing'],effect='add_ideas = aof_v03_workshop_network',excludes=['aof_v03_g_centre'])
# Two genuine independent choices: export/processing does not predetermine
# concentrated/dispersed industry. A nested prerequisite block means OR.
for ident in ['aof_v03_g_centre','aof_v03_g_network']:
    next(n for n in N if n['id']==ident)['pre']=[['aof_v03_g_raw','aof_v03_g_processing']]
chain([('capital','Внутренний капитал','Domestic capital'),('procurement','Государственный заказ','Public procurement'),('cooperation','Производственная кооперация','Industrial cooperation')],14,effects={'capital':'add_political_power = -25 add_stability = 0.03','procurement':capital_building(),'cooperation':'add_ideas = aof_v03_workshop_network'})
for ident in ['aof_v03_g_capital','aof_v03_g_procurement']:
    next(n for n in N if n['id']==ident)['cost']=10 # slower domestic mobilisation, no foreign burden
focus('talks','Открыть инвестиционные переговоры','Open investment talks',17,0,effect='country_event = { id = aof_v03_regions.1 }',excludes=['aof_v03_g_capital'])
N[-4]['excludes']=['aof_v03_g_talks']
focus('concession','Ограниченное промышленное соглашение','A limited industrial agreement',17,1,['talks'],available='has_country_flag = aof_v03_investment_signed',effect='if = { limit = { has_country_flag = aof_v03_investment_foreign } add_timed_idea = { idea = aof_v03_concession days = 730 } } '+capital_building(),desc_ru='Согласованный иностранный договор даёт концессию с её двухлетней нагрузкой. При внутреннем финансировании после отказа проект уже оплачен политической властью и не получает вымышленную иностранную концессию.',desc_en='An accepted foreign contract creates a concession with its two-year burden. Domestic financing after refusal is paid in political power and receives no fictional foreign-concession spirit.')
focus('joint','Совместное предприятие','A joint enterprise',17,2,['concession'],effect=bonus('industry'))
chain([('teachers','Подготовить учителей','Train teachers'),('schools','Технические училища','Technical schools'),('engineers','Отправить инженерную группу','Send an engineering mission'),('institute','Прикладной институт','An applied institute')],20,effects={'teachers':'add_political_power = -20 add_stability = 0.03','schools':bonus('industry'),'engineers':bonus('electronics'),'institute':'add_ideas = aof_v03_applied_institute'})
focus('representation','Кто представляет страну?','Who represents the country?',25,0,effect='add_political_power = 50')
for key,ru,en,x,ideology in [('parliament','Ответственное правительство','Responsible government',23,'democratic'),('labour','Трудовой компромисс','A labour compromise',25,'aof_social_democracy'),('order','Правительство национального порядка','A government of national order',27,'neutrality')]:
    others=['aof_v03_g_'+k for k in ['parliament','labour','order'] if k!=key]
    focus(key,ru,en,x,1,['representation'],effect=f'add_popularity = {{ ideology = {ideology} popularity = 0.1 }} add_stability = 0.03',excludes=others)
    focus(key+'_law',{'parliament':'Гарантии оппозиции','labour':'Социальное законодательство','order':'Ограниченный чрезвычайный мандат'}[key],{'parliament':'Opposition guarantees','labour':'Social legislation','order':'A limited emergency mandate'}[key],x,2,[key],effect='add_stability = 0.05 add_political_power = -35')
    focus(key+'_settlement',{'parliament':'Долгая конституция','labour':'Реформа без революции','order':'Вернуть полномочия гражданским'}[key],{'parliament':'A durable constitution','labour':'Reform without revolution','order':'Return authority to civilians'}[key],x,3,[key+'_law'],effect='add_stability = 0.07 add_war_support = -0.03')
next(n for n in N if n['id']=='aof_v03_g_parliament_settlement')['effect']='country_event = { id = aof_v03_regions.41 }'
next(n for n in N if n['id']=='aof_v03_g_labour_settlement')['effect']=government('aof_social_democracy')+' add_stability = 0.05 add_political_power = -25'
next(n for n in N if n['id']=='aof_v03_g_order_settlement')['effect']='country_event = { id = aof_v03_regions.42 }'
focus('exception','Закрепить исключение','Make the exception permanent',27,4,['order_law'],effect=government('neutrality')+' add_war_support = 0.08 add_stability = -0.05 add_political_power = 75',excludes=['aof_v03_g_order_settlement'])
next(n for n in N if n['id']=='aof_v03_g_order_settlement')['excludes']=['aof_v03_g_exception']
for stem,ru,en,family,x in [('revolution','Представительство советов','Representation of the councils','communism',29),('nationalmission','Национальная миссия','A national mission','fascism',31)]:
    context=f'OR = {{ has_government = {family} {family} > 0.2 }}'
    focus(stem,ru,en,x,1,['representation'],effect=f'add_popularity = {{ ideology = {family} popularity = 0.05 }} add_stability = -0.03',branch=context)
    focus(stem+'_institutions','Органы нового мандата','Institutions of the new mandate',x,2,[stem],effect='add_political_power = -50 add_stability = 0.03',branch=context)
    focus(stem+'_settlement','Утвердить новый политический договор','Ratify the new political compact',x,3,[stem+'_institutions'],effect=government(family)+' add_war_support = 0.05 add_stability = -0.02',branch=context)
roots=['parliament','labour','order','revolution','nationalmission']
for n in N:
    if n['id'] in ['aof_v03_g_'+k for k in roots]:
        n['excludes']=['aof_v03_g_'+k for k in roots if n['id']!='aof_v03_g_'+k]
chain([('arsenals','Инвентаризация арсеналов','Inventory the arsenals'),('calibre','Единый калибр и ремонт','Common calibres and repair'),('ncos','Подготовка младших командиров','Train junior commanders'),('logistics','Снабжение важнее парада','Supply before parades')],33,effects={'arsenals':'army_experience = 15','calibre':bonus('infantry_weapons'),'ncos':'army_experience = 20','logistics':bonus('logistics_tech')})
for i,(key,ru,en,idea) in enumerate([('motor','Мотор решает расстояние','Engines overcome distance','mobile'),('breakthrough','Подготовленный прорыв','The prepared breakthrough','breakthrough'),('territorial','Территориальная армия','The territorial army','territorial'),('expedition','Экспедиционный корпус','The expeditionary corps','expedition')]):
    focus(key,ru,en,30+i*2,4,['logistics'],effect='army_experience = 25 '+doctrine('land')+' add_ideas = aof_v03_'+idea,excludes=['aof_v03_g_'+k for k in ['motor','breakthrough','territorial','expedition'] if k!=key])
coast='any_owned_state = { is_coastal = yes is_controlled_by = ROOT } OR = { NOT = { tag = KAZ } has_global_flag = aof_caspian_navigation_verified }'
chain([('flight','Лётная школа','A flying school'),('recon','Разведать собственную территорию','Survey our territory'),('airrepair','Авиационные ремонтные мастерские','Aircraft repair workshops')],40,effects={'flight':'air_experience = 15','recon':bonus('light_fighter'),'airrepair':bonus('air_equipment')})
for i,(key,ru,en) in enumerate([('frontsky','Небо над фронтом','Skies above the front'),('interdiction','Лишить противника движения','Deny enemy movement'),('seasky','Небо над морем','Skies above the sea')]):
    focus(key,ru,en,38+i*2,3,['airrepair'],effect='air_experience = 25 '+doctrine('air')+' add_ideas = aof_v03_'+key,excludes=['aof_v03_g_'+k for k in ['frontsky','interdiction','seasky'] if k!=key],available=coast if key=='seasky' else 'always = yes')
coast='any_owned_state = { is_coastal = yes is_controlled_by = ROOT } OR = { NOT = { tag = KAZ } has_global_flag = aof_caspian_navigation_verified }'
port_script,port_candidates=coastal_port_effect()
write('common/scripted_effects/aof_v03_core_ports.txt',port_script)
L['aof_v03_one_coastal_port']=('Повысить на 1 уровень одну принадлежащую и подконтрольную прибрежную базу либо построить её с нуля, если есть подходящая провинция ниже уровня 10.','Add one naval-base level to one owned and controlled coastal province, building from zero if necessary, provided an eligible province is below level10.')
chain([('harbour','Гражданская гавань','A civilian harbour'),('shiprepair','Ремонтная верфь','A repair shipyard'),('coastguard','Береговая охрана','The coast guard')],47,branch=coast,available=coast,effects={'harbour':'navy_experience = 15 custom_effect_tooltip = aof_v03_one_coastal_port hidden_effect = { aof_v03_build_one_civilian_port = yes }','shiprepair':'random_owned_controlled_state = { limit = { is_coastal = yes } add_extra_state_shared_building_slots = 1 add_building_construction = { type = dockyard level = 1 instant_build = yes } }','coastguard':bonus('naval_equipment')})
for i,(key,ru,en) in enumerate([('commandsea','Владеть морем','Command the sea'),('denysea','Отрицать чужое господство','Deny hostile supremacy'),('safepassage','Сохранить путь','Keep the route open')]):
    focus(key,ru,en,45+i*2,3,['coastguard'],effect='navy_experience = 25 '+doctrine('naval')+' add_ideas = aof_v03_'+key,branch=coast,available=coast,excludes=['aof_v03_g_'+k for k in ['commandsea','denysea','safepassage'] if k!=key])
chain([('recognition','Признание наших границ','Recognition of our borders'),('neighbours','Соглашение с соседями','An agreement with neighbours'),('conference','Региональная конференция','A regional conference')],53,branch='is_subject = no',available='is_subject = no',effects={'recognition':'add_stability = 0.03','neighbours':'country_event = { id = aof_v03_regions.10 }','conference':'country_event = { id = aof_v03_regions.11 }'})
focus('neutral','Вооружённый нейтралитет','Armed neutrality',52,3,['conference'],effect='add_ideas = aof_v03_armed_neutrality',excludes=['aof_v03_g_defence'])
focus('defence','Взаимная оборона','Mutual defence',54,3,['conference'],effect='country_event = { id = aof_v03_regions.12 }',excludes=['aof_v03_g_neutral'])
chain([('mandate','Пределы внешнего мандата','The limits of the foreign mandate'),('localpowers','Полномочия местного кабинета','Powers of the local cabinet'),('guarantee','Пересмотреть гарантии покровителя','Review the patron guarantee')],57,branch='is_subject = yes',effects={'mandate':'add_political_power = 40','localpowers':'add_stability = 0.05','guarantee':'country_event = { id = aof_v03_regions.20 }'})

# A recovered European institute can request a specialist's return. Host answers
# through aof_diplomacy.100 with FROM preserved as the recovering country.
next(n for n in N if n['id']=='aof_v03_g_institute')['effect'] += ' if = { limit = { has_country_flag = aof_war_exhausted capital_scope = { is_on_continent = europe } } country_event = { id = aof_v03_regions.43 days = 1 } }'

# Regional content lives in the same shared framework so it does not erase its economy.
def regional(prefix,tags,items,effects=None):
    gate='OR = { '+' '.join('tag = '+t for t in tags)+' }'
    previous=()
    for y,(key,ru,en) in enumerate(items):
        full=prefix+'_'+key
        focus(full,ru,en,62,y,previous,effect=(effects or {}).get(key,'add_political_power = 30'),branch=gate)
        previous=(full,)
regional('fin',['FIN'],[('karelia','Послевоенное устройство Карелии','The postwar settlement of Karelia'),('communities','Представительство местных общин','Representation for local communities'),('roads','Общие дороги и школы','Common roads and schools'),('border','Признанная граница','A recognised border')],{'communities':'country_event = { id = aof_v03_regions.30 }','roads':capital_building('infrastructure'),'border':'add_stability = 0.06'})
fin_border=next(n for n in N if n['id']=='aof_v03_g_fin_border')
fin_border.update(available='owns_state = 215 owns_state = 216 NOT = { has_war_with = SOV }',excludes=['aof_v03_g_fin_watch'],effect='if = { limit = { SOV = { exists = yes } } SOV = { country_event = { id = aof_v03_regions.50 days = 1 } } } else = { set_country_flag = aof_v03_fin_border_uncontested add_stability = 0.05 }')
focus('fin_watch','Постоянная тревога на востоке','Vigilance on the eastern frontier',64,3,['fin_roads'],effect='army_experience = 25 add_war_support = 0.05 add_political_power = -25',branch='tag = FIN',excludes=['aof_v03_g_fin_border'])
regional('man',['MAN'],[('rail','Местные кадры железных дорог','Local railway personnel'),('service','Собственная промышленная служба','Our own industrial service'),('garrison','Обсудить полномочия гарнизона','Discuss garrison powers'),('rights','Договорная самостоятельность','Negotiated self-government')],{'rail':bonus('industry'),'service':capital_building(),'garrison':'if = { limit = { JAP = { exists = yes } } JAP = { country_event = { id = aof_diplomacy.50 } } }','rights':'country_event = { id = aof_v03_regions.31 }'})
regional('fer',['FER'],[('port','Город и порт','City and port'),('trade','Торговый договор с Сибирью','Trade with Siberia'),('service','Служба собственной внешней торговли','Our own foreign trade service'),('guarantee','Пересмотр японской гарантии','Review the Japanese guarantee')],{'port':capital_building('infrastructure'),'trade':'if = { limit = { SIB = { exists = yes } } SIB = { country_event = { id = aof_diplomacy.80 } } }','service':'add_ideas = aof_v03_export_orders','guarantee':'if = { limit = { JAP = { exists = yes } } JAP = { country_event = { id = aof_diplomacy.40 } } }'})
regional('trk',['TRK'],[('congress','Новый съезд участников','A new congress of members'),('powers','Разделить полномочия','Divide responsibilities'),('union','Общая оборона при местном управлении','Common defence, local government'),('settlement','Сохранить союз или договориться о разделе','Preserve the union or negotiate separation')],{'powers':'country_event = { id = aof_v03_regions.32 }','union':'army_experience = 25 add_stability = 0.03','settlement':'country_event = { id = aof_v03_regions.33 }'})
regional('raj',['RAJ'],[('supply','Стабилизировать снабжение фронта','Stabilise front-line supply'),('cabinet','Гражданское правительство в военное время','Civilian government in wartime'),('terms','Проверить условия перемирия','Examine armistice terms'),('future','Будущее государства','The future of the state')],{'supply':'army_experience = 20 '+bonus('logistics_tech'),'cabinet':'country_event = { id = aof_v03_regions.34 }','terms':'if = { limit = { PAK = { exists = yes } has_war_with = PAK } PAK = { country_event = { id = aof_diplomacy.130 } } }','future':'add_stability = 0.07'})
next(n for n in N if n['id']=='aof_v03_g_raj_terms')['excludes']=['aof_v03_g_raj_offensive']
next(n for n in N if n['id']=='aof_v03_g_raj_future')['pre']=[['aof_v03_g_raj_terms','aof_v03_g_raj_offensive']]
focus('raj_offensive','Военная цель вместо перемирия','A military objective instead of an armistice',64,2,['raj_cabinet'],effect='add_political_power = -50 add_stability = -0.04 army_experience = 25 add_timed_idea = { idea = aof_v03_raj_wartime_priority days = 365 } if = { limit = { has_war_with = PAK } create_wargoal = { type = puppet_wargoal_focus target = PAK } }',available='PAK = { exists = yes } has_war_with = PAK',branch='tag = RAJ',excludes=['aof_v03_g_raj_terms'],desc_ru='Явно выбрать цель зависимого правительства в уже идущей войне против Пакистана вместо предложения перемирия. Создаёт штатную цель войны и временный военный приоритет ценой стабильности и политической власти; не объявляет новую войну, не назначает её прошлые причины и не аннексирует страну автоматически.',desc_en='Explicitly pursue a dependent government in the existing war against Pakistan instead of proposing an armistice. Creates a native war goal and a temporary military priority at a political and stability cost; declares no new war, invents no past cause and does not automatically annex the country.')
regional('pak',['PAK'],[('aid','Согласовать помощь Ирана и Афганистана','Coordinate Iranian and Afghan aid'),('supply','Единые правила снабжения союзников','Common allied supply rules'),('peace','Самостоятельный мирный договор','An independent peace treaty'),('defence','Общий региональный оборонный блок','A regional defence arrangement')],{'aid':'if = { limit = { PER = { exists = yes } } PER = { country_event = { id = aof_diplomacy.140 } } } if = { limit = { AFG = { exists = yes } } AFG = { country_event = { id = aof_diplomacy.140 } } }','supply':bonus('logistics_tech'),'peace':'if = { limit = { RAJ = { exists = yes } has_war_with = RAJ } RAJ = { country_event = { id = aof_diplomacy.130 } } }','defence':'country_event = { id = aof_v03_regions.12 }'})
regional('can',['CAN'],[('obligations','Пересмотреть обязательства перед метрополией','Review obligations to the metropole'),('treaties','Собственные внешние договоры','Our own foreign agreements'),('ties','Океанские или североамериканские связи','Oceanic or North American ties'),('defence','Самостоятельная оборонная программа','An autonomous defence programme')],{'obligations':'country_event = { id = aof_v03_regions.35 }','treaties':'add_political_power = 60','ties':'country_event = { id = aof_v03_regions.36 }','defence':capital_building('arms_factory')})
next(n for n in N if n['id']=='aof_v03_g_can_treaties')['effect']='country_event = { id = aof_v03_regions.55 days = 1 }'
regional('central',['GUA','HON','ELS','NIC','COS','PAN'],[('summit','Созвать соседние республики','Convene neighbouring republics'),('guarantees','Гарантии малым участникам','Guarantees for small participants'),('transit','Общий транзитный договор','A common transit agreement'),('defence','Оборонное сотрудничество','Defence cooperation'),('compact','Федеративный договор при взаимном согласии','A federal compact by mutual consent')],{'summit':'country_event = { id = aof_v03_regions.11 }','guarantees':'add_stability = 0.05','transit':capital_building('infrastructure'),'defence':'country_event = { id = aof_v03_regions.12 }','compact':'country_event = { id = aof_v03_regions.37 }'})
regional('chaco',['BOL','PAR'],[('commission','Пограничная комиссия по Чако','A Chaco boundary commission'),('supply','Подготовить снабжение спорного района','Prepare supply for the disputed district'),('mediation','Международное посредничество','International mediation'),('settlement','Закончить спор','Bring the dispute to an end')],{'commission':'country_event = { id = aof_v03_regions.38 }','supply':capital_building('infrastructure'),'mediation':'country_event = { id = aof_v03_regions.38 }','settlement':'country_event = { id = aof_v03_regions.47 }'})
regional('ven',['VEN'],[('order','Условия иностранного заказа','Terms of the foreign order'),('technicians','Подготовить местных техников','Train local technicians'),('refining','Переработка в стране','Domestic refining'),('contract','Правила следующего договора','Rules for the next contract')],{'order':'country_event = { id = aof_v03_regions.39 }','technicians':bonus('industry'),'refining':capital_building(),'contract':'add_stability = 0.05 add_political_power = 40'})

# All entries are native shared_focus, reusable by later bespoke trees.
tree,loc=render_tree('aof_v03_generic',[],N,default=True)
start=tree.index(' focus = {')
definitions=tree[start:-2].replace(' focus = {','shared_focus = {')
header=tree[:start]+''.join(' shared_focus = '+n['id']+'\n' for n in N)+'}\n'
write('common/national_focus/aof_v03_generic.txt',header+'\n'+definitions)
L.update(loc)

ideas={
'civil_service':('Гражданская служба','Civil service','political_power_gain = 0.1 stability_factor = 0.03'),
'export_orders':('Мирные экспортные заказы','Peacetime export orders','trade_opinion_factor = 0.1'),
'workshop_network':('Сеть производственной кооперации','Industrial cooperation network','production_factory_efficiency_gain_factor = 0.05'),
'concession':('Ограниченная иностранная концессия','Limited foreign concession','civilian_factory_use = 1 production_factory_efficiency_gain_factor = 0.1'),
'applied_institute':('Прикладной институт','Applied institute','research_speed_factor = 0.03'),
'mobile':('Мотор решает расстояние','Engines overcome distance','new_mobile_warfare_mastery_gain_factor = 0.1 supply_consumption_factor = 0.03'),
'breakthrough':('Подготовленный прорыв','Prepared breakthrough','grand_battleplan_mastery_gain_factor = 0.1 superior_firepower_mastery_gain_factor = 0.1'),
'territorial':('Территориальная армия','Territorial army','mass_assault_mastery_gain_factor = 0.1 army_org_factor = 0.03'),
'expedition':('Экспедиционный корпус','Expeditionary corps','supply_consumption_factor = -0.05 army_org_factor = 0.02'),
'frontsky':('Небо над фронтом','Skies above the front','new_battlefield_support_mastery_gain_factor = 0.15'),
'interdiction':('Лишить противника движения','Deny enemy movement','new_strategic_destruction_mastery_gain_factor = 0.15'),
'seasky':('Небо над морем','Skies above the sea','new_operational_integrity_mastery_gain_factor = 0.15'),
'commandsea':('Владеть морем','Command the sea','new_base_strike_mastery_gain_factor = 0.15'),
'denysea':('Отрицать чужое господство','Deny hostile supremacy','new_convoy_raiding_mastery_gain_factor = 0.15'),
'safepassage':('Сохранить путь','Keep the route open','new_fleet_in_being_mastery_gain_factor = 0.15'),
'armed_neutrality':('Вооружённый нейтралитет','Armed neutrality','war_support_factor = 0.05 army_org_factor = 0.03'),
'raj_wartime_priority':('Приоритет действующему фронту','Priority for the existing front','production_speed_arms_factory_factor = 0.1 civilian_factory_use = 1'),
}
out='ideas = { country = {\n'
for key,(ru,en,mod) in ideas.items():
    ident='aof_v03_'+key
    out+=f'{ident} = {{ picture = {idea_picture(ident)} allowed = {{ always = yes }} removal_cost = -1 modifier = {{ {mod} }} }}\n'
    L[ident]=(ru,en); L[ident+'_desc']=(ru+'. Действующие условия показаны в модификаторах.',en+'. Current terms are shown in the modifiers.')
write('common/ideas/aof_v03_core.txt',out+'} }\n')

# Exact filename override: preserve installed rules and every vanilla subtype.
base=(GAME/'common/ideologies/00_ideologies.txt').read_text(encoding='utf-8-sig')
families={
'democratic':('Либерализм','Liberalism',[('market_liberalism','Рыночный либерализм','Market liberalism'),('social_liberalism','Социальный либерализм','Social liberalism'),('constitutional_federalism','Конституционный федерализм','Constitutional federalism')]),
'communism':('Революционный социализм','Revolutionary socialism',[('soviet_centralism','Советский централизм','Soviet centralism'),('pluralist_councils','Многопартийный советский социализм','Pluralist council socialism'),('syndicalism','Синдикализм','Syndicalism')]),
'neutrality':('Авторитаризм','Authoritarianism',[('military_directory','Военная директория','Military directory'),('bureaucratic_technocracy','Бюрократическая технократия','Bureaucratic technocracy'),('corporate_oligarchy','Корпоративная олигархия','Corporate oligarchy'),('absolute_monarchy','Абсолютная монархия','Absolute monarchy')]),
'fascism':('Радикальный национализм','Radical nationalism',[('national_revolution','Национал-революционизм','National revolutionism'),('integral_nationalism','Интегральный национализм','Integral nationalism'),('expansionist_imperialism','Экспансионистский империализм','Expansionist imperialism')]),
'aof_social_democracy':('Социал-демократия','Social democracy',[('parliamentary_socialism','Парламентский социализм','Parliamentary socialism'),('agrarian_social_democracy','Аграрная социал-демократия','Agrarian social democracy'),('cooperative_socialism','Кооперативный социализм','Cooperative socialism')]),
'aof_conservatism':('Консерватизм','Conservatism',[('parliamentary_conservatism','Парламентский консерватизм','Parliamentary conservatism'),('national_conservatism','Национальный консерватизм','National conservatism'),('religious_constitutionalism','Религиозный конституционализм','Religious constitutionalism')])}
for group,(ru,en,types) in families.items():
    body=' '.join('aof_'+k+' = { }' for k,_,_ in types)
    if group in ('aof_social_democracy','aof_conservatism'):
        color='215 75 130' if group=='aof_social_democracy' else '45 90 150'
        entry=f'''\n {group} = {{ types = {{ {body} }} color = {{ {color} }} dynamic_faction_names = {{ "aof_v03_faction_name" }} rules = {{ can_declare_war_on_same_ideology = no can_force_government = yes can_send_volunteers = no can_puppet = no can_lower_tension = yes can_only_justify_war_on_threat_country = yes can_guarantee_other_ideologies = yes }} can_host_government_in_exile = yes war_impact_on_world_tension = 0.25 faction_impact_on_world_tension = 0.1 modifiers = {{ generate_wargoal_tension = 1.0 join_faction_tension = 0.6 lend_lease_tension = 0.4 guarantee_tension = 0.2 }} }}\n'''
        end=base.rfind('}'); base=base[:end]+entry+base[end:]
    else:
        base,count=re.subn(r'('+group+r'\s*=\s*\{\s*types\s*=\s*\{)',lambda m:m[0]+'\n'+body,base,count=1); assert count==1
    for suffix in ('','_noun','_adj'):
        L[group+suffix]=(ru,en)
    # Native <group>_desc is a compact government value in country selection,
    # not a paragraph tooltip: keep it short enough for that fixed UI row.
    L[group+'_desc']={
        'democratic':('Либеральный кабинет','Liberal Government'),
        'communism':('Социалистическая власть','Socialist Government'),
        'fascism':('Националистический режим','Nationalist Regime'),
        'neutrality':('Авторитарный режим','Authoritarian Regime'),
        'aof_social_democracy':('Социал-демократия','Social Democracy'),
        'aof_conservatism':('Консервативный кабинет','Conservative Cabinet'),
    }[group]
    L['aof_v03_family_'+group+'_tooltip']=(ru+': политическая семья; форма государства и внешнеполитический курс определяются отдельно.',en+': a political family; state structure and foreign policy remain separate choices.')
    for key,tr,te in types:
        L['aof_'+key]=(tr,te); L['aof_'+key+'_desc']=(tr+': одна из программ этой политической семьи.',te+': one programme within this political family.')
write('common/ideologies/00_ideologies.txt',base)
# Provisional interface artwork only: these installed native group emblems
# provide readable controls until the two new families receive original art.
# The texture choice does not assign a political family or government rule.
write('interface/aof_v03_ideologies.gfx','''# PROVISIONAL UI PLACEHOLDERS: native art, not approved ideology emblems.
spriteTypes = {
 spriteType = {
  name = "GFX_ideology_aof_social_democracy_group"
  texturefile = "gfx/interface/ideologies/democratic_group.dds"
 }
 spriteType = {
  name = "GFX_ideology_aof_conservatism_group"
  texturefile = "gfx/interface/ideologies/neutrality_group.dds"
 }
}
''')
L['aof_v03_faction_name']=('Соглашение суверенных государств','Compact of Sovereign States')
L['aof_v03_research_bonus']=('Прикладная программа','Applied research programme')
L['aof_v03_doctrine_bonus']=('Военная школа','Military school')

# Native tech selection: staged industrial, communications, infantry and early chassis.
# Late jets, nuclear, rockets, modern hulls/airframes are intentionally untouched.
tech={
'industry.txt':{'basic_machine_tools':1924,'improved_machine_tools':1927,'advanced_machine_tools':1931,'assembly_line_production':1935,'flexible_line':1938,'streamlined_line':1938,'concentrated_industry':1924,'concentrated_industry2':1927,'concentrated_industry3':1931,'concentrated_industry4':1935,'concentrated_industry5':1938,'dispersed_industry':1924,'dispersed_industry2':1927,'dispersed_industry3':1931,'dispersed_industry4':1935,'dispersed_industry5':1938,**{k+str(i):y for k in ['construction','excavation'] for i,y in enumerate([1924,1927,1931,1935,1938],1)},'fuel_refining':1924,'fuel_refining2':1927,'fuel_refining3':1931,'fuel_refining4':1935,'fuel_refining5':1938,'synth_oil_experiments':1928,'oil_processing':1930,'rubber_processing':1930},
'electronic_mechanical_engineering.txt':{'electronic_mechanical_engineering':1924,'radio':1926,'mechanical_computing':1928,'computing_machine':1934,'radio_detection':1935,'basic_encryption':1927,'basic_decryption':1927,'improved_encryption':1932,'improved_decryption':1932},
'infantry.txt':{'infantry_weapons1':1924,'improved_infantry_weapons':1928,'infantry_weapons2':1932,'improved_infantry_weapons_2':1935,'infantry_at':1935,'motorised_infantry':1926,'mechanised_infantry':1935},
'artillery.txt':{'interwar_artillery':1924,'artillery1':1927,'artillery2':1931,'artillery3':1935,'interwar_antiair':1927,'antiair1':1931,'interwar_antitank':1927,'antitank1':1931},
'NSB_armor.txt':{'basic_light_tank_chassis':1924,'improved_light_tank_chassis':1928,'advanced_light_tank_chassis':1934,'basic_medium_tank_chassis':1934,'armor_tech_1':1927,'armor_tech_2':1931,'engine_tech_1':1927,'engine_tech_2':1931},
'bba_air_techs.txt':{'basic_small_airframe':1928,'improved_small_airframe':1934,'basic_medium_airframe':1929,'improved_medium_airframe':1935,'basic_large_airframe':1932,'engines_2':1928,'engines_3':1934},
'armor.txt':{'basic_light_tank':1924,'improved_light_tank':1928,'advanced_light_tank':1934,'basic_medium_tank':1934},
'air_techs.txt':{'fighter1':1928,'cv_fighter1':1928,'fighter2':1934,'cv_fighter2':1934,'tactical_bomber1':1929,'tactical_bomber2':1935,'naval_bomber1':1928,'naval_bomber2':1934,'heavy_fighter1':1929,'heavy_fighter2':1935},
'support.txt':{'tech_engineers':1924,'tech_recon':1924,'tech_logistics_company':1926,'tech_engineers2':1931,'tech_recon2':1931,'tech_logistics_company2':1931},
'MTG_naval.txt':{'basic_ship_hull_light':1927,'improved_ship_hull_light':1934,'basic_ship_hull_cruiser':1928,'improved_ship_hull_cruiser':1935,'basic_ship_hull_heavy':1929,'improved_ship_hull_heavy':1936,'basic_ship_hull_submarine':1927,'improved_ship_hull_submarine':1934,'basic_ship_hull_carrier':1930,'basic_depth_charges':1924,'improved_depth_charges':1930,'sonar':1928,'improved_sonar':1934},
}
tech['industry.txt']['fuel_silos']=1924
tech['infantry.txt'].update(tech_trucks=1924,infantry_weapons2=1927,improved_infantry_weapons=1929,improved_infantry_weapons_2=1932)
tech['electronic_mechanical_engineering.txt'].update(computing_machine=1932,basic_encryption=1932,basic_decryption=1932,improved_computing_machine=1935,improved_encryption=1935,improved_decryption=1935)
tech['air_techs.txt'].update(early_fighter=1924,cv_early_fighter=1924,early_bomber=1924)
tech['bba_air_techs.txt'].update(iw_small_airframe=1924,iw_medium_airframe=1924,iw_large_airframe=1924)
manifest={}
for filename,changes in tech.items():
    text=(GAME/'common/technologies'/filename).read_text(encoding='utf-8-sig')
    applied={}
    for key,year in changes.items():
        match=re.search(r'^\t'+re.escape(key)+r'\s*=\s*\{',text,re.M); assert match, (filename,key)
        pos=match.end(); depth=1; end=pos
        while depth:
            if text[end]=='{':depth+=1
            if text[end]=='}':depth-=1
            end+=1
        body=text[pos:end]
        old=re.search(r'start_year\s*=\s*(\d+)',body)
        replaced=re.sub(r'start_year\s*=\s*\d+','start_year = '+str(year),body,count=1) if old else '\n\t\tstart_year = '+str(year)+'\n'+body
        text=text[:pos]+replaced+text[end:]
        applied[key]={'installed':int(old[1]) if old else None,'aof':year}
    write('common/technologies/'+filename,text)
    manifest[filename]=applied
write('docs/design_v0_3/RESEARCH_DATE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

# Event authoring keeps every invitation reversible; receivers choose their answer.
events='add_namespace = aof_v03_regions\n'
def event(num,ru,en,desc_ru,desc_en,options,trigger=''):
    global events
    ident='aof_v03_regions.'+str(num)
    L[ident+'.t']=(ru,en);L[ident+'.d']=(desc_ru,desc_en)
    events+=f'country_event = {{ id = {ident} title = {ident}.t desc = {ident}.d is_triggered_only = yes\n'
    if trigger: events += ' trigger = { '+trigger+' }\n'
    for i,(r,e,effect) in enumerate(options):
        key=ident+'.'+chr(97+i);L[key]=(r,e)
        events+=f'option = {{ name = {key} {effect} }}\n'
    events+='}\n'
members=['GUA','HON','ELS','NIC','COS']
pairflags=' '.join(f'if = {{ limit = {{ FROM = {{ tag = {tag} }} }} set_country_flag = aof_v03_cooperation_{tag} }} if = {{ limit = {{ tag = {tag} }} FROM = {{ set_country_flag = aof_v03_cooperation_{tag} }} }}' for tag in members)
pairgate='OR = { '+' '.join(f'AND = {{ FROM = {{ tag = {tag} }} has_country_flag = aof_v03_cooperation_{tag} }}' for tag in members)+' }'
investment_clear='clr_country_flag = aof_v03_investment_pending clr_country_flag = aof_v03_investment_pending_USA clr_country_flag = aof_v03_investment_pending_JAP '
investment_domestic='set_country_flag = aof_v03_investment_signed set_country_flag = aof_v03_investment_domestic clr_country_flag = aof_v03_investment_foreign '+investment_clear+'add_political_power = -50'
def investment_request(tag):
    return f'trigger = {{ NOT = {{ tag = {tag} }} {tag} = {{ exists = yes }} NOT = {{ has_war_with = {tag} }} }} set_country_flag = aof_v03_investment_pending set_country_flag = aof_v03_investment_pending_{tag} {tag} = {{ country_event = {{ id = aof_v03_regions.2 days = 1 }} }}'
event(1,'Инвестиционные переговоры','Investment negotiations','Выберем существующего партнёра, с которым нет войны. Он вправе отказать; тогда остаётся внутреннее финансирование без иностранной концессии. Если ответ пропадёт при изменении мира, через 30 дней доступно решение о собственных средствах.','Choose an existing partner with whom we are not at war. They may refuse; domestic financing remains available without a foreign concession. A decision allows domestic funding after30days if world changes prevent a reply.',[('США','The United States',investment_request('USA')),('Япония','Japan',investment_request('JAP')),('Собственные средства','Domestic funds',investment_domestic)],'NOT = { has_country_flag = aof_v03_investment_signed }')
event(2,'Предложение совместного предприятия','A joint-venture proposal','Партнёр предлагает ограниченную концессию. Согласие не меняет границы и власть.','A partner offers a limited concession. Agreement changes neither borders nor government.',[('Согласиться','Accept','trigger = { FROM = { exists = yes NOT = { has_country_flag = aof_v03_investment_signed } } NOT = { has_war_with = FROM } } FROM = { set_country_flag = aof_v03_investment_signed set_country_flag = aof_v03_investment_foreign clr_country_flag = aof_v03_investment_domestic '+investment_clear+'add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } } add_political_power = 25'),('Отказать','Decline','FROM = { country_event = { id = aof_v03_regions.3 days = 1 } }')],'FROM = { exists = yes NOT = { has_country_flag = aof_v03_investment_signed } }')
event(3,'Переговоры прерваны','Negotiations suspended','Внешнее предприятие не согласовано. Можно оплатить проект самим; иностранный договор и его двухлетние обязательства нам не приписываются.','No foreign venture was agreed. We can pay for the project ourselves; no foreign contract or its two-year obligations are imposed.',[('Внутренний капитал','Domestic capital',investment_domestic)],'NOT = { has_country_flag = aof_v03_investment_signed }')
event(10,'Соглашение с соседом','An agreement with a neighbour','Предложим мирное сотрудничество соседу, с которым нет войны.','Offer peaceful cooperation to a neighbour with whom we are not at war.',[('Направить предложение','Send the proposal','random_neighbor_country = { limit = { NOT = { has_war_with = ROOT } } country_event = { id = aof_v03_regions.13 } }'),('Отложить','Postpone','add_political_power = 20')])
event(11,'Конференция суверенных стран','A conference of sovereign states','Соседи получают приглашение. Отказ не является поводом для войны.','Neighbours receive an invitation. Refusal is no cause for war.',[('Пригласить соседей','Invite our neighbours','every_neighbor_country = { limit = { NOT = { has_war_with = ROOT } } country_event = { id = aof_v03_regions.13 } }')])
event(12,'Взаимная оборона','Mutual defence','Отправим предложение независимому соседу. Он сохраняет право отказа.','Send an offer to an independent neighbour. They retain the right to refuse.',[('Предложить добровольный союз','Propose a voluntary alliance','random_neighbor_country = { limit = { is_subject = no NOT = { has_war_with = ROOT } } country_event = { id = aof_diplomacy.120 } }'),('Подготовить собственную оборону','Prepare our own defence','army_experience = 20')])
event(13,'Приглашение к сотрудничеству','An invitation to cooperate','Сосед предлагает соглашение равных участников. Обязательного вступления в союз нет.','Our neighbour offers cooperation among equals. No alliance membership is imposed.',[('Принять','Accept','add_stability = 0.02 add_opinion_modifier = { target = FROM modifier = aof_v03_cooperation } FROM = { add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } } '+pairflags),('Сохранить дистанцию','Keep our distance','add_political_power = 15')])
event(20,'Полномочия зависимого кабинета','The powers of a dependent cabinet','Покровитель должен сам ответить на требование расширить гражданские полномочия.','The patron must answer our request to expand civilian authority.',[('Направить требование','Send the request','overlord = { country_event = { id = aof_v03_regions.21 } }')])
event(21,'Требование местного кабинета','A local cabinet requests powers','Можно расширить местное управление со штатным ростом автономии, предложить согласованную независимость или сохранить мандат. Предложение независимости требует отдельного согласия зависимой страны и не прекращает чужих войн.','Devolve local government with native autonomy progress, offer agreed independence or retain the mandate. Independence requires the dependent country’s separate consent and does not end anyone else’s war.', [('Расширить полномочия и автономию','Devolve authority and autonomy','FROM = { if = { limit = { is_subject_of = ROOT NOT = { has_country_flag = aof_v03_local_powers } } add_stability = 0.05 add_political_power = 50 add_autonomy_score = { value = 100 localization = aof_v03_local_mandate } set_country_flag = aof_v03_local_powers } }'),('Предложить независимость вне нашего блока','Offer independence outside our bloc','trigger = { has_war = no FROM = { is_subject_of = ROOT has_war = no NOT = { has_country_flag = aof_v03_independence_offer_pending } } } FROM = { set_country_flag = aof_v03_independence_offer_pending country_event = { id = aof_v03_regions.49 days = 1 } }'),('Сохранить мандат','Retain the mandate','FROM = { add_stability = -0.03 add_political_power = 25 }')],'FROM = { exists = yes is_subject_of = ROOT }')
event(30,'Устройство Карелии','The settlement of Karelia','Представительство местных общин или пограничная администрация? Новые войны не предрешены.','Local representation or a border administration? No further war is predetermined.',[('Представительство общин','Community representation','add_stability = 0.06 add_political_power = -25'),('Пограничная администрация','Border administration','army_experience = 25 add_war_support = 0.04')])
event(31,'Собственная опора','Our own foundations','Японский ответ не отменяет необходимости обучать собственные кадры.','The Japanese answer does not remove the need to train our own personnel.',[('Местные кадры','Local personnel',bonus('industry')),('Внешняя опора','External support','country_event = { id = aof_v03_regions.1 }')])
event(32,'Полномочия Туркестана','Turkestani responsibilities','Выбор между местным управлением и единой исполнительной властью.','Choose between local administration and a common executive.',[('Договор участников','A compact of members','add_stability = 0.05 add_political_power = -25'),('Единая исполнительная власть','A common executive','add_political_power = 75 add_stability = -0.03')])
event(33,'Сохранить союз','Preserve the union','Съезд может сохранить союз или открыть подтверждение согласованного мирного раздела. Перед изменением территории будут показаны точные условия и проверены права участников.','The congress can preserve the union or open confirmation of an agreed peaceful partition. Exact terms and participant rights are checked before territory changes.',[('Подтвердить союз','Reaffirm the union','add_stability = 0.07'),('Открыть переговоры о разделе','Open separation negotiations','country_event = { id = aof_partition.1 days = 1 }')])
event(34,'Военное управление','Government during war','Снабжение фронта не решает, кто будет править после войны.','Supplying the front does not determine who governs after the war.',[('Гражданский кабинет','A civilian cabinet','add_stability = 0.06 add_war_support = -0.03'),('Чрезвычайное командование','Emergency command','army_experience = 30 add_war_support = 0.06 add_stability = -0.03')])
event(35,'Канадские обязательства','Canadian obligations','Если страна зависима, пересмотр полномочий требует ответа покровителя; независимая страна пересматривает свои обязательства сама.','A dependent country requires its patron to answer; an independent country reviews its own obligations.',[('Пересмотреть обязательства','Review our obligations','if = { limit = { is_subject = yes } country_event = { id = aof_v03_regions.20 } } else = { add_political_power = 50 }')])
event(36,'Направление канадской торговли','The direction of Canadian trade','Океанские связи или североамериканский рынок?','Oceanic links or the North American market?', [('Океанские связи','Oceanic links','navy_experience = 25'),('Североамериканский рынок','North American market','add_ideas = aof_v03_export_orders')])
fullcontrol='NOT = { any_owned_state = { NOT = { is_controlled_by = PREV } } }'
unionoffers=' '.join(f'if = {{ limit = {{ NOT = {{ tag = {tag} }} {tag} = {{ exists = yes is_subject = no has_war = no {fullcontrol} }} }} {tag} = {{ country_event = {{ id = aof_v03_regions.40 days = 1 }} }} }}' for tag in members)
unionmember='OR = { '+' '.join('tag = '+tag for tag in members)+' }'
event(37,'Федеративный договор','A federal compact','После транзитного и оборонного сотрудничества можно сохранить союз суверенных участников или предложить территориальную федерацию Гватемале, Гондурасу, Сальвадору, Никарагуа и Коста-Рике. Каждая страна решает сама. Согласившийся участник передаёт свои территории общему правительству; отказ не приводит к войне.','After transit and defence cooperation, retain a compact of sovereign members or propose territorial federation to Guatemala, Honduras, El Salvador, Nicaragua and Costa Rica. Each decides independently. An accepting member transfers its territory to the common government; refusal does not cause war.',[('Предложить добровольную территориальную федерацию','Propose a voluntary territorial federation','trigger = { is_subject = no has_war = no '+fullcontrol+' '+unionmember+' } '+unionoffers),('Сохранить союз суверенных участников','Retain a compact of sovereign members','add_stability = 0.04 country_event = { id = aof_v03_regions.12 }')])
event(40,'Вступить в Центральноамериканскую федерацию?','Join the Central American Federation?','Прежний партнёр предлагает объединение территорий. Принятие упраздняет отдельное правительство: все наши собственные земли, включая внешние владения, и войска перейдут общему государству. Национальные права возникают только на нашей прежней национальной территории. Игрок, желающий продолжать отдельную кампанию, должен отказаться. Согласие возможно только для мирной независимой страны после принятого двустороннего сотрудничества.','Our existing partner proposes territorial union. Acceptance ends our separate government: all our owned lands, including outlying possessions, and troops join the common state. New cores apply only to our former core states. A player wishing to continue a separate campaign should decline. Only a peaceful independent country with previously accepted bilateral cooperation can consent.',[('Принять: передать территории общему государству','Accept: transfer our territory to the common state','trigger = { is_subject = no has_war = no '+fullcontrol+' '+pairgate+' FROM = { exists = yes is_subject = no has_war = no '+fullcontrol+' OR = { '+' '.join('tag = '+t for t in members)+' } } } ai_chance = { factor = 1 } every_owned_state = { limit = { is_core_of = ROOT } add_core_of = FROM } FROM = { set_cosmetic_tag = aof_central_american_federation annex_country = { target = ROOT transfer_troops = yes } }'),('Сохранить независимость и прежнее сотрудничество','Retain independence and existing cooperation','ai_chance = { factor = 99 } add_stability = 0.03')])
for family in list(families)+['']:
    stem='aof_central_american_federation'+('_'+family if family else '')
    L[stem]=('Центральноамериканская Федерация','Central American Federation')
    L[stem+'_DEF']=('Центральноамериканская Федерация','the Central American Federation')
    L[stem+'_ADJ']=('Центральноамериканск.','Central American')
# 688 is the installed disputed Chaco Boreal, PAR-owned with BOL/PAR cores.
# 509 is Argentine Gran Chaco and is deliberately outside this bilateral crisis.
chaco_source=(GAME/'history/states/688-Chaco Boreal.txt').read_text(encoding='utf-8-sig')
assert re.search(r'\bid\s*=\s*688\b',chaco_source)
assert all(re.search(r'add_core_of\s*=\s*'+t+r'\b',chaco_source) for t in ['BOL','PAR'])
chaco_world='BOL = { exists = yes is_subject = no has_war = no } PAR = { exists = yes is_subject = no has_war = no } 688 = { OR = { is_owned_by = BOL is_owned_by = PAR } }'
chaco_actor='OR = { tag = BOL tag = PAR } '+chaco_world
chaco_pair='OR = { AND = { tag = BOL FROM = { tag = PAR } } AND = { tag = PAR FROM = { tag = BOL } } } '
def chaco_send(number):
    return 'if = { limit = { tag = BOL } PAR = { country_event = { id = aof_v03_regions.'+str(number)+' days = 1 } } } else_if = { limit = { tag = PAR } BOL = { country_event = { id = aof_v03_regions.'+str(number)+' days = 1 } } }'
chaco_coop='BOL = { set_country_flag = aof_v03_chaco_settled clr_country_flag = aof_v03_chaco_pending add_stability = 0.04 add_opinion_modifier = { target = PAR modifier = aof_v03_cooperation } } PAR = { set_country_flag = aof_v03_chaco_settled clr_country_flag = aof_v03_chaco_pending add_stability = 0.04 add_opinion_modifier = { target = BOL modifier = aof_v03_cooperation } }'
chaco_begin='BOL = { set_country_flag = aof_v03_chaco_pending clr_country_flag = aof_v03_chaco_arbitration_yes clr_country_flag = aof_v03_chaco_refused } PAR = { set_country_flag = aof_v03_chaco_pending clr_country_flag = aof_v03_chaco_arbitration_yes clr_country_flag = aof_v03_chaco_refused } '
chaco_refused='BOL = { set_country_flag = aof_v03_chaco_refused clr_country_flag = aof_v03_chaco_pending } PAR = { set_country_flag = aof_v03_chaco_refused clr_country_flag = aof_v03_chaco_pending } '
event(38,'Предмет спора: Чако','The disputed Chaco','Спор касается только установленной области 688, Чако-Бореаль: она принадлежит Парагваю, а национальные права имеют обе стороны. Аргентинская область 509 не входит в предложение. Предложим взаимное признание нынешнего владения без уничтожения национальных прав, либо попросим арбитраж. Ни одно решение здесь не меняет границы автоматически.','The dispute concerns installed state 688, Chaco Boreal, currently Paraguayan with both countries’ cores. Argentine state 509 is outside this offer. Propose recognition of current possession without erasing national rights, or seek arbitration. No option here automatically changes borders.',[('Направить двустороннее предложение','Send a bilateral proposal','trigger = { NOT = { has_country_flag = aof_v03_chaco_settled } } add_political_power = -25 '+chaco_begin+chaco_send(44)),('Подготовить ограниченный военный вариант','Review a limited military contingency','country_event = { id = aof_v03_regions.47 days = 1 }'),('Отложить спор без эскалации','Set the dispute aside','add_stability = 0.02')],chaco_actor)

event(39,'Условия нефтяного заказа','The terms of the oil order','Быстрый экспорт или подготовка собственной переработки?','Immediate exports or preparation for domestic refining?', [('Расширить экспортную концессию','Expand export concessions','add_ideas = aof_v03_export_orders add_political_power = 50'),('Обучить местных техников','Train local technicians',bonus('industry'))])
event(41,'Долгая конституция','A durable constitution','После подготовки гарантий парламент определяет общественный договор. Либеральный кабинет или консервативная преемственность сохраняют выборы.','After preparing safeguards, parliament settles the social compact. A liberal cabinet and conservative continuity both retain elections.',[('Либеральное правительство','A liberal government',government('democratic')+' add_stability = 0.05'),('Консервативный парламентский кабинет','A conservative parliamentary cabinet',government('aof_conservatism')+' add_stability = 0.05')])
event(42,'Возвращение гражданского мандата','Return of the civilian mandate','Чрезвычайные полномочия заканчиваются. Гражданское правительство будет отвечать перед избирателями.','Emergency powers end. Civilian government will answer to the electorate.',[('Консервативный гражданский кабинет','A conservative civilian cabinet',government('aof_conservatism')+' add_stability = 0.05'),('Либеральная конституция','A liberal constitution',government('democratic')+' add_stability = 0.03 add_political_power = 20')])

event(43,'Институт снова открывает двери','An institute reopens its doors','Восстановленный прикладной институт может пригласить домой специалиста, работающего в США или Японии. Принимающая держава сама решит, удержать его заказом, создать совместную кафедру или поддержать передачу опыта. Оплата предложения не гарантирует согласия.','Our rebuilt applied institute can invite a specialist working in America or Japan to return. The host decides whether to retain the scholar, establish a joint department or support a transfer of expertise. Paying for an offer does not guarantee agreement.',[
 ('Пригласить из американской школы','Approach the American school','trigger = { country_exists = USA NOT = { has_war_with = USA } } add_political_power = -35 USA = { country_event = { id = aof_diplomacy.100 days = 2 } }'),
 ('Пригласить из японской школы','Approach the Japanese school','trigger = { country_exists = JAP NOT = { has_war_with = JAP } } add_political_power = -35 JAP = { country_event = { id = aof_diplomacy.100 days = 2 } }'),
 ('Сначала подготовить собственных учеников','Prepare our own students first','add_political_power = -20 '+bonus('electronics'))],
 'has_country_flag = aof_war_exhausted capital_scope = { is_on_continent = europe }')
event(44,'Встречное предложение по Чако','A bilateral proposal on Chaco','Сосед предлагает признать нынешнего владельца области 688 и закончить кризис, сохранив национальные права сторон. Можно согласиться, попросить Аргентину провести арбитраж или отказать. Никто не передаёт нашу землю без нашего решения.','Our neighbour proposes recognising the present owner of state 688 and closing the crisis while preserving both sides’ cores. Accept, seek Argentine arbitration or refuse. Our land cannot be transferred without our decision.',[
 ('Признать нынешнее владение и закончить кризис','Recognise current possession and end the crisis',chaco_coop+' FROM = { country_event = { id = aof_v03_regions.45 days = 1 } }'),
 ('Попросить независимый аргентинский арбитраж','Request independent Argentine arbitration','trigger = { ARG = { exists = yes is_subject = no has_war = no } NOT = { has_war_with = ARG } FROM = { NOT = { has_war_with = ARG } } } add_political_power = -15 ARG = { country_event = { id = aof_v03_regions.46 days = 1 } }'),
 ('Отказать и сохранить свободу действий','Decline and retain our freedom of action',chaco_refused+' FROM = { country_event = { id = aof_v03_regions.47 days = 1 } }')],
 chaco_pair+chaco_world+' BOL = { has_country_flag = aof_v03_chaco_pending } PAR = { has_country_flag = aof_v03_chaco_pending }')
event(45,'Чако: согласие двух правительств','Chaco: agreement between two governments','Оба правительства согласились сохранить нынешнее владение областью 688 и завершить текущий кризис. Национальные права сторон не удалены. Война не началась, территории не переданы, Аргентинский Чако не затронут.','Both governments agreed to preserve current possession of state 688 and close the present crisis. Neither side’s cores were removed. No war began, no territory changed hands, and Argentine Chaco was unaffected.',[('Исполнять договор','Honour the agreement','add_political_power = 20')],chaco_actor+' has_country_flag = aof_v03_chaco_settled')
event(46,'Аргентинский арбитраж Чако','Argentine arbitration of Chaco','Одна из сторон просит предложить решение спора Боливии и Парагвая. Рекомендация сохранить нынешнее владение Чако-Бореаль вступит в силу только после отдельного согласия обоих правительств. Мы можем отказаться от посредничества.','One party asks us to propose a settlement between Bolivia and Paraguay. A recommendation to preserve present possession of Chaco Boreal takes effect only after both governments separately accept. We may decline to mediate.',[
 ('Предложить нынешнюю границу с сохранением национальных прав','Recommend current possession while retaining cores','add_political_power = -20 BOL = { country_event = { id = aof_v03_regions.48 days = 1 } } PAR = { country_event = { id = aof_v03_regions.48 days = 1 } }'),
 ('Не принимать арбитражный мандат','Decline the arbitration mandate',chaco_refused+' BOL = { country_event = { id = aof_v03_regions.47 days = 1 } } PAR = { country_event = { id = aof_v03_regions.47 days = 1 } }')],
 'tag = ARG is_subject = no has_war = no FROM = { OR = { tag = BOL tag = PAR } } '+chaco_world+' BOL = { has_country_flag = aof_v03_chaco_pending } PAR = { has_country_flag = aof_v03_chaco_pending }')
chaco_goal='if = { limit = { tag = BOL PAR = { owns_state = 688 } } create_wargoal = { type = take_state_focus target = PAR generator = { 688 } } } else_if = { limit = { tag = PAR BOL = { owns_state = 688 } } create_wargoal = { type = take_state_focus target = BOL generator = { 688 } } }'
event(47,'Чако: пределы эскалации','Chaco: the limits of escalation','Переговоры не обязывают нас воевать. Можно сохранить мир или подготовить ограниченную цель войны только против нынешнего боливийского либо парагвайского владельца области 688. Если область уже наша, такой цели нет: остаётся оборонная подготовка. Эта кнопка не объявляет войну и не обещает автоматического ограниченного мира после боёв.','Negotiations do not compel war. Retain peace, or prepare a state-specific war goal against the current Bolivian or Paraguayan owner of state 688. If we already own it, there is no such goal: defensive preparation remains available. This option neither declares war nor guarantees a scripted limited peace after fighting.',[
 ('Сохранить мир и продолжить работу комиссии','Retain peace and continue the commission','add_stability = 0.03'),
 ('Оформить цель войны только на область 688','Prepare a war goal for state 688 only','trigger = { NOT = { has_country_flag = aof_v03_chaco_settled } NOT = { has_country_flag = aof_v03_chaco_goal_prepared } OR = { AND = { tag = BOL PAR = { owns_state = 688 } } AND = { tag = PAR BOL = { owns_state = 688 } } } } add_political_power = -50 add_stability = -0.04 '+chaco_goal+' set_country_flag = aof_v03_chaco_goal_prepared'),
 ('Подготовить оборону без территориальной цели','Prepare defence without a territorial goal','army_experience = 15 add_political_power = -20')],chaco_actor)
event(48,'Принять арбитраж по Чако?','Accept Chaco arbitration?','Аргентина рекомендует сохранить нынешнее владение областью 688. Национальные права не стираются. Рекомендация становится договором только при согласии обоих правительств; отказ сохраняет нашу самостоятельность и не начинает войну.','Argentina recommends preserving current possession of state 688 without removing cores. Its recommendation becomes an agreement only if both governments accept; refusal preserves sovereignty and does not start a war.',[
 ('Принять рекомендацию при согласии соседа','Accept if our neighbour also accepts','set_country_flag = aof_v03_chaco_arbitration_yes if = { limit = { BOL = { has_country_flag = aof_v03_chaco_arbitration_yes } PAR = { has_country_flag = aof_v03_chaco_arbitration_yes } } '+chaco_coop+' BOL = { country_event = { id = aof_v03_regions.45 days = 1 } } PAR = { country_event = { id = aof_v03_regions.45 days = 1 } } }'),
 ('Отказать в арбитражном решении','Reject the arbitration recommendation',chaco_refused+' country_event = { id = aof_v03_regions.47 days = 1 } '+chaco_send(47))],
 chaco_actor+' FROM = { tag = ARG exists = yes } BOL = { has_country_flag = aof_v03_chaco_pending } PAR = { has_country_flag = aof_v03_chaco_pending }')

# The overlord offers; the subject separately accepts. No unilateral forced
# independence, faction removal or ending another country's war.
independence_guard='is_subject = yes is_subject_of = FROM has_war = no FROM = { exists = yes has_war = no } has_country_flag = aof_v03_independence_offer_pending'
event(49,'Предложение договорной независимости','An offer of negotiated independence','Покровитель согласен отпустить нас. Принятие прекращает зависимость штатным эффектом и выводит нас из его блока, если мы в одном союзе. Оно не аннексирует страну и не завершает чужих войн. Можно сохранить нынешний статус.','Our patron is willing to release us. Acceptance ends dependency through the native effect and leaves their faction if we share one. It annexes no country and does not end anyone else’s war. We may retain the current status.',[
 ('Принять независимость вне блока покровителя','Accept independence outside the patron’s bloc','ai_chance = { factor = 60 } trigger = { '+independence_guard+' } if = { limit = { '+independence_guard+' } FROM = { set_autonomy = { target = ROOT autonomy_state = autonomy_free end_wars = no end_civil_wars = no } } if = { limit = { is_in_faction_with = FROM } leave_faction = yes } clr_country_flag = aof_v03_independence_offer_pending set_country_flag = aof_v03_independence_accepted set_country_flag = aof_v03_local_powers add_political_power = -50 add_stability = 0.05 mark_focus_tree_layout_dirty = yes }'),
 ('Сохранить нынешний мандат','Retain the current mandate','ai_chance = { factor = 40 } clr_country_flag = aof_v03_independence_offer_pending add_political_power = 15')],independence_guard)
L['aof_v03_local_mandate']=('Согласованное расширение местных полномочий','Agreed devolution of local authority')

# Karelia recognition is an actual Soviet response, not a unilateral buff.
finland_guard='FIN = { exists = yes owns_state = 215 owns_state = 216 } NOT = { FIN = { has_war_with = SOV } }'
fin_agree='set_country_flag = aof_v03_fin_border_recognized FROM = { set_country_flag = aof_v03_fin_border_recognized clr_country_flag = aof_v03_fin_border_refused add_stability = 0.05 add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } country_event = { id = aof_v03_regions.51 days = 1 } } add_opinion_modifier = { target = FROM modifier = aof_v03_cooperation }'
event(50,'Финляндия предлагает признать границу','Finland proposes border recognition','Финляндия просит признать её нынешнее владение Карелией, областями 215 и 216. Мы можем согласиться либо оставить вопрос открытым. Петроград не входит в предложение; никакие территории и национальные права не передаются этой кнопкой.','Finland asks us to recognise its present possession of Karelia, states215 and216. We can agree or leave the question open. Petrograd is outside the proposal; no territory or national cores change through this option.',[
 ('Признать нынешнюю границу','Recognise the current border','ai_chance = { factor = 40 } '+fin_agree),
 ('Оставить вопрос открытым','Leave the question open','ai_chance = { factor = 60 } FROM = { set_country_flag = aof_v03_fin_border_refused army_experience = 15 country_event = { id = aof_v03_regions.51 days = 1 } }')],
 'tag = SOV FROM = { tag = FIN } '+finland_guard)
event(51,'Ответ по карельской границе','The response on Karelia','Сосед дал ответ. Признание улучшает отношения и устойчивость; отказ оставляет вопрос открытым и требует оборонной подготовки, но не начинает войну.','Our neighbour has replied. Recognition improves relations and stability; refusal leaves the question open and calls for defensive preparation, but starts no war.',[
 ('Исполнять признанное соглашение','Honour the recognised agreement','trigger = { has_country_flag = aof_v03_fin_border_recognized } add_political_power = 15'),
 ('Готовить рубежи без новой войны','Prepare the frontier without a new war','trigger = { has_country_flag = aof_v03_fin_border_refused } add_war_support = 0.03')],
 'tag = FIN FROM = { tag = SOV } OR = { has_country_flag = aof_v03_fin_border_recognized has_country_flag = aof_v03_fin_border_refused }')

# A bounded negotiated ending for a genuinely bilateral Chaco war. No faction,
# global or civil war is touched, and a third country's state is never transferred.
chaco_war='BOL = { exists = yes is_subject = no is_in_faction = no has_civil_war = no has_capitulated = no is_in_peace_conference = no has_war_with = PAR all_enemy_country = { tag = PAR } } PAR = { exists = yes is_subject = no is_in_faction = no has_civil_war = no has_capitulated = no is_in_peace_conference = no has_war_with = BOL all_enemy_country = { tag = BOL } } 688 = { OR = { is_owned_by = BOL is_owned_by = PAR } OR = { is_controlled_by = BOL is_controlled_by = PAR } }'
chaco_war_actor='OR = { tag = BOL tag = PAR } '+chaco_war
chaco_no_peace_pending='BOL = { NOT = { has_country_flag = aof_v03_chaco_peace_pending } } PAR = { NOT = { has_country_flag = aof_v03_chaco_peace_pending } }'
chaco_peace_clear=' '.join(tag+' = { clr_country_flag = aof_v03_chaco_peace_pending clr_country_flag = aof_v03_chaco_peace_to_BOL clr_country_flag = aof_v03_chaco_peace_to_PAR clr_country_flag = aof_v03_chaco_peace_initiator }' for tag in ['BOL','PAR'])
def chaco_peace_offer(target):
    return chaco_peace_clear+' BOL = { set_country_flag = aof_v03_chaco_peace_pending set_country_flag = aof_v03_chaco_peace_to_'+target+' } PAR = { set_country_flag = aof_v03_chaco_peace_pending set_country_flag = aof_v03_chaco_peace_to_'+target+' } set_country_flag = aof_v03_chaco_peace_initiator add_political_power = -25 '+chaco_send(53)
event(52,'Предложить ограниченный мир по Чако','Propose a limited peace over Chaco','Подтвердим точные условия: область 688 закрепляется за её нынешним контролирующим государством, остальные занятые земли возвращаются прежним владельцам по белому миру. Вторая сторона должна явно согласиться; при изменении контроля до ответа условия устареют. Аргентинская область 509 не затрагивается.','Confirm exact terms: state688 goes to its current controller; all other occupied territory returns to its owners through white peace. The other government must explicitly accept. A change of control before its reply makes the offer stale. Argentine state509 is unaffected.',[
 ('Предложить мир с областью 688 у Боливии','Offer peace with state688 held by Bolivia','trigger = { '+chaco_war+' '+chaco_no_peace_pending+' 688 = { is_controlled_by = BOL } } '+chaco_peace_offer('BOL')),
 ('Предложить мир с областью 688 у Парагвая','Offer peace with state688 held by Paraguay','trigger = { '+chaco_war+' '+chaco_no_peace_pending+' 688 = { is_controlled_by = PAR } } '+chaco_peace_offer('PAR')),
 ('Пока не направлять предложение','Do not send an offer yet','')],chaco_war_actor+' '+chaco_no_peace_pending)
def chaco_peace_accept(target):
    terms='BOL = { has_country_flag = aof_v03_chaco_peace_to_'+target+' } PAR = { has_country_flag = aof_v03_chaco_peace_to_'+target+' } 688 = { is_controlled_by = '+target+' }'
    opponent='PAR' if target=='BOL' else 'BOL'
    effect='if = { limit = { '+chaco_war+' '+terms+' } '+target+' = { white_peace = '+opponent+' } if = { limit = { 688 = { NOT = { is_owned_by = '+target+' } } } '+target+' = { transfer_state = 688 } } '+chaco_coop+' '+chaco_peace_clear+' BOL = { country_event = { id = aof_v03_regions.54 days = 1 } } PAR = { country_event = { id = aof_v03_regions.54 days = 1 } } }'
    return 'trigger = { '+chaco_war+' '+terms+' } '+effect
event(53,'Принять ограниченный мир по Чако?','Accept a limited peace over Chaco?','Противник предлагает закончить только двустороннюю войну. По выбранным условиям нынешний контролирующий участник получает область 688; другие занятые земли возвращаются владельцам. Национальные права сохраняются. Это реальный белый мир с единственным согласованным территориальным исключением. Можно отказаться. Если вмешалась третья страна, появился союз или изменился контроль, согласие недоступно.','Our opponent proposes ending this bilateral war only. Under the offered terms, the current controlling participant receives state688; other occupied lands return to their owners. Cores remain. This is actual white peace with one explicitly agreed territorial exception. We may refuse. Acceptance is unavailable if a third country joins, either party enters a faction or control changes.',[
 ('Принять: мир и область 688 у Боливии','Accept: peace and state688 held by Bolivia',chaco_peace_accept('BOL')),
 ('Принять: мир и область 688 у Парагвая','Accept: peace and state688 held by Paraguay',chaco_peace_accept('PAR')),
 ('Отказать или отозвать устаревшие условия','Refuse or withdraw stale terms',chaco_peace_clear)],
 chaco_pair+' BOL = { has_country_flag = aof_v03_chaco_peace_pending } PAR = { has_country_flag = aof_v03_chaco_peace_pending } FROM = { has_country_flag = aof_v03_chaco_peace_initiator }')
event(54,'Ограниченный мир заключён','A limited peace is concluded','Правительства согласовали прекращение двусторонних боёв и владение Чако-Бореаль, областью 688. Другие области не аннексированы, национальные права не удалены. Дальнейшая политика остаётся нашим решением.','The governments agreed to end bilateral hostilities and settle possession of Chaco Boreal, state688. No other states were annexed and no cores were removed. Future policy remains our choice.',[
 ('Соблюдать согласованный мир','Honour the agreed peace','add_political_power = 15')],
 'OR = { tag = BOL tag = PAR } has_country_flag = aof_v03_chaco_settled BOL = { NOT = { has_war_with = PAR } }')
event(55,'Канадские внешние полномочия','Canadian external authority','Независимая страна может заключать собственные соглашения. Зависимый кабинет сначала обращается к покровителю: местные полномочия и автономия не равны независимости. Отказ не мешает торговле и внутренней оборонной программе.','An independent country may negotiate its own agreements. A dependent cabinet must first approach its patron: local powers and autonomy are not independence. Refusal does not block trade or domestic defence.',[
 ('Заключать собственные соседские соглашения','Negotiate our own neighbour agreements','trigger = { is_subject = no } country_event = { id = aof_v03_regions.10 days = 1 }'),
 ('Обсудить полномочия с покровителем','Discuss authority with our patron','trigger = { is_subject = yes } country_event = { id = aof_v03_regions.20 days = 1 }'),
 ('Расширить торговлю при нынешнем статусе','Expand trade under the current status','add_ideas = aof_v03_export_orders add_political_power = 25')],'tag = CAN')

# These are ordinary native decisions, not debug content or an economic system.
project_category='aof_v03_core_projects'
fallback='has_country_flag = aof_v03_investment_pending NOT = { has_country_flag = aof_v03_investment_signed } OR = { has_country_flag = { flag = aof_v03_investment_pending days > 30 } AND = { has_country_flag = aof_v03_investment_pending_USA OR = { NOT = { country_exists = USA } has_war_with = USA } } AND = { has_country_flag = aof_v03_investment_pending_JAP OR = { NOT = { country_exists = JAP } has_war_with = JAP } } }'
write('common/decisions/categories/aof_v03_core_projects.txt',project_category+' = { icon = generic_research allowed = { always = yes } visible = { OR = { has_country_flag = aof_v03_investment_pending AND = { OR = { tag = BOL tag = PAR } OR = { has_war = yes has_country_flag = aof_v03_chaco_peace_pending } } } } }\n')
write('common/decisions/aof_v03_core_projects.txt',project_category+''' = {
 aof_v03_domestic_investment_fallback = {
  icon = generic_research allowed = { always = yes }
  visible = { has_country_flag = aof_v03_investment_pending NOT = { has_country_flag = aof_v03_investment_signed } }
  available = { '''+fallback+''' }
  cost = 0 complete_effect = { if = { limit = { '''+fallback+''' } country_event = { id = aof_v03_regions.3 days = 1 } } }
  ai_will_do = { factor = 1 }
 }
 aof_v03_chaco_limited_peace_offer = {
  icon = generic_political_discourse allowed = { OR = { tag = BOL tag = PAR } }
  visible = { OR = { AND = { tag = BOL has_war_with = PAR } AND = { tag = PAR has_war_with = BOL } } }
  available = { '''+chaco_war_actor+' '+chaco_no_peace_pending+''' }
  cost = 0 days_re_enable = 30
  complete_effect = { if = { limit = { '''+chaco_war_actor+' '+chaco_no_peace_pending+''' } country_event = { id = aof_v03_regions.52 days = 1 } } }
  ai_will_do = { factor = 1 }
 }
 aof_v03_chaco_withdraw_stale_offer = {
  icon = generic_political_discourse allowed = { OR = { tag = BOL tag = PAR } }
  visible = { has_country_flag = aof_v03_chaco_peace_pending }
  available = { has_country_flag = aof_v03_chaco_peace_pending }
  cost = 0 complete_effect = { '''+chaco_peace_clear+''' }
  ai_will_do = { factor = 1 modifier = { factor = 0 '''+chaco_war+''' NOT = { has_country_flag = { flag = aof_v03_chaco_peace_pending days > 30 } } } }
 }
}
''')
L[project_category]=('Договорные проекты','Projects by agreement')
L[project_category+'_desc']=('Выход из затянувшихся переговоров и ограниченные мирные предложения через штатные решения.','Native decisions for stalled negotiations and bounded peace offers.')
L['aof_v03_domestic_investment_fallback']=('Оплатить промышленный проект своими средствами','Fund the industrial project domestically')
L['aof_v03_domestic_investment_fallback_desc']=('Если ответа нет 30 дней либо партнёр исчез или стал противником, можно открыть внутреннее финансирование за 50 политической власти без иностранной концессии. Уже подписанный договор не дублируется.','After30days without a reply, or if the partner disappears or becomes an enemy, open domestic funding for50political power without a foreign concession. A signed contract cannot be duplicated.')
L['aof_v03_chaco_limited_peace_offer']=('Чако: предложить ограниченный мир','Chaco: propose a limited peace')
L['aof_v03_chaco_limited_peace_offer_desc']=('Только отдельная война независимых Боливии и Парагвая без фракций, иных противников, гражданской войны или конференции. Сначала явно подтвердим точного получателя области 688; затем противник принимает или отказывает. Контроль перепроверяется до белого мира и единственного согласованного переноса. Новая война автоматически не объявляется.','Only an isolated war between independent Bolivia and Paraguay, without factions, other enemies, civil war or a peace conference. First explicitly confirm the recipient of state688; then the opponent accepts or refuses. Control is rechecked before white peace and the single agreed transfer. No new war is automatically declared.')
L['aof_v03_chaco_withdraw_stale_offer']=('Чако: отозвать ожидающее предложение','Chaco: withdraw the pending offer')
L['aof_v03_chaco_withdraw_stale_offer_desc']=('Очистить только ожидающие условия, если переговоры устарели, началась другая война или противник не отвечает. Это не заключает мир и не передаёт землю. ИИ сохраняет действующее предложение до 30 дней, пока двусторонние условия не нарушены.','Clear only the pending terms when negotiations become stale, another war begins or no reply arrives. This makes no peace and transfers no land. The AI retains a valid bilateral offer for up to30days.')

write('events/aof_v03_regions.txt',events)
write('common/opinion_modifiers/aof_v03_core.txt','opinion_modifiers = { aof_v03_cooperation = { value = 20 months = 24 } }\n')
L['aof_v03_cooperation']=('Договорное сотрудничество','Cooperation by agreement')
localize('aof_v03_core',L)
print(f'Core: {len(N)} shared focuses, {len(ideas)} ideas, {len(families)} ideology families, {sum(map(len,tech.values()))} research dates, {events.count("country_event = { id = aof_v03_regions.")} event/call entries; {len(L)} localisation keys/language')
