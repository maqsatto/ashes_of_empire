"""Reciprocal negotiations: proposals do not control another player's answer."""
from contentlib import write, localize, q

LOC={}; EVENTS=[]
COOP='add_opinion_modifier = { target = FROM modifier = aof_v03_cooperation } FROM = { add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } }'
PRESSURE='add_opinion_modifier = { target = FROM modifier = aof_v03_diplomatic_pressure } FROM = { add_opinion_modifier = { target = ROOT modifier = aof_v03_diplomatic_pressure } }'

def event(num,title,description,options,trigger=''):
    key=f'aof_diplomacy.{num}'
    LOC[key+'.t']=title; LOC[key+'.d']=description
    text=f'country_event = {{\n id = {key}\n title = {key}.t\n desc = {key}.d\n picture = GFX_aof_event_world_peace_1924\n is_triggered_only = yes\n'
    if trigger:text+=' trigger = { '+trigger+' }\n'
    for i,(label,effect,chance,condition) in enumerate(options):
        if num in (170,171,172) and i<2:
            flag='aof_cmt_procurement_closed' if num==171 else 'aof_cmt_protection_closed'
            current='USA = { exists = yes is_subject = no has_war = no } CMT = { exists = yes is_subject = no has_war = no NOT = { has_country_flag = '+flag+' } }'
            condition=current+' '+condition
            effect='if = { limit = { '+current+' } '+effect+' }'
        name=key+'.'+chr(97+i);LOC[name]=label
        text+=' option = { name = '+name
        if condition:text+=' trigger = { '+condition+' }'
        text+=' ai_chance = { factor = '+str(chance)+' } '+effect+' }\n'
    EVENTS.append(text+'}\n')

def notify(num):return 'FROM = { country_event = { id = aof_diplomacy.'+str(num)+' days = 1 } }'

def offer(num,receiver,sender,title,description,flag,yes='',conditional='',reject='',extra_trigger='',accept_condition=''):
    guard=f'tag = {receiver} FROM = {{ tag = {sender} exists = yes }} NOT = {{ has_war_with = FROM }} '+extra_trigger
    def outcome(suffix,fx,response):
        clear=('clr_country_flag = '+flag+'_refused ') if suffix=='accepted' else ''
        return (COOP if suffix!='refused' else PRESSURE)+' '+clear+'set_country_flag = '+flag+'_'+suffix+' FROM = { '+clear+'set_country_flag = '+flag+'_'+suffix+' '+fx+' } '+notify(response)
    event(num,title,description,[
      (('Принять договор с взаимными обязательствами.','Accept reciprocal commitments.'),outcome('accepted',yes,201)+' add_political_power = -25',50,accept_condition),
      (('Предложить ограниченный компромисс.','Offer a limited compromise.'),outcome('accepted',conditional or yes,202)+' add_political_power = -10',30,accept_condition),
      (('Отказать и сохранить самостоятельный курс.','Decline and retain our own course.'),outcome('refused',reject,203),20,'')],guard)

for number,title,desc in [
 (201,('Договор принят','Agreement accepted'),('Партнёр согласился на взаимные обязательства. Действуют показанные условия; независимость сторон сохраняется.','Our partner accepted reciprocal obligations. The stated terms now apply; both parties retain sovereignty.')),
 (202,('Найден ограниченный компромисс','A limited compromise'),('Партнёр предложил более узкое сотрудничество. Оно оставляет пространство для будущего пересмотра вместо обязательного конфликта.','Our partner offered narrower cooperation, leaving room for later revision rather than compulsory conflict.')),
 (203,('Предложение отклонено','Proposal declined'),('Партнёр отказался. Решение не даёт нам чужой территории или права распоряжаться его политикой. Можно продолжать внутреннюю программу либо искать других партнёров.','Our partner declined. This grants neither foreign territory nor control of its policy. Domestic development and other partners remain available.'))]:
    event(number,title,desc,[(('Принять ответ.','Acknowledge the answer.'),'set_country_flag = aof_diplomatic_answer_received',1,'')])

