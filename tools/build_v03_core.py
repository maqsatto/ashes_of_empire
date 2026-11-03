"""Author the v0.3 common framework against the installed 1.19 database.
Only explicitly selected start_year values are changed in native technology files.
"""
from pathlib import Path
import re, json
from contentlib import write, localize, render_tree, capital_building
from ideaicons import idea_picture

GAME=Path('C:/Hearts of Iron IV')
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
chain([('capital','Внутренний капитал','Domestic capital'),('procurement','Государственный заказ','Public procurement'),('cooperation','Производственная кооперация','Industrial cooperation')],14,effects={'capital':'add_political_power = -25 add_stability = 0.03','procurement':capital_building(),'cooperation':'add_ideas = aof_v03_workshop_network'})
focus('talks','Открыть инвестиционные переговоры','Open investment talks',17,0,effect='country_event = { id = aof_v03_regions.1 }',excludes=['aof_v03_g_capital'])
N[-4]['excludes']=['aof_v03_g_talks']
focus('concession','Ограниченная концессия','A limited concession',17,1,['talks'],available='has_country_flag = aof_v03_investment_signed',effect='add_timed_idea = { idea = aof_v03_concession days = 730 } '+capital_building())
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
chain([('harbour','Гражданская гавань','A civilian harbour'),('shiprepair','Ремонтная верфь','A repair shipyard'),('coastguard','Береговая охрана','The coast guard')],47,branch=coast,available=coast,effects={'harbour':'navy_experience = 15','shiprepair':'random_owned_controlled_state = { limit = { is_coastal = yes } add_extra_state_shared_building_slots = 1 add_building_construction = { type = dockyard level = 1 instant_build = yes } }','coastguard':bonus('naval_equipment')})
for i,(key,ru,en) in enumerate([('commandsea','Владеть морем','Command the sea'),('denysea','Отрицать чужое господство','Deny hostile supremacy'),('safepassage','Сохранить путь','Keep the route open')]):
    focus(key,ru,en,45+i*2,3,['coastguard'],effect='navy_experience = 25 '+doctrine('naval')+' add_ideas = aof_v03_'+key,branch=coast,available=coast,excludes=['aof_v03_g_'+k for k in ['commandsea','denysea','safepassage'] if k!=key])
chain([('recognition','Признание наших границ','Recognition of our borders'),('neighbours','Соглашение с соседями','An agreement with neighbours'),('conference','Региональная конференция','A regional conference')],53,branch='is_subject = no',available='is_subject = no',effects={'recognition':'add_stability = 0.03','neighbours':'country_event = { id = aof_v03_regions.10 }','conference':'country_event = { id = aof_v03_regions.11 }'})
focus('neutral','Вооружённый нейтралитет','Armed neutrality',52,3,['conference'],effect='add_ideas = aof_v03_armed_neutrality',excludes=['aof_v03_g_defence'])
focus('defence','Взаимная оборона','Mutual defence',54,3,['conference'],effect='country_event = { id = aof_v03_regions.12 }',excludes=['aof_v03_g_neutral'])
chain([('mandate','Пределы внешнего мандата','The limits of the foreign mandate'),('localpowers','Полномочия местного кабинета','Powers of the local cabinet'),('guarantee','Пересмотреть гарантии покровителя','Review the patron guarantee')],57,branch='is_subject = yes',effects={'mandate':'add_political_power = 40','localpowers':'add_stability = 0.05','guarantee':'country_event = { id = aof_v03_regions.20 }'})

# Regional content lives in the same shared framework so it does not erase its economy.
def regional(prefix,tags,items,effects=None):
    gate='OR = { '+' '.join('tag = '+t for t in tags)+' }'
    previous=()
    for y,(key,ru,en) in enumerate(items):
        full=prefix+'_'+key
        focus(full,ru,en,62,y,previous,effect=(effects or {}).get(key,'add_political_power = 30'),branch=gate)
        previous=(full,)
regional('fin',['FIN'],[('karelia','Послевоенное устройство Карелии','The postwar settlement of Karelia'),('communities','Представительство местных общин','Representation for local communities'),('roads','Общие дороги и школы','Common roads and schools'),('border','Признанная граница','A recognised border')],{'communities':'country_event = { id = aof_v03_regions.30 }','roads':capital_building('infrastructure'),'border':'add_stability = 0.06'})
regional('man',['MAN'],[('rail','Местные кадры железных дорог','Local railway personnel'),('service','Собственная промышленная служба','Our own industrial service'),('garrison','Обсудить полномочия гарнизона','Discuss garrison powers'),('rights','Договорная самостоятельность','Negotiated self-government')],{'rail':bonus('industry'),'service':capital_building(),'garrison':'if = { limit = { JAP = { exists = yes } } JAP = { country_event = { id = aof_diplomacy.50 } } }','rights':'country_event = { id = aof_v03_regions.31 }'})
regional('fer',['FER'],[('port','Город и порт','City and port'),('trade','Торговый договор с Сибирью','Trade with Siberia'),('service','Служба собственной внешней торговли','Our own foreign trade service'),('guarantee','Пересмотр японской гарантии','Review the Japanese guarantee')],{'port':capital_building('infrastructure'),'trade':'if = { limit = { SIB = { exists = yes } } SIB = { country_event = { id = aof_diplomacy.80 } } }','service':'add_ideas = aof_v03_export_orders','guarantee':'if = { limit = { JAP = { exists = yes } } JAP = { country_event = { id = aof_diplomacy.40 } } }'})
regional('trk',['TRK'],[('congress','Новый съезд участников','A new congress of members'),('powers','Разделить полномочия','Divide responsibilities'),('union','Общая оборона при местном управлении','Common defence, local government'),('settlement','Сохранить союз или договориться о разделе','Preserve the union or negotiate separation')],{'powers':'country_event = { id = aof_v03_regions.32 }','union':'army_experience = 25 add_stability = 0.03','settlement':'country_event = { id = aof_v03_regions.33 }'})
regional('raj',['RAJ'],[('supply','Стабилизировать снабжение фронта','Stabilise front-line supply'),('cabinet','Гражданское правительство в военное время','Civilian government in wartime'),('terms','Проверить условия перемирия','Examine armistice terms'),('future','Будущее государства','The future of the state')],{'supply':'army_experience = 20 '+bonus('logistics_tech'),'cabinet':'country_event = { id = aof_v03_regions.34 }','terms':'if = { limit = { PAK = { exists = yes } has_war_with = PAK } PAK = { country_event = { id = aof_diplomacy.130 } } }','future':'add_stability = 0.07'})
regional('pak',['PAK'],[('aid','Согласовать помощь Ирана и Афганистана','Coordinate Iranian and Afghan aid'),('supply','Единые правила снабжения союзников','Common allied supply rules'),('peace','Самостоятельный мирный договор','An independent peace treaty'),('defence','Общий региональный оборонный блок','A regional defence arrangement')],{'aid':'if = { limit = { PER = { exists = yes } } PER = { country_event = { id = aof_diplomacy.140 } } } if = { limit = { AFG = { exists = yes } } AFG = { country_event = { id = aof_diplomacy.140 } } }','supply':bonus('logistics_tech'),'peace':'if = { limit = { RAJ = { exists = yes } has_war_with = RAJ } RAJ = { country_event = { id = aof_diplomacy.130 } } }','defence':'country_event = { id = aof_v03_regions.12 }'})
regional('can',['CAN'],[('obligations','Пересмотреть обязательства перед метрополией','Review obligations to the metropole'),('treaties','Собственные внешние договоры','Our own foreign agreements'),('ties','Океанские или североамериканские связи','Oceanic or North American ties'),('defence','Самостоятельная оборонная программа','An autonomous defence programme')],{'obligations':'country_event = { id = aof_v03_regions.35 }','treaties':'add_political_power = 60','ties':'country_event = { id = aof_v03_regions.36 }','defence':capital_building('arms_factory')})
regional('central',['GUA','HON','ELS','NIC','COS','PAN'],[('summit','Созвать соседние республики','Convene neighbouring republics'),('guarantees','Гарантии малым участникам','Guarantees for small participants'),('transit','Общий транзитный договор','A common transit agreement'),('defence','Оборонное сотрудничество','Defence cooperation'),('compact','Федеративный договор при взаимном согласии','A federal compact by mutual consent')],{'summit':'country_event = { id = aof_v03_regions.11 }','guarantees':'add_stability = 0.05','transit':capital_building('infrastructure'),'defence':'country_event = { id = aof_v03_regions.12 }','compact':'country_event = { id = aof_v03_regions.37 }'})
regional('chaco',['BOL','PAR'],[('commission','Пограничная комиссия по Чако','A Chaco boundary commission'),('supply','Подготовить снабжение спорного района','Prepare supply for the disputed district'),('mediation','Международное посредничество','International mediation'),('settlement','Закончить спор','Bring the dispute to an end')],{'commission':'country_event = { id = aof_v03_regions.38 }','supply':capital_building('infrastructure'),'mediation':'country_event = { id = aof_v03_regions.10 }','settlement':'add_stability = 0.05'})
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
    L[group+'_desc']=(ru+': политическая семья; форма государства и внешнеполитический курс определяются отдельно.',en+': a political family; state structure and foreign policy remain separate choices.')
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
def event(num,ru,en,desc_ru,desc_en,options):
    global events
    ident='aof_v03_regions.'+str(num)
    L[ident+'.t']=(ru,en);L[ident+'.d']=(desc_ru,desc_en)
    events+=f'country_event = {{ id = {ident} title = {ident}.t desc = {ident}.d is_triggered_only = yes\n'
    for i,(r,e,effect) in enumerate(options):
        key=ident+'.'+chr(97+i);L[key]=(r,e)
        events+=f'option = {{ name = {key} {effect} }}\n'
    events+='}\n'