oil_title=('Пересмотр нефтяных обязательств','Revising oil obligations')
oil_desc=('Другая сторона предлагает пересмотреть сроки и компенсации нефтяного соглашения. Поддержка собственного курса не требует немедленной войны: можно принять переход, ограничить договор или отказаться.','The other party proposes revised oil terms and compensation. Accept a transition, narrow the agreement or decline; war is not automatic.')
for n,r,s in [(10,'USA','MEX'),(11,'MEX','USA')]:
    offer(n,r,s,oil_title,oil_desc,'aof_oil_compromise',
      'add_timed_idea = { idea = aof_v03_compensated_trade days = 730 } add_political_power = -35',
      'add_timed_idea = { idea = aof_v03_compensated_trade days = 365 } add_stability = 0.02',
      'add_stability = -0.02 set_country_flag = aof_oil_diversification_available')

for n,r,s,flag,idea in [(20,'USA','KAZ','aof_usa_partnership','aof_v03_american_tools'),(21,'KAZ','USA','aof_usa_partnership','aof_v03_american_tools'),(30,'JAP','KAZ','aof_jap_partnership','aof_v03_japanese_training'),(31,'KAZ','JAP','aof_jap_partnership','aof_v03_japanese_training')]:
    # Both directions apply the negotiated development benefit to Alash only.
    benefit=f'KAZ = {{ add_timed_idea = {{ idea = {idea} days = 730 }} set_country_flag = {flag}_accepted }}'
    offer(n,r,s,('Промышленное партнёрство с Алаш','An industrial partnership with Alash'),
      ('Станки и обучение ускорят развитие, но исключительный договор создаёт обязательства. Получатель сохраняет право отказа и возможность собственной программы.','Machine tools and training accelerate development, while exclusive terms create obligations. The recipient may decline and pursue domestic development.'),flag,
      'add_political_power = -40 '+benefit,
      'add_political_power = -20 '+benefit.replace('730','365'),
      f'KAZ = {{ set_country_flag = {flag}_refused add_political_power = 15 }}',
      accept_condition='KAZ = { NOT = { has_completed_focus = aof_v03_kaz_diverse1 } NOT = { has_country_flag = '+('aof_jap_partnership_accepted' if n in (20,21) else 'aof_usa_partnership_accepted')+' } }')

for n,r,s,flag in [(40,'JAP','FER','aof_far_east_revision'),(41,'FER','JAP','aof_far_east_revision'),(50,'JAP','MAN','aof_manchurian_revision'),(51,'MAN','JAP','aof_manchurian_revision')]:
    target='FER' if n in (40,41) else 'MAN'
    autonomy=f'JAP = {{ if = {{ limit = {{ {target} = {{ is_subject_of = JAP }} }} set_autonomy = {{ target = {target} autonomy_state = autonomy_free end_wars = no end_civil_wars = no }} }} }} {target} = {{ set_country_flag = {flag}_accepted add_stability = 0.04 }}'
    restricted=f'{target} = {{ set_country_flag = {flag}_accepted add_timed_idea = {{ idea = aof_v03_limited_autonomy days = 730 }} }}'
    offer(n,r,s,('Пересмотр полномочий зависимого правительства','Revising a dependent government’s powers'),
      ('Правительство просит больше самостоятельности. Можно признать независимость под договорными гарантиями, сохранить защиту с местными правами или отказать. Изменение Маньчжурии не меняет автоматически статус Владивостока.','The government seeks greater autonomy. Recognise independence under treaty guarantees, retain protection with local powers or refuse. Manchuria and Vladivostok remain separate questions.'),flag,autonomy,restricted,
      f'{target} = {{ set_country_flag = {flag}_refused add_political_power = 25 }}')

for n,r,s in [(60,'USA','JAP'),(61,'JAP','USA')]:
    offer(n,r,s,('Тихоокеанская разрядка','Pacific de-escalation'),('Предлагается сотрудничество по морской безопасности без передачи островов, баз или права командовать чужим флотом.','A maritime security agreement is proposed, without transferring islands, bases or command of another navy.'),'aof_pacific_detente',
      'add_stability = 0.03 JAP = { add_stability = 0.03 } USA = { add_stability = 0.03 }','add_political_power = 20','add_war_support = 0.02')

for n,r,s in [(70,'CAU','KAZ'),(71,'KAZ','CAU')]:
    offer(n,r,s,('Каспийская конвенция','The Caspian convention'),('Условия морского коридора требуют согласия обеих сторон. Обычный транзит, оборонные гарантии и отказ дают разные последствия. Соглашение само не создаёт морской путь на карте.','A maritime corridor needs both parties’ consent. Transit, defence guarantees and refusal have different consequences. An agreement cannot itself create a navigable map route.'),'aof_caspian_agreement',
      'KAZ = { set_country_flag = aof_caspian_agreement_accepted add_timed_idea = { idea = aof_v03_transit_guarantees days = 1095 } } CAU = { add_political_power = 40 }',
      'KAZ = { set_country_flag = aof_caspian_agreement_accepted add_political_power = -35 } CAU = { add_stability = 0.03 }',
      'KAZ = { set_country_flag = aof_caspian_agreement_refused set_country_flag = aof_siberian_land_route }',
      'has_global_flag = aof_caspian_navigation_verified')

event(72,('Конвенция перед испытанием войной','War tests the convention'),
 ('Алаш, уже участвующий в войне, просит подтвердить проход через кавказский канал. Договор не обязывает Кавказ вступать в войну. Можно сохранить проход, потребовать оплату охраны или закрыть маршрут для этой воюющей стороны. Закрытие касается и её конвоев; сухопутная программа остаётся доступной.',
  'Alash, now a belligerent, asks us to confirm canal passage. The convention does not require Caucasus to enter the war. Maintain access, charge for protection, or close the route to this belligerent. Closure also affects its convoys; overland development remains available.'),[
 (('Соблюдать конвенцию, сохраняя нейтралитет.','Honour the convention and remain neutral.'),'clr_global_flag = aof_caucasian_canal_closed FROM = { clr_country_flag = aof_caucasian_canal_blocked_for_country set_country_flag = aof_caspian_wartime_access } add_political_power = -20 '+COOP+' '+notify(201),50,''),
 (('Пропускать при оплате охраны маршрута.','Maintain passage with a protection fee.'),'clr_global_flag = aof_caucasian_canal_closed add_political_power = 35 FROM = { add_political_power = -35 clr_country_flag = aof_caucasian_canal_blocked_for_country set_country_flag = aof_caspian_wartime_access } '+notify(202),30,''),
 (('Закрыть проход для воюющей стороны.','Close passage to the belligerent.'),'FROM = { set_country_flag = aof_caucasian_canal_blocked_for_country set_country_flag = aof_caspian_agreement_refused set_country_flag = aof_caspian_overland_fallback } '+PRESSURE+' '+notify(203),20,'')],
 'tag = CAU FROM = { tag = KAZ has_war = yes has_country_flag = aof_caspian_agreement_accepted } has_global_flag = aof_caspian_navigation_verified NOT = { has_war_with = FROM }')

for n,r,s in [(80,'SIB','FER'),(81,'FER','SIB')]:
    offer(n,r,s,('Сибирский выход к портам','Siberian access to ports'),('Сухопутный коридор и открытый порт могут связать соседей без объединения государств. Японская зависимость порта остаётся отдельным вопросом.','An overland corridor and open port can connect neighbours without unifying them. Japanese protection remains a separate issue.'),'aof_siberian_corridor',
      'SIB = { add_timed_idea = { idea = aof_v03_compensated_trade days = 730 } } FER = { add_political_power = 35 }',
      'SIB = { add_stability = 0.03 } FER = { add_stability = 0.02 }','set_country_flag = aof_alternative_trade_route')