members=['GUA','HON','ELS','NIC','COS']
pairflags=' '.join(f'if = {{ limit = {{ FROM = {{ tag = {tag} }} }} set_country_flag = aof_v03_cooperation_{tag} }} if = {{ limit = {{ tag = {tag} }} FROM = {{ set_country_flag = aof_v03_cooperation_{tag} }} }}' for tag in members)
pairgate='OR = { '+' '.join(f'AND = {{ FROM = {{ tag = {tag} }} has_country_flag = aof_v03_cooperation_{tag} }}' for tag in members)+' }'
event(1,'Инвестиционные переговоры','Investment negotiations','Выберем адресата. Он вправе отказать; тогда останется внутренний капитал.','Choose a partner. A refusal leaves domestic capital available.',[('США','The United States','if = { limit = { USA = { exists = yes } NOT = { has_war_with = USA } } USA = { country_event = { id = aof_v03_regions.2 } } }'),('Япония','Japan','if = { limit = { JAP = { exists = yes } NOT = { has_war_with = JAP } } JAP = { country_event = { id = aof_v03_regions.2 } } }'),('Собственные средства','Domestic funds','set_country_flag = aof_v03_investment_signed add_political_power = -50')])
event(2,'Предложение совместного предприятия','A joint-venture proposal','Партнёр предлагает ограниченную концессию. Согласие не меняет границы и власть.','A partner offers a limited concession. Agreement changes neither borders nor government.',[('Согласиться','Accept','FROM = { set_country_flag = aof_v03_investment_signed add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } } add_political_power = 25'),('Отказать','Decline','FROM = { country_event = { id = aof_v03_regions.3 } }')])
event(3,'Переговоры прерваны','Negotiations suspended','Внешнее предприятие не согласовано. Можно финансировать проект самим.','No foreign venture was agreed. We can finance the project ourselves.',[('Внутренний капитал','Domestic capital','set_country_flag = aof_v03_investment_signed add_political_power = -50')])
event(10,'Соглашение с соседом','An agreement with a neighbour','Предложим мирное сотрудничество соседу, с которым нет войны.','Offer peaceful cooperation to a neighbour with whom we are not at war.',[('Направить предложение','Send the proposal','random_neighbor_country = { limit = { NOT = { has_war_with = ROOT } } country_event = { id = aof_v03_regions.13 } }'),('Отложить','Postpone','add_political_power = 20')])
event(11,'Конференция суверенных стран','A conference of sovereign states','Соседи получают приглашение. Отказ не является поводом для войны.','Neighbours receive an invitation. Refusal is no cause for war.',[('Пригласить соседей','Invite our neighbours','every_neighbor_country = { limit = { NOT = { has_war_with = ROOT } } country_event = { id = aof_v03_regions.13 } }')])
event(12,'Взаимная оборона','Mutual defence','Отправим предложение независимому соседу. Он сохраняет право отказа.','Send an offer to an independent neighbour. They retain the right to refuse.',[('Предложить добровольный союз','Propose a voluntary alliance','random_neighbor_country = { limit = { is_subject = no NOT = { has_war_with = ROOT } } country_event = { id = aof_diplomacy.120 } }'),('Подготовить собственную оборону','Prepare our own defence','army_experience = 20')])
event(13,'Приглашение к сотрудничеству','An invitation to cooperate','Сосед предлагает соглашение равных участников. Обязательного вступления в союз нет.','Our neighbour offers cooperation among equals. No alliance membership is imposed.',[('Принять','Accept','add_stability = 0.02 add_opinion_modifier = { target = FROM modifier = aof_v03_cooperation } FROM = { add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } } '+pairflags),('Сохранить дистанцию','Keep our distance','add_political_power = 15')])
event(20,'Полномочия зависимого кабинета','The powers of a dependent cabinet','Покровитель должен сам ответить на требование расширить гражданские полномочия.','The patron must answer our request to expand civilian authority.',[('Направить требование','Send the request','overlord = { country_event = { id = aof_v03_regions.21 } }')])
event(21,'Требование местного кабинета','A local cabinet requests powers','Передать гражданские полномочия или сохранить нынешний мандат?','Devolve civilian powers or retain the current mandate?', [('Расширить полномочия','Devolve authority','FROM = { add_stability = 0.05 add_political_power = 75 set_country_flag = aof_v03_local_powers }'),('Сохранить мандат','Retain the mandate','FROM = { add_stability = -0.03 add_political_power = 25 }')])
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
event(38,'Предмет спора: Чако','The disputed Chaco','Комиссия собирает требования по Чако. Границы не меняются без договора; война не является автоматическим итогом.','The commission collects Chaco claims. Borders require agreement; war is not an automatic outcome.',[('Сначала комиссия','Commission first','add_political_power = 35'),('Подготовить военный вариант','Prepare a military contingency','army_experience = 25 add_stability = -0.03')])
event(39,'Условия нефтяного заказа','The terms of the oil order','Быстрый экспорт или подготовка собственной переработки?','Immediate exports or preparation for domestic refining?', [('Расширить экспортную концессию','Expand export concessions','add_ideas = aof_v03_export_orders add_political_power = 50'),('Обучить местных техников','Train local technicians',bonus('industry'))])
event(41,'Долгая конституция','A durable constitution','После подготовки гарантий парламент определяет общественный договор. Либеральный кабинет или консервативная преемственность сохраняют выборы.','After preparing safeguards, parliament settles the social compact. A liberal cabinet and conservative continuity both retain elections.',[('Либеральное правительство','A liberal government',government('democratic')+' add_stability = 0.05'),('Консервативный парламентский кабинет','A conservative parliamentary cabinet',government('aof_conservatism')+' add_stability = 0.05')])
event(42,'Возвращение гражданского мандата','Return of the civilian mandate','Чрезвычайные полномочия заканчиваются. Гражданское правительство будет отвечать перед избирателями.','Emergency powers end. Civilian government will answer to the electorate.',[('Консервативный гражданский кабинет','A conservative civilian cabinet',government('aof_conservatism')+' add_stability = 0.05'),('Либеральная конституция','A liberal constitution',government('democratic')+' add_stability = 0.03 add_political_power = 20')])
write('events/aof_v03_regions.txt',events)
write('common/opinion_modifiers/aof_v03_core.txt','opinion_modifiers = { aof_v03_cooperation = { value = 20 months = 24 } }\n')
L['aof_v03_cooperation']=('Договорное сотрудничество','Cooperation by agreement')
localize('aof_v03_core',L)
print(f'Core: {len(N)} shared focuses, {len(ideas)} ideas, {len(families)} ideology families, {sum(map(len,tech.values()))} research dates, {events.count("country_event = { id = aof_v03_regions.")} event/call entries; {len(L)} localisation keys/language')