event(90,('Условия южноамериканской конференции','Terms of a South American conference'),
 ('Инициатор предлагает общий договор. Можно вступить на равных, требовать пересмотра условий или остаться вне проекта. Отказ не объявляет войну.','The initiator proposes a common compact. Join as an equal, seek revised terms or remain outside. Refusal does not declare war.'),[
 (('Присоединиться как равноправный участник.','Join as an equal participant.'),COOP+' set_country_flag = aof_conference_participant if = { limit = { FROM = { tag = BRA } } set_country_flag = aof_conference_participant_bra } else = { set_country_flag = aof_conference_participant_arg } FROM = { set_country_flag = aof_conference_accepted add_political_power = 30 } '+notify(201),50,'NOT = { FROM = { has_country_flag = aof_brazil_hegemonic_conference } }'),
 (('Требовать равноправного пересмотра.','Demand equal terms.'),'set_country_flag = aof_conference_counteroffer_pending FROM = { country_event = { id = aof_diplomacy.91 days = 1 } }',35,''),
 (('Не признавать чужого первенства.','Decline another state’s primacy.'),PRESSURE+' set_country_flag = aof_conference_refused '+notify(203),25,'')],
 'FROM = { exists = yes OR = { tag = BRA tag = ARG } } NOT = { has_war_with = FROM } is_subject = no')

event(100,('Возврат научной школы','A scientific school returns'),
 ('Восстановленный европейский институт приглашает специалиста домой. Его ученики уже работают у нас. Сохранить исключительное преимущество, создать совместную кафедру или поддержать передачу опыта?','A restored European institute invites a scholar home. Local students are already working here. Preserve exclusivity, establish a joint department or support transfer of expertise?'),[
 (('Удержать специалиста новым заказом.','Retain the scholar with a new commission.'),'add_political_power = -60 add_timed_idea = { idea = aof_v03_research_commission days = 730 } '+notify(203),35,''),
 (('Создать совместный институт.','Establish a joint institute.'),COOP+' add_political_power = -30 add_tech_bonus = { name = aof_v03_joint_institute bonus = 0.5 uses = 1 category = industry } FROM = { add_tech_bonus = { name = aof_v03_joint_institute bonus = 0.5 uses = 1 category = industry } } '+notify(201),45,''),
 (('Передать руководство подготовленным ученикам.','Appoint the trained successors.'),'add_stability = 0.03 FROM = { add_timed_idea = { idea = aof_v03_research_commission days = 365 } } '+notify(202),20,'')],
 'OR = { tag = USA tag = JAP } FROM = { exists = yes } NOT = { has_war_with = FROM }')

offer(110,'USA','CMT',('Конец военного устава','The end of the wartime charter'),
 ('Коммерческое государство просит поддержки нового гражданского соглашения. Это предложение будущего партнёрства, а не утверждение, что США были его прежним покровителем.','The commercial state seeks support for a civil settlement. This is a prospective partnership, not an assertion that America was its original patron.'),'aof_charter_settlement',
 'CMT = { set_country_flag = aof_charter_reformed add_stability = 0.06 remove_ideas = aof_v03_cmt_initial }',
 'CMT = { add_timed_idea = { idea = aof_v03_compensated_trade days = 730 } add_stability = 0.02 }',
 'CMT = { set_country_flag = aof_charter_domestic_alternative add_political_power = 30 }')

event(120,('Предложение о взаимной обороне','An offer of mutual defence'),
 ('Инициатор предлагает добровольный оборонный союз. Принятие создаёт общий блок, но не передаёт территории или власть. Отказ сохраняет независимость и оставляет торговое сотрудничество возможным.','The sender proposes a voluntary defensive alliance. Acceptance creates a common faction without transferring land or sovereignty. Refusal leaves trade cooperation possible.'),[
 (('Принять взаимные оборонные обязательства.','Accept mutual defence.'),COOP+' FROM = { if = { limit = { is_in_faction = no } set_rule = { can_create_factions = yes } if = { limit = { has_dlc = "No Compromise, No Surrender" } create_faction_from_template = { template = aof_v03_defensive_compact name = aof_v03_mutual_defence icon = GFX_faction_logo_generic } } else = { create_faction = aof_v03_mutual_defence } } add_to_faction = ROOT } if = { limit = { is_in_faction_with = FROM } set_country_flag = aof_alliance_accepted clr_country_flag = aof_alliance_refused FROM = { set_country_flag = aof_alliance_accepted clr_country_flag = aof_alliance_refused } '+notify(201)+' } else = { '+notify(203)+' }',40,'is_subject = no is_in_faction = no FROM = { is_subject = no OR = { is_in_faction = no is_faction_leader = yes } }'),
 (('Только торговля и ненападение.','Trade and non-aggression only.'),COOP+' diplomatic_relation = { country = FROM relation = non_aggression_pact active = yes } set_country_flag = aof_alliance_limited FROM = { set_country_flag = aof_alliance_limited } add_stability = 0.02 '+notify(202),35,''),
 (('Сохранить самостоятельную оборону.','Retain independent defence.'),'set_country_flag = aof_alliance_refused FROM = { set_country_flag = aof_alliance_refused } '+notify(203),25,'')],
 'FROM = { exists = yes } NOT = { has_war_with = FROM }')

event(130,('Условия перемирия','Terms of an armistice'),
 ('Другая сторона предлагает прекратить текущую войну без обязательного поглощения. Перемирие сохраняет государства и открывает послевоенный курс. Можно предпочесть продолжение войны.','The other side proposes ending the current war without compulsory absorption. Peace preserves both states and opens postwar development. Continuing the war remains a choice.'),[
 (('Прекратить огонь и заключить мир.','Cease fire and conclude peace.'),'white_peace = FROM set_country_flag = aof_armistice_signed FROM = { set_country_flag = aof_armistice_signed } add_stability = 0.04 '+notify(201),65,''),
 (('Продолжать войну.','Continue the war.'),'add_war_support = 0.03 '+notify(203),35,'')],
 'OR = { tag = RAJ tag = PAK } FROM = { OR = { tag = RAJ tag = PAK } } has_war_with = FROM')

event(140,('Запрос помощи Пакистану','Pakistan requests assistance'),
 ('Пакистан просит ограниченную партию вооружения. Поставка не делает нас участником войны; прямое вмешательство не утверждено исходной историей.','Pakistan requests a limited arms shipment. Sending aid does not make us a belligerent; direct intervention is not established by the starting history.'),[
 (('Отправить оружие и инструкторов.','Send arms and instructors.'),'add_political_power = -35 FROM = { add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 500 producer = ROOT } set_country_flag = aof_pak_support_received } '+COOP+' '+notify(201),65,''),
 (('Ограничиться дипломатической поддержкой.','Provide diplomatic support only.'),COOP+' FROM = { add_political_power = 25 } '+notify(202),25,''),
 (('Отказать в новой поставке.','Decline another shipment.'),notify(203),10,'')],
 'OR = { tag = PER tag = AFG } FROM = { tag = PAK exists = yes }')

offer(150,'CHI','JAP',('Китайское соглашение без подчинения','A Chinese agreement without subordination'),
 ('Япония предлагает договор вместо прямого доминирования. Китай сохраняет правительство и территории; условия требуют собственного согласия.','Japan proposes an agreement rather than direct domination. China retains government and territory, and must consent to the terms.'),'aof_sino_japanese_agreement',
 'JAP = { remove_ideas = aof_v03_jap_garrison add_stability = 0.04 } CHI = { add_stability = 0.04 }',
 'JAP = { add_political_power = 35 } CHI = { add_political_power = 35 }',
 'JAP = { set_country_flag = aof_chinese_negotiations_failed }')

from diplomacy_extensions import register
register(event,offer,notify,LOC,COOP,PRESSURE)
event(183,('Договор о взаимном невмешательстве','A mutual non-interference treaty'),
 ('Алаш предлагает признать самостоятельность сторон и отказаться от нападения. Это договор, а не вступление в общий военный блок. Согласие сохраняет разные общественные системы; отказ не даёт нам чужих земель.',
  'Alash proposes recognition of mutual independence and non-aggression. This is a treaty, not entry into a common military bloc. Agreement preserves different social systems; rejection grants no foreign territory.'),[
 (('Подписать договор о ненападении.','Sign the non-aggression pact.'),'diplomatic_relation = { country = FROM relation = non_aggression_pact active = yes } set_country_flag = aof_kaz_sov_noninterference_accepted FROM = { set_country_flag = aof_kaz_sov_noninterference_accepted } '+COOP+' '+notify(201),65,''),
 (('Не связывать кабинет новым договором.','Decline to bind the cabinet to a new treaty.'),'set_country_flag = aof_kaz_sov_noninterference_refused FROM = { set_country_flag = aof_kaz_sov_noninterference_refused } '+notify(203),35,'')],
 'tag = SOV FROM = { tag = KAZ exists = yes } NOT = { has_war_with = FROM }')
write('events/aof_v03_diplomacy.txt','add_namespace = aof_diplomacy\n'+''.join(EVENTS))
write('common/opinion_modifiers/aof_v03_diplomacy.txt','opinion_modifiers = { aof_v03_diplomatic_pressure = { value = -25 months = 24 } }\n')
write('common/factions/templates/aof_v03_compact.txt','''aof_v03_defensive_compact = {
 name = aof_v03_mutual_defence
 manifest = faction_manifest_strength_in_unity
 icon = GFX_faction_logo_generic
 can_leader_join_other_factions = yes
 visible = { always = yes }
 available = { always = yes }
 goals = { faction_goal_a_military_base }
 default_rules = { joining_rule_has_no_offensive_war }
}
''')
ideas={
 'aof_v03_american_tools':(('Американские станки и условия концессии','American tools and concession terms'),'industrial_capacity_factory = 0.06 research_speed_factor = 0.03 consumer_goods_factor = 0.04'),
 'aof_v03_japanese_training':(('Японская техническая миссия','Japanese technical mission'),'research_speed_factor = 0.04 production_factory_efficiency_gain_factor = 0.05 political_power_gain = -0.05'),
 'aof_v03_compensated_trade':(('Согласованный переходный договор','An agreed transition contract'),'industrial_capacity_factory = 0.04 consumer_goods_factor = 0.02'),
 'aof_v03_limited_autonomy':(('Местные полномочия под внешней защитой','Local powers under external protection'),'stability_factor = 0.05 political_power_gain = 0.08'),
 'aof_v03_transit_guarantees':(('Гарантии морского транзита','Maritime transit guarantees'),'stability_factor = 0.04 production_factory_efficiency_gain_factor = 0.04'),
 'aof_v03_research_commission':(('Заказ исследовательскому институту','Research institute commission'),'research_speed_factor = 0.04 consumer_goods_factor = 0.01')}
it='ideas = { country = {\n'
PICTURES = {
 'aof_v03_american_tools': 'generic_production_bonus',
 'aof_v03_japanese_training': 'generic_flexible_foreign_policy',
 'aof_v03_compensated_trade': 'generic_production_bonus',
 'aof_v03_limited_autonomy': 'generic_local_self_management',
 'aof_v03_transit_guarantees': 'generic_flexible_foreign_policy',
 'aof_v03_research_commission': 'generic_production_bonus',
}
for key,(names,mods) in ideas.items():
    LOC[key]=names; LOC[key+'_desc']=(names[0]+'. Временные преимущества сопровождаются обязательствами.',names[1]+'. Temporary benefits come with obligations.')
    it+=f' {key} = {{ picture = {PICTURES[key]} allowed = {{ always = no }} removal_cost = -1 modifier = {{ {mods} }} }}\n'
write('common/ideas/aof_v03_diplomacy.txt',it+'} }\n')
LOC['aof_v03_joint_institute']=('Совместный институт','Joint institute')
LOC['aof_v03_mutual_defence']=('Договор взаимной обороны','Mutual defence compact')
LOC['aof_v03_diplomacy_category']=('Переговоры о новом мире','Negotiating the new peace')
LOC['aof_v03_diplomacy_category_desc']=('Предложения требуют ответа получателя. Отказ не отменяет самостоятельность другой страны и не объявляет войну автоматически.','Proposals require a recipient’s response. Refusal neither removes sovereignty nor automatically declares war.')
write('common/decisions/categories/aof_v03_categories.txt','''aof_v03_diplomacy_category = { icon = generic_political_actions visible = { is_ai = no } }
aof_v03_canal_policy = { icon = generic_political_actions allowed = { tag = CAU } visible = { tag = CAU } }
aof_v03_federation_category = { icon = generic_political_actions allowed = { OR = { tag = CHI tag = SIB tag = SOV } } visible = { OR = { tag = CHI tag = SIB tag = SOV } } }
''')
ds='aof_v03_diplomacy_category = {\n'
actions=[('KAZ','USA',20,'Станки из США','American machine tools'),('KAZ','JAP',30,'Японская техническая миссия','Japanese technical mission'),('KAZ','CAU',70,'Предложить Каспийскую конвенцию','Propose the Caspian convention'),('KAZ','SIB',120,'Предложить договор Сибири','Offer a Siberian defence compact'),('FER','JAP',40,'Пересмотреть японскую гарантию','Revise Japanese protection'),('FER','SIB',80,'Открыть сибирскую торговлю','Open Siberian trade'),('MAN','JAP',50,'Обсудить права гарнизона','Discuss garrison powers'),('MEX','USA',10,'Пересмотр нефтяного договора','Revise the oil agreement'),('CMT','USA',110,'Добиться нового гражданского договора','Seek a new civil compact'),('JAP','USA',60,'Переговоры о Тихом океане','Negotiate Pacific security'),('RAJ','PAK',130,'Предложить Пакистану перемирие','Offer Pakistan an armistice'),('PAK','RAJ',130,'Предложить Индии перемирие','Offer India an armistice'),('PAK','PER',140,'Запросить иранскую помощь','Request Iranian assistance'),('PAK','AFG',140,'Запросить афганскую помощь','Request Afghan assistance')]
actions.append(('KAZ','CAU',72,'Подтвердить проход во время войны','Confirm wartime passage'))
for sender,target,n,ru,en in actions:
    key=f'aof_v03_offer_{sender.lower()}_{target.lower()}'+('_wartime' if n==72 else '');LOC[key]=(ru,en)
    LOC[key+'_desc']=('Дипломатическая инициатива стоит политической власти; результат зависит от ответа получателя.','This initiative costs political power; the outcome depends on the recipient’s answer.')
    condition='has_war_with = '+target if n==130 else 'NOT = { has_war_with = '+target+' }'
    if n==70:condition+=' has_global_flag = aof_caspian_navigation_verified'
    if n==72:condition+=' has_war = yes has_country_flag = aof_caspian_agreement_accepted has_global_flag = aof_caspian_navigation_verified'
    if sender=='KAZ' and n in (20,30):
        condition+=' NOT = { has_country_flag = '+('aof_jap_partnership_accepted' if n==20 else 'aof_usa_partnership_accepted')+' }'
    ds+=f''' {key} = {{ icon = generic_political_discourse cost = 35 days_re_enable = 365
 visible = {{ tag = {sender} country_exists = {target} }}
 available = {{ {condition} }}
 complete_effect = {{ {target} = {{ country_event = {{ id = aof_diplomacy.{n} days = 2 }} }} }}
 ai_will_do = {{ factor = 0 }}
 }}\n'''
from build_v03_caspian import ROUTE
corridor=' '.join('owns_state = '+str(s) for s in sorted(set(ROUTE.values())))+' '+' '.join('controls_province = '+str(p) for p in ROUTE)
LOC['aof_v03_canal_policy']=('Правила Кавказского канала','Caucasian canal policy')
LOC['aof_v03_reopen_canal']=('Возобновить общее судоходство','Resume general navigation')
LOC['aof_v03_reopen_canal_desc']=('После чрезвычайного закрытия восстановить проход для разрешённых стран. Запрет отдельному участнику конвенции и обычные правила военного доступа продолжают действовать.','After an emergency closure, restore passage for permitted countries. Restrictions on individual treaty partners and ordinary wartime access rules remain in force.')
LOC['aof_v03_restore_kaz_passage']=('Восстановить проход для Алаш','Restore Alash passage')
LOC['aof_v03_restore_kaz_passage_desc']=('После окончания войны Алаш вернуть предусмотренный конвенцией проход его кораблям и торговым конвоям. Общее чрезвычайное закрытие канала отменяется отдельным решением.','After Alash concludes its war, restore convention passage for its ships and trade convoys. General emergency closure is lifted separately.')
policy='aof_v03_canal_policy = {\n'
for ident,cost,status,guard,effect in [
 ('aof_v03_reopen_canal',25,'has_global_flag = aof_caucasian_canal_closed','has_war = no','clr_global_flag = aof_caucasian_canal_closed'),
 ('aof_v03_restore_kaz_passage',20,'KAZ = { exists = yes has_country_flag = aof_caucasian_canal_blocked_for_country }','has_war = no KAZ = { has_war = no }','KAZ = { clr_country_flag = aof_caucasian_canal_blocked_for_country set_country_flag = aof_caspian_agreement_accepted clr_country_flag = aof_caspian_agreement_refused clr_country_flag = aof_caspian_overland_fallback }')]:
    condition='tag = CAU has_global_flag = aof_caspian_navigation_verified '+corridor+' '+guard+' '+status
    policy+=f''' {ident} = {{ icon = generic_political_discourse cost = {cost} days_re_enable = 30
 allowed = {{ tag = CAU }} visible = {{ tag = CAU {status} }}
 available = {{ {condition} }}
 complete_effect = {{ if = {{ limit = {{ {condition} }} {effect} }} }}
 ai_will_do = {{ factor = 1 }} }}
'''
LOC['aof_v03_federation_category']=('Договоры об общих учреждениях','Treaties on common institutions')
unions='aof_v03_federation_category = {\n'
for sender,route,targets in [
 ('CHI','agreement4',['SHX','YUN','GXC','XSM','SIK','PRC']),
 ('SIB','russia4',['SOV','FER']),('SOV','treaty4',['SIB','KAZ','FER'])]:
    for target in targets:
        key='aof_v03_union_'+sender.lower()+'_'+target.lower()
        LOC[key]=('Предложить федерацию: ['+target+'.GetName]','Propose federation: ['+target+'.GetName]')
        LOC[key+'_desc']=('Партнёр по союзу самостоятельно решит, объединять ли территории и учреждения. Ограниченный договор и отказ сохраняют отдельное государство. Повторные переговоры возможны после изменения обстоятельств.','Our ally independently decides whether to unify territory and institutions. A limited agreement and refusal preserve its separate country. Renewed negotiations are possible after circumstances change.')
        ready='is_subject = no has_war = no NOT = { any_owned_state = { NOT = { is_controlled_by = PREV } } }'
        gate=f'tag = {sender} has_completed_focus = aof_v03_{sender.lower()}_{route} '+ready+f' {target} = {{ exists = yes {ready} is_in_faction_with = ROOT }}'
        unions+=f''' {key} = {{ icon = generic_political_discourse cost = 75 days_re_enable = 365
 allowed = {{ tag = {sender} }} visible = {{ tag = {sender} country_exists = {target} has_completed_focus = aof_v03_{sender.lower()}_{route} }}
 available = {{ {gate} }}
 complete_effect = {{ if = {{ limit = {{ {gate} }} {target} = {{ country_event = {{ id = aof_diplomacy.160 days = 2 }} }} }} }}
 ai_will_do = {{ factor = 0.05 }} }}
'''
write('common/decisions/aof_v03_diplomacy.txt',ds+'}\n'+policy+'}\n'+unions+'}\n')
localize('aof_v03_diplomacy',LOC)
print(f'Diplomacy: {len(EVENTS)} reciprocal events, {len(actions)} player initiatives, {len(ideas)} ideas.')
