"""Deterministic DesignBook v0.3 national campaign authoring."""
from contentlib import write, localize, render_tree, capital_building
from ideaicons import idea_picture
from focus_flavour import national_descriptions
LOC={}; IDEAS={}; EVENTS=[]; EVENT_INDEX={}; COUNTS={}
CIV=capital_building(); MIL=capital_building('arms_factory'); INF=capital_building('infrastructure')
TECH='add_tech_bonus = { name = aof_v03_practical_school bonus = 0.5 uses = 1 category = industry }'
LOC['aof_v03_practical_school']=('Прикладная школа','Practical school')
def idea(key,ru,en,mods):
    IDEAS[key]=mods; LOC[key]=(ru,en);LOC[key+'_desc']=(ru+' — преимущества и ограничения выбранного курса.',en+' — strengths and limits of the chosen course.')
    return 'add_ideas = '+key
FAMILIES=['democratic','neutrality','communism','fascism','aof_social_democracy','aof_conservatism']
POL={p:'set_popularities = { '+' '.join(f+' = '+str(70 if f==p else 6) for f in FAMILIES)+' } set_politics = { ruling_party = '+p+' elections_allowed = '+('yes' if p in ['democratic','aof_social_democracy','aof_conservatism'] else 'no')+' }' for p in FAMILIES}
def call(tag,n):
    return f'if = {{ limit = {{ country_exists = {tag} NOT = {{ has_war_with = {tag} }} }} {tag} = {{ country_event = {{ id = aof_diplomacy.{n} days = 2 }} }} }}'
def event(number,ru,en,dr,de,options):
    assert number not in EVENT_INDEX or number in {10,30,40,70}, f'Duplicate national event ID: {number}'
    ident='aof_nations.'+str(number);LOC[ident+'.t']=(ru,en);LOC[ident+'.d']=(dr,de)
    s=f'country_event = {{ id = {ident} title = {ident}.t desc = {ident}.d picture = GFX_aof_event_kazakhstan_development is_triggered_only = yes\n'
    for i,option in enumerate(options):
        r,e,fx=option[:3];condition=' trigger = { '+option[3]+' }' if len(option)>3 else ''
        key=ident+'.'+chr(97+i);LOC[key]=(r,e);s+=' option = { name = '+key+condition+' ai_chance = { factor = 1 } '+fx+' }\n'
    if number in EVENT_INDEX:EVENTS[EVENT_INDEX[number]]=s+'}\n'
    else:EVENT_INDEX[number]=len(EVENTS);EVENTS.append(s+'}\n')
    return 'country_event = { id = '+ident+' days = 1 }'
class Tree:
    def __init__(self,tag,ru,en,mods):
        self.tag=tag;self.nodes=[];self.prefix='aof_v03_'+tag.lower()+'_'
        idea(self.prefix+'initial',ru,en,mods)
    def node(self,key,ru,en,x,y,pre=None,fx='add_political_power = 30',**kw):
        d=dict(id=self.prefix+key,ru=ru,en=en,x=x,y=y,pre=[self.prefix+p for p in (pre or [])],effect=fx,
          desc_ru=ru+'. Решение определяет будущий курс страны. Последствия и условия показаны ниже.',
          desc_en=en+'. This decision determines the country’s future course. Conditions and consequences are shown below.')
        d.update(kw);self.nodes.append(d);return key
    def chain(self,stem,names,x,y,pre,fxs=None):
        effects=fxs or ['add_political_power = 30'];prev=pre
        for i,pair in enumerate(names):
            key=stem+str(i+1);self.node(key,*pair,x,y+i,[prev] if prev else [],effects[i%len(effects)]);prev=key
        return prev
    def routes(self,routes,start,y=3):
        roots=[]
        for j,(stem,names,pol,mods) in enumerate(routes):
            roots.append(stem+'1')
            reward=idea(self.prefix+stem+'_settlement',names[-1][0],names[-1][1],mods)
            fxs=[POL[pol]+' add_stability = -0.03','add_stability = 0.04',INF,'add_political_power = 50','add_stability = 0.03']
            self.chain(stem,names,3+j*6,y,start,fxs)
            self.nodes[-1]['effect']+=' '+reward
        for n in self.nodes:
            if n['id'][len(self.prefix):] in roots:n['excludes']=[self.prefix+r for r in roots if self.prefix+r!=n['id']]
    def opening(self,names):
        return self.chain('entry',names,0,0,None,['add_political_power = 40',INF,'remove_ideas = '+self.prefix+'initial add_stability = 0.04'])
    def save(self):
        text,loc=render_tree(self.prefix+'tree',[self.tag],self.nodes);LOC.update(loc)
        write('common/national_focus/aof_v03_'+self.tag.lower()+'.txt',text);COUNTS[self.tag]=len(self.nodes)
    def find(self,key):return next(n for n in self.nodes if n['id']==self.prefix+key)

k=Tree('KAZ','Независимость без прежних связей','Independence without old connections','industrial_capacity_factory = -0.06')
idea('aof_v03_kaz_local_compacts','Местные договорённости вместо общей службы','Local compacts instead of a common service','political_power_gain = -0.1')
idea('aof_v03_kaz_resource_gap','Недра ещё не стали производством','Deposits have not yet become production','industrial_capacity_factory = -0.06 research_speed_factor = -0.04')
LOC['aof_v03_kaz_local_compacts_desc']=('Общая гражданская служба ещё уступает местным договорённостям. Ежедневная работа республики завершает этот переходный этап.','The common civil service still gives way to local arrangements. Making the republic work every day completes this transitional stage.')
LOC['aof_v03_kaz_resource_gap_desc']=('Знание о недрах не заменяет дороги, переработку и собственный инструмент. Полная цепочка машиностроения снимает этот переходный недостаток.','Knowledge of deposits does not replace roads, processing and domestic tools. A complete machine-building chain removes this transitional weakness.')
a=k.opening([('Созвать общий съезд','Convene the common congress'),('Связать центры республики','Connect the republican centres'),('Общая казна вместо чрезвычайных сборов','A common treasury instead of emergency levies')])
a=k.chain('service',[('Служба гражданской администрации','A civil administration'),('Школа для нового поколения','A school for the next generation'),('Республика должна работать ежедневно','The republic must work every day')],0,3,a,['add_political_power = 50',TECH,'add_stability = 0.05'])
k.routes([
 ('constitution',[('Конституция, признанная на местах','A constitution recognised locally'),('Права гражданина важнее покровителя','Citizenship before patronage'),('Выборное местное управление','Elected local government'),('Суд между властью и собственностью','Courts between power and property'),('Республика разных общин','A republic of many communities')],'democratic','stability_factor = 0.12 political_power_gain = 0.1 mobilization_speed = -0.1'),
 ('land',[('Земельный компромисс','A land compromise'),('Сельские кооперативы','Rural cooperatives'),('Учитель раньше чиновника','Teachers before officials'),('Общественный заказ на переработку','Public orders for processing'),('Социальная республика','A social republic')],'democratic','research_speed_factor = 0.05 consumer_goods_factor = -0.04 industrial_capacity_factory = -0.03'),
 ('mandate',[('Единое командование','Unified command'),('Охранять узлы, а не каждый километр','Guard junctions rather than every mile'),('Чрезвычайный промышленный заказ','An emergency industrial order'),('Армия гарантирует государство','The army guarantees the state')],'neutrality','army_org_factor = 0.08 industrial_capacity_factory = 0.04 stability_factor = -0.08')],a,6)
k.node('return_mandate','Вернуть мандат съезду','Return the mandate to congress',15,10,['mandate4'],POL['democratic']+' remove_ideas = aof_v03_kaz_mandate_settlement add_stability = 0.1',excludes=[k.prefix+'directory'])
k.node('directory','Постоянная директория','A permanent directorate',18,10,['mandate4'],'add_war_support = 0.1 add_stability = -0.03',excludes=[k.prefix+'return_mandate'])
k.find('constitution5')['effect']+=' '+event(1,'Одна служба или договор областей?','One service or a compact of regions?','Съезд согласен сохранить республику. Спор идёт о полномочиях: единая служба быстрее проводит реформы, местные гарантии укрепляют доверие.','Congress agrees to preserve the republic. A uniform service accelerates reform; regional guarantees strengthen trust.',[('Единая служба с общими судами','A common service under common courts','add_political_power = 70 add_stability = -0.02'),('Закрепить областные гарантии','Entrench regional guarantees','add_stability = 0.08 add_political_power = -30')])
end=k.chain('industry',[('Собрать геологические материалы','Collect the geological records'),('Первая общая экспедиционная программа','The first common survey programme'),('Дороги к подтверждённым месторождениям','Roads to proven deposits'),('Переработка рядом с добычей','Processing beside extraction'),('Инструментальная мастерская','A toolmaking workshop'),('Собственное машиностроение','Domestic machine building')],-5,3,'entry1',[TECH,'add_political_power = -25 add_stability = 0.02',INF,CIV,MIL,TECH])
roots=[]
for x,stem,names,fxs in [(-12,'american',[('Заказ на станки','Order machine tools'),('Условия концессии','Concession terms'),('Инженерные места для граждан Алаш','Engineering places for Alash citizens'),('Пересмотр первоначального договора','Revise the original contract')],[call('USA',20),'add_political_power = 30',TECH,'add_stability = 0.04']),(-9,'japanese',[('Техническая миссия','A technical mission'),('Совместные ремонтные предприятия','Joint repair works'),('Лицензия вместе с обучением','Licences with training'),('Собственная серия деталей','A domestic series of parts')],[call('JAP',30),CIV,TECH,MIL]),(-6,'diverse',[('Разделить большие заказы','Divide the major orders'),('Пригласить независимые коллективы','Invite independent teams'),('Институт прикладных работ','An institute of applied work'),('Свой стандарт совместимости','Our own compatibility standard')],['add_political_power = -50',TECH,CIV,idea('aof_v03_kaz_standards','Собственный стандарт','Domestic standards','research_speed_factor = 0.04 production_factory_max_efficiency_factor = 0.06')])]:
    k.chain(stem,names,x,10,end,fxs);roots.append(stem+'1')
for n in k.nodes:
    if n['id'][len(k.prefix):] in roots:n['excludes']=[k.prefix+r for r in roots if k.prefix+r!=n['id']]
k.node('first_batch','Первая партия собственной цепочки','The first batch for our own chain',-5,15,['industry6'],event(2,'Первая партия — не для нас','The first batch is not for us','Контракт отправляет большую часть выпуска заказчику. Местные мастерские ждут материалов. Исполнить договор, выторговать квоту или рискнуть поставками?','The contract sends most output to the customer. Local workshops await material. Honour it, bargain for a quota, or risk supply disruption?',[('Исполнить договор','Honour the contract','add_political_power = 80 add_stability = 0.03'),('Согласовать внутреннюю квоту','Negotiate a domestic quota','add_political_power = -30 '+TECH),('Односторонний пересмотр','Revise the terms unilaterally','add_stability = -0.07 '+MIL)]))
k.chain('caspian',[('Каспий не тупик','The Caspian is not a dead end'),('Условия транзита с Кавказом','Transit terms with the Caucasus'),('Гавань и внутренняя дорога','The harbour and inland road'),('Собственные торговые суда','Our own merchant vessels'),('Береговая охрана','Coastguard'),('Сохранить морской путь','Preserve the sea route')],-17,4,'entry2',['navy_experience = 10',call('CAU',70),INF,'add_equipment_to_stockpile = { type = convoy amount = 20 producer = KAZ }','navy_experience = 20','add_stability = 0.05'])
for n in k.nodes:
    if '_caspian' in n['id']:n['available']='has_global_flag = aof_caspian_navigation_verified any_owned_state = { is_controlled_by = ROOT is_coastal = yes }'
k.chain('siberia',[('Пограничный договор с Сибирью','A border compact with Siberia'),('Северный сухопутный коридор','The northern overland corridor'),('Взаимная безопасность','Mutual security')],-21,4,'entry2',['add_political_power = 30',INF,call('SIB',120)])
k.chain('soviet',[('Признание или спор о наследстве','Recognition or a succession dispute')],21,3,'entry2',['add_political_power = 35'])
k.node('noninterference','Невмешательство','Non-interference',21,4,['soviet1'],'add_stability = 0.06',excludes=[k.prefix+'border_defence'])
k.node('border_defence','Подготовить рубежи','Prepare the frontiers',24,4,['soviet1'],'army_experience = 20 '+MIL,available='SOV = { has_country_flag = aof_v03_sov_external_pressure }',excludes=[k.prefix+'noninterference'])
k.chain('turkestan',[('Пригласить посредников','Invite mediators'),('Гарантии местным правительствам','Guarantees for local governments')],27,3,'entry2',['add_political_power = -25 add_stability = 0.03',call('TRK',120)])
k.node('turk_union','Сохранить соседний союз','Preserve the neighbouring union',27,5,['turkestan2'],'add_stability = 0.04',excludes=[k.prefix+'turk_exit'])
k.node('turk_exit','Согласованный выход участников','An agreed withdrawal of participants',30,5,['turkestan2'],'add_political_power = 60',excludes=[k.prefix+'turk_union'])
k.chain('army',[('Подвижный пограничный резерв','A mobile border reserve'),('Младшие командиры республики','Junior republican officers'),('Ремонтные команды на маршрутах','Repair teams along the routes'),('Разведка больших расстояний','Long-range reconnaissance'),('Моторизовать ядро','Motorise the core'),('Парк, который мы можем содержать','A fleet we can maintain')],33,3,'entry1',['army_experience = 15','army_experience = 20',INF,'army_experience = 20',MIL,idea('aof_v03_kaz_maintained_army','Армия доступного снабжения','A maintainable army','supply_consumption_factor = -0.08 army_org_factor = 0.04')])
for x,key,r,e,fx in [(-3,'independent','Самостоятельная республика','An independent republic','add_stability = 0.1 add_political_power = 80'),(0,'steppe','Союз степных республик','A league of steppe republics',call('TRK',120)+' '+call('SIB',120)),(3,'regional','Региональная держава','A regional power','add_war_support = 0.1 army_experience = 40')]:
    k.node(key,r,e,x,17,['first_batch','army6'],fx,excludes=[k.prefix+other for other in ['independent','steppe','regional'] if other!=key])

c=Tree('CAU','Спор о федеральной казне','The disputed federal treasury','political_power_gain = -0.15 stability_factor = -0.05')
a=c.opening([('Федеральный съезд после войны','The postwar federal congress'),('Чьи обязательства обслуживает канал?','Whose obligations does the canal serve?'),('Общий бюджет или местные кассы','A common budget or local treasuries')])
c.routes([
('compact',[('Подтвердить права субъектов','Confirm constituent rights'),('Общее гражданское ведомство','A common civil service'),('Распределить доходы от транзита','Distribute transit revenues'),('Конституция сложного государства','A constitution for a complex state')],'democratic','stability_factor = 0.12 political_power_gain = 0.08 mobilization_speed = -0.1'),
('central',[('Общая армия','A common army'),('Единая таможенная служба','A common customs service'),('Центральное управление дорогами','Central management of strategic roads'),('Федеральная власть без посредников','Federal authority without intermediaries')],'neutrality','army_org_factor = 0.08 industrial_capacity_factory = 0.06 stability_factor = -0.05')],a)
c.chain('neutral',[('Конвенция свободного прохода','A convention of free passage'),('Никаких иностранных гарнизонов','No foreign garrisons'),('Собственная служба охраны','Our own security service'),('Транзит не равен подчинению','Transit is not submission')],-5,3,a,['add_political_power = 40','add_stability = 0.05','army_experience = 20',idea('aof_v03_cau_neutral','Вооружённый нейтралитет','Armed neutrality','army_defence_factor = 0.08 war_support_factor = 0.05')])
c.node('transit_crisis','Правила на случай чужой войны','Rules for somebody else’s war',-5,7,['neutral4'],event(10,'Два клиента, одна война','Two customers, one war','Прежние торговые партнёры готовятся воевать. Правила транзита должны пережить их конфликт. Военное сопровождение потребует собственных сил.','Former trading partners prepare for war. Transit rules must survive their conflict; military escorts will require our own forces.',[('Ограничить военные перевозки обеих сторон','Restrict military traffic on both sides','add_stability = 0.08 add_political_power = -30'),('Сопровождать по общим правилам','Escort traffic under common rules','army_experience = 25 add_war_support = 0.05'),('Приостановить спорный транзит','Suspend disputed transit','add_political_power = 60 add_stability = -0.04')]),available='has_global_flag = aof_caspian_navigation_verified')
c.node('alash','Предложить Алаш правила прохода','Offer Alash transit rules',-9,3,[a],call('KAZ',120),available='has_global_flag = aof_caspian_navigation_verified country_exists = KAZ NOT = { has_war_with = KAZ }')

s=Tree('SIB','Огромная страна, редкие связи','A vast country, few connections','supply_consumption_factor = 0.12 industrial_capacity_factory = -0.08')
a=s.opening([('Соединить страну после войны','Reconnect the country after war'),('Общее расписание и ремонт','A common timetable and repair service'),('Чего хотят регионы?','What do the regions want?')])
s.routes([
('civil',[('Съезд регионов','A congress of regions'),('Гражданская федерация','A civilian federation'),('Договор с Алаш','A compact with Alash'),('Свободный выход через Дальний Восток','Open access through the Far East')],'democratic','stability_factor = 0.1 supply_consumption_factor = -0.08 mobilization_speed = -0.1'),
('russia',[('Общее гражданство без общего вождя','Common citizenship without a common leader'),('Конференция российских республик','Conference of Russian republics'),('Договор вместо нового похода','A treaty instead of another march'),('Федеративное объединение согласившихся','A federation of willing republics')],'democratic','political_power_gain = 0.15 consumer_goods_factor = 0.03'),
('directory',[('Охрана узлов под единым командованием','Unified command of junction security'),('Военный заказ для мастерских','Military orders for the workshops'),('Подвижный резерв','A mobile reserve'),('Порядок на всём протяжении','Order along the whole route')],'neutrality','supply_consumption_factor = -0.12 army_org_factor = 0.06 stability_factor = -0.08')],a)
s.find('civil3')['effect']=call('KAZ',120)
s.find('civil4')['effect']+=' '+call('FER',120)
s.find('russia4')['effect']+=' '+call('SOV',120)+' '+call('FER',120)
s.chain('workshops',[('Ремонт вдоль магистрали','Repairs along the trunk line'),('Местные заказы для местных мастерских','Local orders for local workshops'),('Связность прежде парада','Connections before parades')],-5,3,a,[INF,CIV,TECH])

v=Tree('SOV','Наследие чрезвычайных управлений','Legacy of emergency administration','consumer_goods_factor = 0.08 stability_factor = -0.05')
a=v.opening([('Закрыть чрезвычайные фронтовые управления','Close emergency front administrations'),('Вернуть мастерские к работе','Return workshops to work'),('Проверить реальные возможности государства','Audit the state’s real capabilities')])
v.routes([
('recovery',[('Компромисс с местным хозяйством','A compromise with local production'),('Хлеб и промышленный товар','Bread and manufactured goods'),('От военного приказа к плану','From military orders to planning'),('Границы, которые можно защищать','Borders we can defend')],'communism','consumer_goods_factor = -0.05 industrial_capacity_factory = 0.08 war_support_factor = -0.05'),
('treaty',[('Право на отдельное правительство','The right to a separate government'),('Переговоры о взаимной торговле','Reciprocal trade negotiations'),('Общий оборонный договор','A common defence treaty'),('Добровольный союз республик','A voluntary union of republics')],'communism','stability_factor = 0.1 political_power_gain = 0.1 industrial_capacity_factory = -0.03'),
('pressure',[('Восстановить влияние за границей','Restore influence abroad'),('Помощь дружественным движениям','Aid friendly movements'),('Армия революционного давления','An army of revolutionary pressure'),('Пересмотр послевоенного устройства','Revisit the postwar settlement')],'communism','army_org_factor = 0.1 war_support_factor = 0.1 consumer_goods_factor = 0.06')],a)
v.find('pressure1')['effect']+=' set_country_flag = aof_v03_sov_external_pressure'
v.find('treaty4')['effect']+=' '+call('SIB',120)+' '+call('KAZ',120)
v.node('council_central','Советский централизм','Soviet centralism',-5,3,[a],idea('aof_v03_sov_central','Централизованный план','A centralised plan','industrial_capacity_factory = 0.06 political_power_gain = 0.1 stability_factor = -0.04'),excludes=[v.prefix+'council_local'])
v.node('council_local','Самостоятельные советы и кооперация','Autonomous councils and cooperation',-8,3,[a],idea('aof_v03_sov_local','Местные советы','Local councils','stability_factor = 0.08 research_speed_factor = 0.03 mobilization_speed = -0.1'),excludes=[v.prefix+'council_central'])
v.node('ultimatum','Потребовать пересмотра границ','Demand a revision of borders',15,7,['pressure4'],event(20,'Цена революционного давления','The price of revolutionary pressure','Командование предлагает войну независимому соседу. Это будущая эскалация, а не объявление его земли нашей исторической собственностью. Правительство может отказаться.','Command proposes war against an independent neighbour. This is a future escalation, not a declaration of historical ownership. The government may refuse.',[('Отступить от ультиматума','Withdraw the ultimatum','add_stability = 0.05 add_war_support = -0.05'),('Подготовить войну против Сибири','Prepare war against Siberia','if = { limit = { country_exists = SIB NOT = { has_war_with = SIB } } create_wargoal = { type = annex_everything target = SIB } } add_stability = -0.08')]),available='country_exists = SIB NOT = { has_war_with = SIB }')

n=Tree('NAF','Победа раньше общих учреждений','Victory before common institutions','industrial_capacity_factory = -0.08 political_power_gain = -0.1')
a=n.opening([('Съезд освобождённых территорий','Congress of liberated territories'),('Восстановить общие дороги','Restore common roads'),('Гражданская администрация вместо штаба','Civil administration instead of headquarters')])
# Complementary programmes: neutrality is compatible with civic recovery and mediation.
n.chain('neutral',[('Гарантии без иностранных баз','Guarantees without foreign bases'),('Охрана торговых портов','Guard the trading ports'),('Учебные части содружества','Commonwealth training units'),('Не становиться чужим фронтом','Do not become somebody else’s front')],-5,3,a,['add_stability = 0.05','army_experience = 20',MIL,idea('aof_v03_naf_neutral','Защищённый нейтралитет','Defended neutrality','army_defence_factor = 0.08 war_support_factor = -0.05')])
n.chain('citizen',[('Общее гражданство','Common citizenship'),('Школьная программа восстановления','Schools for recovery'),('Согласованный федеральный бюджет','An agreed federal budget'),('Одна страна равных участников','One country of equal members')],1,3,a,[POL['democratic'],TECH,CIV,idea('aof_v03_naf_citizen','Содружество граждан','A commonwealth of citizens','stability_factor = 0.08 research_speed_factor = 0.03')])
n.chain('voice',[('Посредничество между соседями','Mediation among neighbours'),('Подготовка африканских специалистов','Train African specialists'),('Порты для независимой торговли','Ports for independent trade'),('Помощь без новой опеки','Aid without new tutelage')],7,3,a,['add_political_power = 50',TECH,CIV,'add_stability = 0.05'])
n.node('aid_crisis','Просьба о помощи в чужой войне','A request for aid in another war',7,7,['voice4'],event(30,'Оружие и нейтралитет','Arms and neutrality','Просители обещают бороться за независимость. Военная помощь может защитить соседей, но ставит под угрозу нейтралитет. Содружество должно само определить предел обязательств.','Petitioners promise to fight for independence. Military aid may protect neighbours but puts neutrality at risk. The commonwealth must define the limits of its obligations.',[('Только гражданская помощь','Civilian relief only','add_political_power = -30 add_stability = 0.06'),('Ограниченная военная миссия','A limited military mission','army_experience = 30 add_war_support = 0.05 add_stability = -0.04'),('Активная оборонная политика','An active defence policy','remove_ideas = aof_v03_naf_neutral add_war_support = 0.15 add_stability = -0.08')]))

m=Tree('CMT','Военный устав в мирное время','A wartime charter in peacetime','consumer_goods_factor = 0.08 stability_factor = -0.08')
a=m.opening([('Последняя оплаченная накладная','The last paid invoice'),('Проверить военный устав','Audit the wartime charter'),('Кто говорит от имени страны?','Who speaks for the country?')])
m.routes([
('residents',[('Представительство местных общин','Representation for local communities'),('Трудовой договор вместо чрезвычайного режима','Labour contracts instead of emergency rule'),('Гражданская конституция','A civil constitution'),('Порт принадлежит стране','The port belongs to the country')],'democratic','stability_factor = 0.1 political_power_gain = 0.1 consumer_goods_factor = 0.03'),
('board',[('Сохранить коммерческий устав','Preserve the commercial charter'),('Новый американский заказ','A new American order'),('Охрана производственных коридоров','Guard production corridors'),('Государство долгого контракта','The state of the long contract')],'neutrality','industrial_capacity_factory = 0.12 production_factory_max_efficiency_factor = 0.05 stability_factor = -0.1'),
('patrons',[('Переговоры с прежними покровителями','Talks with the former patrons'),('Обновить концессионные права','Renew concession rights'),('Запросить иностранную гарантию','Request a foreign guarantee'),('Порядок за цену самостоятельности','Order at the cost of autonomy')],'neutrality','army_defence_factor = 0.08 political_power_gain = -0.1 consumer_goods_factor = -0.05')],a)
m.find('board2')['effect']=call('USA',110)
m.find('patrons3')['effect']=call('USA',110)
m.node('charter_end','Конец военного устава','The end of the wartime charter',-4,3,[a],event(40,'Не остановить страну вместе с контрактом','Do not close the country with the contract','Рабочие требуют представительства; подрядчики предупреждают о срыве снабжения. Новый устав должен решить, кто несёт цену перехода.','Workers demand representation; contractors warn of interrupted supplies. The new charter must decide who pays for transition.',[('Переходные гарантии занятости','Transitional employment guarantees','add_political_power = -50 add_stability = 0.08'),('Сохранить договоры до пересмотра','Honour contracts pending revision','add_political_power = 60 add_stability = -0.03'),('Оплатить гражданский переход','Pay for a civilian transition','add_political_power = -80 add_stability = 0.1 '+POL['democratic'])])+' '+call('USA',110))

mx=Tree('MEX','Земля, нефть и договор','Land, oil and contract','political_power_gain = -0.1 stability_factor = -0.05')
a=mx.opening([('Прекратить чрезвычайные сборы','End emergency levies'),('Земельный спор и нефтяной вопрос','Land disputes and the oil question'),('Правила для правительства и компаний','Rules for government and companies')])
mx.routes([
('law',[('Гарантии собственности и труда','Property and labour guarantees'),('Пересмотр соглашений по срокам','Revise agreements on schedule'),('Общая налоговая служба','A common tax service'),('Самостоятельность через предсказуемость','Independence through predictability')],'democratic','stability_factor = 0.12 political_power_gain = 0.1 industrial_capacity_factory = -0.03'),
('oil',[('Государственная переработка','State-owned refining'),('Местные кадры для промыслов','Local skills for the oilfields'),('Переговоры о компенсациях','Compensation negotiations'),('Договор, который пишет Мексика','A contract written by Mexico')],'democratic','industrial_capacity_factory = 0.08 research_speed_factor = 0.03 stability_factor = -0.05'),
('officers',[('Единая армия вместо политических гарнизонов','One army instead of political garrisons'),('Охрана дорог и промыслов','Guard roads and oilfields'),('Военный кабинет переходного периода','A transitional military cabinet')],'neutrality','army_org_factor = 0.08 war_support_factor = 0.05 stability_factor = -0.08')],a)
mx.find('oil1')['effect']+=' '+CIV
mx.find('oil3')['effect']=call('USA',10)
mx.find('law2')['effect']=call('USA',10)
mx.node('civil_return','Вернуть гражданский порядок','Restore civilian order',15,7,['officers3'],POL['democratic']+' remove_ideas = aof_v03_mex_officers_settlement add_stability = 0.08',excludes=[mx.prefix+'permanent'])
mx.node('permanent','Сделать исключение постоянным','Make the exception permanent',18,7,['officers3'],'add_war_support = 0.1 add_stability = -0.04',excludes=[mx.prefix+'civil_return'])
mx.node('neutral_bloc','Региональный блок нейтральных стран','A regional bloc of neutral countries',-5,3,[a],call('ARG',120)+' '+call('BRA',120))
mx.node('oil_settlement','Самостоятельное соглашение с США','An independent agreement with the USA',-5,5,['neutral_bloc'],call('USA',10))

b=Tree('BRA','Разрозненные экспортные привилегии','Fragmented export privileges','industrial_capacity_factory = -0.08 political_power_gain = -0.1')
a=b.opening([('Счёт экспортного десятилетия','Accounts of the export decade'),('Общий рынок вместо привилегий','A common market instead of privileges'),('Кому служит федеральное правительство?','Who does the federal government serve?')])
b.routes([
('republic',[('Пересмотреть правила выборов','Revise electoral rules'),('Гражданское управление гарнизонами','Civilian administration of garrisons'),('Связать внутренние рынки','Connect internal markets'),('Республика доходит до провинций','A republic that reaches the provinces')],'democratic','stability_factor = 0.1 industrial_capacity_factory = 0.04 mobilization_speed = -0.1'),
('officers',[('Программа молодых командиров','The young officers’ programme'),('Общий инфраструктурный приказ','A common infrastructure order'),('Государственный промышленный заказ','A state industrial order'),('Большая страна под единым планом','A great country under one plan')],'neutrality','industrial_capacity_factory = 0.1 army_org_factor = 0.05 stability_factor = -0.08'),
('federal',[('Гарантии региональным правительствам','Guarantees for regional governments'),('Совместные межрегиональные дороги','Joint interregional roads'),('Единый экспортный договор','A common export agreement'),('Сильная федерация без единоличного центра','A strong federation without personal rule')],'democratic','stability_factor = 0.12 political_power_gain = 0.1 mobilization_speed = -0.15')],a)
b.chain('peace',[('Не покупать влияние войной','Do not buy influence through war'),('Южноамериканская конференция','A South American conference'),('Общий оборонный договор','A common defence treaty')],-5,3,a,['add_stability = 0.05',call('ARG',90),call('ARG',120)])
b.chain('hegemony',[('Бразилия определяет правила','Brazil sets the rules'),('Приоритет собственным партнёрам','Our partners come first'),('Давление на несогласных','Pressure on dissenters')],-9,3,a,['add_war_support = 0.08','add_political_power = 60','set_country_flag = aof_brazil_hegemonic_conference '+call('ARG',90)+' add_stability = -0.04'])
b.find('peace1')['excludes']=[b.prefix+'hegemony1'];b.find('hegemony1')['excludes']=[b.prefix+'peace1']

ar=Tree('ARG','Зависимость от старого покупателя','Dependence on the old buyer','consumer_goods_factor = 0.08 production_factory_max_efficiency_factor = -0.05')
a=ar.opening([('Доходы долгой войны','Revenues of the long war'),('Когда старый покупатель не платит','When the old buyer no longer pays'),('Заказ на другую экономику','Orders for a different economy')])
ar.routes([
('industry',[('Переработка вместо одного сырья','Processing instead of raw exports'),('Собственные машины для хозяйства','Domestic machines for production'),('Верфи торгового флота','Merchant shipyards'),('Полный производственный цикл','A complete production cycle')],'democratic','industrial_capacity_factory = 0.1 production_factory_max_efficiency_factor = 0.08 consumer_goods_factor = 0.03'),
('league',[('Конференция южных государств','Conference of southern states'),('Арбитраж вместо ультиматума','Arbitration instead of ultimatums'),('Совместная морская безопасность','Joint maritime security'),('Никто не говорит за весь континент','Nobody speaks for the whole continent')],'democratic','stability_factor = 0.1 political_power_gain = 0.12 war_support_factor = -0.05'),
('atlantic',[('Порты как основа влияния','Ports as the basis of influence'),('Приоритет морскому заказу','Naval orders take priority'),('Защита дальних торговых связей','Defend distant trading links'),('Право определять региональный порядок','The right to shape regional order')],'neutrality','industrial_capacity_dockyard = 0.12 navy_org_factor = 0.08 industrial_capacity_factory = -0.05')],a)
ar.find('industry2')['effect']+=' '+MIL
ar.find('industry3')['effect']='navy_experience = 20 add_equipment_to_stockpile = { type = convoy amount = 20 producer = ARG }'
ar.find('league1')['effect']+=' '+call('BRA',90)
ar.find('league4')['effect']+=' '+call('BRA',120)

ch=Tree('CHI','Раздельные цепочки командования','Separate chains of command','army_org_factor = -0.08 political_power_gain = -0.1')
a=ch.opening([('Согласовать ближайший фронт','Coordinate the nearest front'),('Кому подчиняются гарнизоны?','Who commands the garrisons?'),('Разобрать иностранные обязательства','Audit foreign obligations')])
ch.routes([
('agreement',[('Конференция региональных правительств','Conference of regional governments'),('Общие пошлины и снабжение','Common customs and military supplies'),('Конституция объединения','A constitution for union'),('Одна дипломатия без одного генерала','One diplomacy without one general')],'democratic','stability_factor = 0.1 political_power_gain = 0.1 army_org_factor = -0.03'),
('army',[('Общий штаб','A common general staff'),('Отрезать независимые каналы оружия','End independent arms channels'),('Поход на неподчиняющиеся центры','A campaign against defiant centres')],'neutrality','army_org_factor = 0.1 war_support_factor = 0.08 stability_factor = -0.08'),
('land',[('Соглашение с сельскими движениями','Agreement with rural movements'),('Местная реформа собственности','Local property reform'),('Снабжение изнутри страны','Supply from within the country')],'democratic','consumer_goods_factor = -0.05 supply_consumption_factor = -0.08 stability_factor = -0.04')],a)
ch.node('army_civil','Гражданское правительство после объединения','Civil government after unification',8,7,['army3'],POL['democratic']+' remove_ideas = aof_v03_chi_army_settlement add_stability = 0.08',excludes=[ch.prefix+'army_state'])
ch.node('army_state','Государство командования','A state of command',11,7,['army3'],'add_war_support = 0.1 '+MIL,excludes=[ch.prefix+'army_civil'])
ch.node('social','Социальная республика','A social republic',15,7,['land3'],POL['democratic']+' add_stability = 0.06',excludes=[ch.prefix+'revolution'])
ch.node('revolution','Революционная власть','Revolutionary government',18,7,['land3'],POL['communism']+' add_war_support = 0.08',excludes=[ch.prefix+'social'])
ch.node('foreign_price','Единство не за чужую цену','Unity without a foreign price',-5,3,[a],event(50,'Условия военной миссии','The military mission’s conditions','Иностранные инструкторы готовы обучать части, но требуют политических уступок. Помощь не должна навсегда решать за правительство страны.','Foreign instructors offer training but demand political concessions. Assistance must not permanently decide the government’s choices.',[('Ограниченное обучение без обязательств','Limited training without commitments','army_experience = 20 add_political_power = -30'),('Собственная школа командиров','Our own officer school','army_experience = 10 add_stability = 0.05 '+TECH),('Принять военный приоритет','Accept the military priority','army_experience = 40 add_stability = -0.06')]))

# Six-family political milestones: cooperative reform is not Soviet centralism.
for tree,key in [(k,'land1'),(mx,'oil1'),(ch,'land1')]:
    tree.find(key)['effect']=tree.find(key)['effect'].replace(POL['democratic'],POL['aof_social_democracy'])
ch.find('social')['effect']=POL['aof_social_democracy']+' add_stability = 0.06'

# A refused offer opens a domestic substitute rather than silently granting aid.
for stem,flag in [('american','aof_usa_partnership'),('japanese','aof_jap_partnership')]:
    k.find(stem+'2')['available']='OR = { has_country_flag = '+flag+'_accepted has_country_flag = '+flag+'_refused }'
    for i in [2,3,4]:
        node=k.find(stem+str(i));original=node['effect']
        node['effect']='if = { limit = { has_country_flag = '+flag+'_accepted } '+original+' } else = { add_political_power = -25 army_experience = 10 }'
        node['desc_ru']='При согласии партнёра действует совместная программа. При отказе республика оплачивает более медленную внутреннюю замену: 25 политической власти за подготовку собственных специалистов.'
        node['desc_en']='Acceptance enables the joint programme. If refused, the republic pays for a slower domestic substitute: 25 political power to train its own specialists.'
        node['cost']=5 if i==2 else 7
k.find('caspian3')['available']+=' has_country_flag = aof_caspian_agreement_accepted'
k.find('caspian2')['desc_ru']='Кавказ получает встречное предложение и может отказать. Тогда северный сухопутный коридор остаётся доступен без морского соглашения.'
k.find('caspian2')['desc_en']='The Caucasus receives an offer and may refuse. The northern overland corridor remains available without a maritime agreement.'
k.find('american4')['effect']+=' '+event(3,'Следующий договор','The next contract','Первый контракт дал станки и обязательства. Теперь можно продлить прежние условия, оплатить более равноправный договор или выйти из него с временными потерями.','The first contract brought machines and obligations. Renew it, pay for more equal terms, or leave with transitional losses.',[('Сохранить доверие заказчика','Preserve the customer’s trust','add_political_power = 70 add_stability = -0.02'),('Оплатить равноправный пересмотр','Pay for equal revision','add_political_power = -60 add_stability = 0.07 '+TECH),('Завершить исключительный договор','End the exclusive contract','clr_country_flag = aof_usa_partnership_accepted set_country_flag = aof_usa_partnership_ended add_stability = -0.06 '+MIL)])

# Explicit costs of retaining a wartime command, not an automatic coup.
# Give each programme projects matching its purpose; not every third step is
# an infrastructure reward merely because of its position in a route.
for tree,key,reward in [
    (k,'land2',CIV),(k,'land3',TECH),(k,'land4',CIV),(k,'mandate3',MIL),
    (c,'central1','army_experience = 20'),(c,'compact3','add_political_power = 50'),
    (s,'directory2',MIL),(s,'directory3','army_experience = 25'),
    (v,'recovery2',CIV),(v,'recovery3',TECH),(v,'pressure2','army_experience = 20'),(v,'pressure3',MIL),
    (m,'residents2','add_stability = 0.04'),(m,'board3',INF),
    (mx,'oil2',TECH),(mx,'officers3',MIL),
    (b,'republic3',CIV),(b,'officers3',MIL),(b,'federal3',CIV),
    (ar,'industry1',CIV),(ar,'industry2',TECH),(ar,'league3','navy_experience = 25'),
    (ch,'army2',MIL),(ch,'land2',CIV)]:
    tree.find(key)['effect']+=' '+reward

b.node('military_promise','Обещание переходного кабинета','The transitional cabinet’s promise',9,7,['officers4'],event(60,'После общего приказа','After the common order','Единый план построил дороги. Офицеры теперь спорят, кому передать учреждения, которые они создали. Продление их мандата сохранит скорость приказа ценой гражданских гарантий.','The common plan built roads. Officers now dispute who should inherit their institutions. Extending their mandate preserves command speed at the cost of civilian guarantees.',[('Гражданский контроль над новым аппаратом','Civilian control of the new administration',POL['democratic']+' remove_ideas = aof_v03_bra_officers_settlement add_stability = 0.1'),('Постоянное командование модернизации','Permanent modernisation command',POL['neutrality']+' add_war_support = 0.1 add_stability = -0.05')]))
s.node('port_conditions','Цена чужого выхода к морю','The price of somebody else’s sea access',-5,6,['workshops3'],event(70,'Порт и японские условия','The port and Japanese conditions','Выход через Владивосток зависит не только от Сибири. Военные требуют независимого маршрута, купцы — доступных условий. Можно сохранить компромисс, обойти порт или поддержать самостоятельность соседа.','Access through Vladivostok depends on more than Siberia. Officers demand an independent route, merchants seek workable terms. Keep a compromise, bypass the port, or support the neighbour’s autonomy.',[('Торговое сотрудничество без военных обязательств','Trade cooperation without military commitments',call('FER',120)+' add_political_power = -30'),('Вложиться в сухопутный маршрут через Алаш','Invest in an overland route through Alash',INF+' add_political_power = -25'),('Поддержать самостоятельность Дальнего Востока','Support Far Eastern autonomy',call('FER',120)+' add_war_support = 0.08 add_stability = -0.03')]))

# China: a consensual coalition offers replies; military coercion needs an
# existing neighbouring warlord rather than an invented territorial claim.
ch.find('agreement1')['effect']+=' '+''.join(call(tag,120) for tag in ['SHX','YUN','GXC','XSM'])
targets=' '.join('tag = '+tag for tag in ['SHX','YUN','GXC','XSM'])
ch.find('army3')['effect']='army_experience = 25 '+event(80,'Цена общего штаба','The price of a common staff','Военная координация не даёт права на чужие правительства. Можно пригласить соседей в добровольный договор или подготовить поход против неподчинившегося пограничного центра.','Military coordination gives no ownership of other governments. Invite neighbours into a voluntary compact or prepare a campaign against a defiant neighbouring centre.',[('Договорный выход остаётся открыт','Keep a negotiated outcome open',''.join(call(tag,120) for tag in ['SHX','YUN','GXC','XSM'])),('Готовить поход только против пограничного центра','Prepare a campaign against a neighbouring centre only','random_other_country = { limit = { OR = { '+targets+' } is_neighbor_of = ROOT is_subject = no NOT = { is_in_faction_with = ROOT } NOT = { has_war_with = ROOT } } ROOT = { create_wargoal = { type = annex_everything target = PREV } } } add_stability = -0.08')])

k.find('first_batch')['pre'].append([k.prefix+'american2',k.prefix+'japanese2',k.prefix+'diverse2'])
k.find('service3')['effect']+=' remove_ideas = aof_v03_kaz_local_compacts'
k.find('industry6')['effect']+=' remove_ideas = aof_v03_kaz_resource_gap'
k.find('army5')['pre'].append(k.prefix+'industry5')
coast='any_owned_state = { is_controlled_by = ROOT is_coastal = yes }'
for tree,key in [(n,'neutral2'),(n,'voice3'),(ar,'industry3'),(ar,'atlantic1')]:tree.find(key)['available']=coast
ar.find('industry3')['effect']+=' random_owned_controlled_state = { limit = { is_coastal = yes } add_extra_state_shared_building_slots = 1 add_building_construction = { type = dockyard level = 1 instant_build = yes } }'
ar.find('atlantic2')['effect']='navy_experience = 25'
ar.find('atlantic3')['effect']='add_equipment_to_stockpile = { type = convoy amount = 20 producer = ARG }'

# Material DesignBook audit: a named project must change its actual subject,
# and an offer must leave the other country's player a real response.
# Verified playtest railway spurs: join the capital and Caspian home base to
# the existing level-two main line, without changing foreign infrastructure.
kaz_rail_spurs=[[1591,10146,4773,10603,12640,4686,12397],[1517,4523,10262,12163,10131,4303,4374]]
kaz_rail_network=[12397,7597,12329,7657,7600,7243,4300,4374]
kaz_rail_provinces=sorted(set(kaz_rail_network+sum(kaz_rail_spurs,[])))
kaz_rail_guard='tag = KAZ '+' '.join(str(sid)+' = { is_owned_by = ROOT }' for sid in [402,404,586,587,1083,1086])+' '+' '.join('controls_province = '+str(prov) for prov in kaz_rail_provinces)
k.find('entry2')['effect']+=' if = { limit = { '+kaz_rail_guard+' } '+' '.join('build_railway = { level = 1 build_only_on_allied = yes path = { '+' '.join(map(str,path))+' } }' for path in kaz_rail_spurs)+' }'
k.find('entry2')['final_desc_ru']='Улучшим инфраструктуру и соединим столицу и каспийскую базу с главной железнодорожной сетью. Обе перемычки требуют владения и контроля Алаш над всем маршрутом.'
k.find('entry2')['final_desc_en']='Improve infrastructure and connect the capital and Caspian base to the main railway network. Both spurs require Alash to own and control the entire route.'
c.find('transit_crisis')['available']='has_global_flag = aof_caspian_navigation_verified KAZ = { exists = yes has_war = yes has_country_flag = aof_caspian_agreement_accepted } NOT = { has_war_with = KAZ }'
c.find('transit_crisis')['effect']=event(10,'Конвенция и воюющий клиент','The convention and a belligerent client','Алаш участвует в войне и требует сохранить проход. Охрана требует наших средств. Ограничение страны перекрывает её военные перевозки и торговые конвои; чрезвычайное закрытие всего канала затрагивает всех клиентов. Ни одно решение не вводит Кавказ в чужую войну.','Alash is at war and requests continued passage. Protection costs us resources. A country restriction blocks its military shipping and trade convoys; emergency closure affects every customer. None of these decisions joins another country’s war.',[
 ('Сохранить проход за счёт собственной охраны','Maintain passage with our own protection','add_political_power = -30 clr_global_flag = aof_caucasian_canal_closed KAZ = { clr_country_flag = aof_caucasian_canal_blocked_for_country set_country_flag = aof_caspian_wartime_access } army_experience = 15'),
 ('Приостановить проход воюющего клиента','Suspend passage for the belligerent client','KAZ = { set_country_flag = aof_caucasian_canal_blocked_for_country set_country_flag = aof_caspian_overland_fallback } add_stability = -0.03'),
 ('Временно закрыть канал для всех','Temporarily close the canal to everyone','set_global_flag = aof_caucasian_canal_closed add_political_power = -25 add_stability = -0.05'),
])
def answered(flag):return 'OR = { has_country_flag = '+flag+'_accepted has_country_flag = '+flag+'_limited has_country_flag = '+flag+'_refused }'

# Existing parties receive an overt organising proposal, never a generated
# rebellion. The neighbour's government makes the political decision itself.
movement_target='is_subject = no communism > 0 NOT = { has_government = communism } NOT = { has_war_with = ROOT }'
movement_response='is_subject = no FROM = { exists = yes tag = SOV } NOT = { has_war_with = FROM }'
event(81,'Зарубежная помощь и местное движение','Foreign support and a local movement','Представители существующего коммунистического движения предлагают принять советскую помощь для открытой политической работы. Правительство может разрешить организацию, поддержать собственную парламентскую реформу или выслать организаторов. Это меняет поддержку партий, а не объявляет восстание, войну или смену власти.','Representatives of an existing communist movement propose accepting Soviet support for public political organising. The government may permit it, pursue its own parliamentary reform, or expel the organisers. This changes party support; it creates no rebellion, war or imposed government.',[
 ('Разрешить открытую организационную работу','Permit public organising','add_popularity = { ideology = communism popularity = 0.03 } add_stability = -0.02',movement_response),
 ('Ответить собственной парламентской реформой','Respond with domestic parliamentary reform','add_political_power = -15 add_popularity = { ideology = aof_social_democracy popularity = 0.02 } add_stability = 0.01',movement_response),
 ('Выслать иностранных организаторов','Expel foreign organisers','add_popularity = { ideology = communism popularity = -0.02 } add_opinion_modifier = { target = FROM modifier = aof_v03_diplomatic_pressure }',movement_response),
 ('Обстоятельства изменились: оставить вопрос без продолжения','Circumstances changed: take no further action','','NOT = { AND = { '+movement_response+' } }'),
])
v.find('pressure2')['available']='has_government = communism'
v.find('pressure2')['effect']='add_political_power = -35 if = { limit = { any_neighbor_country = { '+movement_target+' } } random_neighbor_country = { limit = { '+movement_target+' } country_event = { id = aof_nations.81 days = 2 } } } else = { '+TECH+' add_stability = 0.02 }'
v.find('pressure2')['details_ru']='На организационную программу уйдут 35 единиц политического ресурса. Одному независимому соседу с существующей коммунистической поддержкой поступит предложение: его правительство может отказать или выбрать собственную реформу. Если подходящего соседа нет, средства пойдут на внутреннюю прикладную школу и согласование хозяйственного плана.'
v.find('pressure2')['details_en']='The organising programme costs 35 political power. One independent neighbour with existing communist support receives a proposal; its government may reject it or choose its own reform. If no eligible neighbour exists, the funds support a domestic applied school and agreement on the economic plan.'
def union_offer(tag):
    return 'if = { limit = { has_war = no is_subject = no '+tag+' = { exists = yes has_war = no is_subject = no is_in_faction_with = ROOT } } '+tag+' = { country_event = { id = aof_diplomacy.160 days = 2 } } }'
SOUTH_AMERICA=['BRA','ARG','CHL','PRU','BOL','PAR','URG','ECU','COL','VEN']
def conference_offers(sender):return ' '.join(call(tag,90) for tag in SOUTH_AMERICA if tag!=sender)
def conference_defence(sender):
    return 'every_other_country = { limit = { has_country_flag = aof_conference_participant_'+sender.lower()+' is_subject = no NOT = { has_war_with = ROOT } } country_event = { id = aof_diplomacy.120 days = 2 } }'

# One bounded industrial project in an actually owned, controlled state. The
# existing resource determines the small recovery; no ore field is invented.
resources=['steel','oil','aluminium','tungsten','chromium','rubber']
known_resource='OR = { '+' '.join('has_resources_amount = { resource = '+r+' amount > 0 }' for r in resources)+' }'
project='has_state_flag = aof_kaz_survey_project'
survey='if = { limit = { any_owned_state = { is_controlled_by = ROOT '+known_resource+' } } random_owned_controlled_state = { limit = { '+known_resource+' } set_state_flag = aof_kaz_survey_project } } else = { capital_scope = { set_state_flag = aof_kaz_survey_project } }'
road='add_building_construction = { type = infrastructure level = 1 instant_build = yes }'
recovery=''
for i,r in enumerate(resources):
    recovery+=('if' if i==0 else 'else_if')+' = { limit = { has_resources_amount = { resource = '+r+' amount > 0 } } add_resource = { type = '+r+' amount = '+('1' if r=='oil' else '2')+' } } '
processing='add_extra_state_shared_building_slots = 1 add_building_construction = { type = industrial_complex level = 1 instant_build = yes } '+recovery
k.find('industry2')['effect']='add_political_power = -25 '+survey
k.find('industry3')['effect']='if = { limit = { any_owned_state = { is_controlled_by = ROOT '+project+' } } random_owned_controlled_state = { limit = { '+project+' } '+road+' } } else = { '+INF+' }'
k.find('industry4')['effect']='if = { limit = { any_owned_state = { is_controlled_by = ROOT '+project+' } } random_owned_controlled_state = { limit = { '+project+' } '+processing+' } } else = { '+CIV+' }'
k.find('industry2')['details_ru']='Один контролируемый район с уже известным сырьём станет местом ограниченного проекта. После дороги переработка увеличит выпуск только того ресурса, который уже производится здесь.'
k.find('industry2')['details_en']='One controlled state with a known resource becomes the site of a limited project. After a road is built, processing recovers a little more of a resource already produced there.'
k.find('siberia1')['effect']=call('SIB',120)
k.find('siberia2')['effect']='if = { limit = { any_owned_state = { is_controlled_by = ROOT any_neighbor_state = { is_owned_by = SIB } } } random_owned_controlled_state = { limit = { any_neighbor_state = { is_owned_by = SIB } } '+road+' } } else = { '+INF+' }'
k.find('soviet1')['effect']=call('SOV',183)
k.find('noninterference')['available']='has_country_flag = aof_kaz_sov_noninterference_accepted'
k.find('noninterference')['effect']='add_stability = 0.04 '+TECH
k.find('border_defence')['available']='OR = { has_country_flag = aof_kaz_sov_noninterference_refused SOV = { has_country_flag = aof_v03_sov_external_pressure } }'
k.find('turkestan1')['effect']='if = { limit = { TRK = { exists = yes is_subject = no has_war = no } NOT = { has_war_with = TRK } } '+call('TRK',182)+' } else = { set_country_flag = aof_turkestan_mediation_refused add_stability = 0.02 }'
k.find('turkestan2')['available']=answered('aof_turkestan_mediation')
k.find('turkestan2')['effect']='if = { limit = { has_country_flag = aof_turkestan_mediation_accepted TRK = { exists = yes is_subject = no } NOT = { has_war_with = TRK } } give_guarantee = TRK } else = { army_experience = 15 }'
k.find('turk_union')['effect']=call('TRK',120)
k.find('turk_exit')['effect']='if = { limit = { has_country_flag = aof_turkestan_mediation_accepted TRK = { exists = yes has_war = no } } TRK = { country_event = { id = aof_partition.1 days = 2 } } } else = { add_stability = 0.03 }'
k.find('turk_exit')['details_ru']='Предложение поступит съезду Туркестана. Только его правительство может принять конкретный договор о разделе; отказ не передаёт нам территории и не начинает войну.'
k.find('turk_exit')['details_en']='The proposal goes to the Turkestani congress. Only its government can accept the specific partition treaty; refusal transfers no territory and starts no war.'
k.find('independent')['effect']=idea('aof_v03_kaz_self_reliant','Самостоятельная производственная цепочка','A self-reliant production chain','research_speed_factor = 0.03 production_factory_max_efficiency_factor = 0.04 stability_factor = 0.05')
k.find('regional')['effect']=idea('aof_v03_kaz_regional_capacity','Средства региональной политики','The means of a regional policy','industrial_capacity_factory = 0.05 army_org_factor = 0.05 stability_factor = -0.04')+' army_experience = 25'

# The civil Siberian route buys access, not an unwanted alliance. Its other
# Russian route and the Soviet treaty route can propose actual consensual union.
s.find('civil4')['effect']=s.find('civil4')['effect'].replace(call('FER',120),call('FER',81))
s.find('russia2')['effect']=call('SOV',120)+' '+call('FER',120)
s.find('russia4')['effect']=idea('aof_v03_sib_russia_settlement','Договор российских республик','A compact of Russian republics',IDEAS['aof_v03_sib_russia_settlement'])+' '+union_offer('SOV')+' '+union_offer('FER')
v.find('treaty3')['effect']=call('SIB',120)+' '+call('KAZ',120)
v.find('treaty4')['effect']=idea('aof_v03_sov_treaty_settlement','Союз согласившихся республик','A union of consenting republics',IDEAS['aof_v03_sov_treaty_settlement'])+' '+union_offer('SIB')+' '+union_offer('KAZ')
ch.find('agreement4')['effect']+=' '+' '.join(union_offer(tag) for tag in ['SHX','YUN','GXC','XSM'])
s.find('port_conditions')['effect']=event(70,'Порт и японские условия','The port and Japanese conditions','Выход через Владивосток зависит от местного правительства и японской гарантии. Можно согласовать торговлю, вложиться в другой маршрут или предложить поддержку самостоятельности. Ни одно решение не начинает войну само по себе.','Access through Vladivostok depends on its government and the Japanese guarantee. Negotiate trade, invest in another route, or offer support for autonomy. None of these choices automatically starts a war.',[('Торговое сотрудничество без военных обязательств','Trade without military commitments',call('FER',81)+' add_political_power = -30'),('Вложиться в сухопутный маршрут через Алаш','Invest in an overland route through Alash',INF+' add_political_power = -25'),('Предложить поддержку самостоятельности','Offer support for autonomy',call('FER',190)+' add_political_power = -35')])

# Commercial government: constitutional reform, procurement and a prospective
# dependency are different bargains, each with a sovereign counterparty.
employment=idea('aof_v03_cmt_employment_transition','Гарантии переходной занятости','Transitional employment guarantees','stability_factor = 0.05 industrial_capacity_factory = -0.04 consumer_goods_factor = 0.02')
market=idea('aof_v03_cmt_market_charter','Выборный надзор над контрактами','Elected oversight of contracts','production_factory_efficiency_gain_factor = 0.05 consumer_goods_factor = 0.02')
social=idea('aof_v03_cmt_social_charter','Общественный договор труда','A social compact of labour','research_speed_factor = 0.03 consumer_goods_factor = -0.02 industrial_capacity_factory = -0.03')
domestic_orders=idea('aof_v03_cmt_internal_orders','Внутренний заказ без покровителя','Domestic orders without a patron','industrial_capacity_factory = 0.06 production_factory_max_efficiency_factor = 0.03 stability_factor = -0.05')
m.find('charter_end')['effect']=event(40,'Не остановить страну вместе с контрактом','Do not close the country with the contract','Рабочие требуют представительства, подрядчики предупреждают о срыве снабжения. Можно оплатить гарантии занятости, исполнить старые обязательства до пересмотра или до выбора авторитарного пути профинансировать гражданский переход.','Workers demand representation, while contractors warn of disrupted supplies. Fund transitional employment, honour old obligations pending revision, or fund a civilian transition before committing to an authoritarian course.',[('Переходные гарантии занятости','Transitional employment guarantees','add_political_power = -50 add_timed_idea = { idea = aof_v03_cmt_employment_transition days = 365 }'),('Сохранить договоры до пересмотра','Honour contracts pending revision','add_political_power = 40 add_stability = -0.03 set_country_flag = aof_cmt_contracts_honoured'),('Оплатить гражданский переход','Fund a civilian transition','add_political_power = -80 add_stability = 0.06 set_country_flag = aof_cmt_civil_charter '+POL['democratic'],'NOT = { OR = { has_completed_focus = aof_v03_cmt_board1 has_completed_focus = aof_v03_cmt_patrons1 has_completed_focus = aof_v03_cmt_residents3 } }')])
for key in ['board1','patrons1']:m.find(key)['available']='NOT = { has_country_flag = aof_cmt_civil_charter }'
m.find('residents3')['effect']=event(41,'Кому подотчётна гражданская республика?','To whom is the civilian republic accountable?','Представительство жителей стало законом. Выборный надзор может сохранить рыночные договоры или опереться на парламентскую программу труда и образования. Ни один вариант не отменяет независимость и многопартийность.','Resident representation has become law. Elected oversight may preserve market contracts or rest on a parliamentary programme for labour and education. Both choices retain independence and competitive government.',[('Выборный рыночный кабинет','An elected market cabinet',POL['democratic']+' '+market),('Парламентский социальный договор','A parliamentary social compact',POL['aof_social_democracy']+' '+social)])
m.find('residents4')['effect']+=' '+call('USA',110)
def cmt_partner(protection=False):
    return 'is_subject = no '+('has_war = no ' if protection else '')+'USA = { exists = yes is_subject = no has_war = no } NOT = { has_war_with = USA }'
def cmt_request(flag,number,protection=False):
    return 'set_country_flag = '+flag+'_requested if = { limit = { '+cmt_partner(protection)+' } '+call('USA',number)+' } else = { set_country_flag = '+flag+'_refused set_country_flag = '+flag+'_closed add_political_power = 10 }'
def cmt_answer_or_expiry(flag,protection=False):
    return 'OR = { '+answered(flag)+' has_country_flag = { flag = '+flag+'_requested days > 30 } NOT = { AND = { '+cmt_partner(protection)+' } } }'
def cmt_close_unanswered(flag):
    return 'if = { limit = { NOT = { '+answered(flag)+' } } set_country_flag = '+flag+'_refused set_country_flag = '+flag+'_closed } '
m.find('board2')['effect']=cmt_request('aof_cmt_procurement',171)
m.find('board2').pop('available',None)
m.find('board3')['available']=cmt_answer_or_expiry('aof_cmt_procurement')
m.find('board3')['effect']=cmt_close_unanswered('aof_cmt_procurement')+m.find('board3')['effect']
m.find('board4')['effect']='if = { limit = { OR = { has_country_flag = aof_cmt_procurement_accepted has_country_flag = aof_cmt_procurement_limited } } add_ideas = aof_v03_cmt_board_settlement } else = { '+domestic_orders+' }'
m.find('patrons3')['effect']=cmt_request('aof_cmt_protection',170,True)
m.find('patrons3').pop('available',None)
m.find('patrons3')['details_ru']='Предложение новой защиты США допускает добровольную зависимость, ограниченную гарантию или отказ. Оно не утверждает, что США были прежним покровителем.'
m.find('patrons3')['details_en']='The request for new American protection may produce voluntary dependency, a limited guarantee or refusal. It does not make America an original patron.'
m.find('patrons4')['available']=cmt_answer_or_expiry('aof_cmt_protection',True)
m.find('patrons4')['effect']=cmt_close_unanswered('aof_cmt_protection')+'if = { limit = { OR = { has_country_flag = aof_cmt_protection_accepted has_country_flag = aof_cmt_protection_limited } } add_ideas = aof_v03_cmt_patrons_settlement } else = { army_experience = 20 '+INF+' }'
for key in ['board3','patrons4']:
    m.find(key)['details_ru']='Продолжить можно после ответа, через тридцать дней без ответа либо при недоступности партнёра. Без действительного согласия правительство закроет запрос как отклонённый и продолжит внутреннюю программу; иностранные гарантии не появятся.'
    m.find(key)['details_en']='Continue after a reply, after thirty days without one, or when the partner becomes unavailable. Without actual consent the government closes the request as refused and continues domestically; no foreign guarantees are invented.'

# Neutrality now includes accepted mediation and real, stock-limited aid.
n.find('voice1')['effect']='add_political_power = -25 if = { limit = { country_exists = CMT NOT = { has_war_with = CMT } } '+call('CMT',180)+' } else = { '+TECH+' }'
n.find('voice4')['effect']=TECH+' if = { limit = { has_country_flag = aof_naf_mediation_accepted country_exists = CMT } CMT = { '+TECH+' } }'
n.find('voice3')['effect']+=' add_equipment_to_stockpile = { type = convoy amount = 10 producer = NAF } random_owned_controlled_state = { limit = { is_coastal = yes } add_extra_state_shared_building_slots = 1 add_building_construction = { type = dockyard level = 1 instant_build = yes } }'
african_war='is_subject = no has_war = yes capital_scope = { is_on_continent = africa } NOT = { has_war_with = ROOT }'
n.find('aid_crisis')['available']='any_other_country = { '+african_war+' }'
n.find('aid_crisis')['effect']='random_other_country = { limit = { '+african_war+' } country_event = { id = aof_diplomacy.181 days = 2 } }'
aid_partner='FROM = { exists = yes is_subject = no has_war = yes capital_scope = { is_on_continent = africa } } NOT = { has_war_with = FROM }'
event(31,'Просьба о помощи изменилась','The aid request has changed','Получатель больше не соответствует условиям согласованной помощи. Вооружение и гарантии не переданы; можно вернуться к дипломатии при новых обстоятельствах.','The recipient no longer meets the agreed conditions. No arms or guarantees were transferred; diplomacy can resume when circumstances change.',[('Учесть новые обстоятельства','Acknowledge the changed circumstances','')])
def aid_recheck(fx,extra=''):
    return 'if = { limit = { '+aid_partner+' '+extra+' } '+fx+' } else = { country_event = { id = aof_nations.31 days = 1 } }'
event(30,'Оружие и нейтралитет','Arms and neutrality','Иностранное правительство ответило на наше предложение. Гражданская помощь не создаёт военного союза. Оружие берётся из наших запасов, а гарантия безопасности означает сознательное расширение обязательств, но не вступление в текущую войну.','A foreign government has answered our offer. Civilian relief creates no alliance. Arms come from our stockpile; a guarantee deliberately expands our commitments without entering the current war.',[
 ('Гражданская помощь без военных обязательств','Civilian aid without military commitments',aid_recheck('add_political_power = -30 FROM = { add_stability = 0.04 add_opinion_modifier = { target = ROOT modifier = aof_v03_cooperation } }'),aid_partner),
 ('Передать двести винтовок из наших запасов','Send two hundred rifles from our stockpile',aid_recheck('send_equipment = { equipment = infantry_equipment amount = 200 target = FROM } army_experience = 10 add_stability = -0.02','has_equipment = { infantry_equipment > 199 }'),aid_partner+' FROM = { has_country_flag = aof_naf_military_aid_requested } has_equipment = { infantry_equipment > 199 }'),
 ('Дать собственную гарантию безопасности','Offer our own security guarantee',aid_recheck('give_guarantee = FROM remove_ideas = aof_v03_naf_neutral add_war_support = 0.08 add_stability = -0.04'),aid_partner+' FROM = { has_country_flag = aof_naf_military_aid_requested }'),
 ('Сохранить нейтралитет без новой помощи','Retain neutrality without new assistance','add_political_power = 15'),
])

# Invitations reach actual sovereign governments. Equal-term counteroffers
# return to the proposer; defence membership still needs each recipient's yes.
b.find('peace2')['effect']='add_political_power = -35 '+conference_offers('BRA')
b.find('peace3')['effect']=conference_defence('BRA')+' army_experience = 15'
b.find('hegemony3')['effect']='set_country_flag = aof_brazil_hegemonic_conference '+conference_offers('BRA')+' add_stability = -0.04'
ar.find('league1')['effect']=POL['democratic']+' add_political_power = -35 '+conference_offers('ARG')
ar.find('league4')['effect']=idea('aof_v03_arg_league_settlement','Лига равных республик','A league of equal republics',IDEAS['aof_v03_arg_league_settlement'])+' '+conference_defence('ARG')
ar.node('counterconference','Равноправная конференция вместо первенства','An equal conference instead of primacy',-6,3,['entry3'],'add_political_power = -50 '+conference_offers('ARG'),available='OR = { has_country_flag = aof_counterconference_mandate BRA = { has_country_flag = aof_brazil_hegemonic_conference } }')
ar.node('counterdefence','Оборона без чужого первенства','Defence without another state’s primacy',-6,4,['counterconference'],conference_defence('ARG')+' army_experience = 20')

disruption=idea('aof_v03_mex_supply_disruption','Издержки одностороннего пересмотра','Costs of unilateral revision','industrial_capacity_factory = -0.08 research_speed_factor = -0.03')
oil_event=event(90,'Нефтяной договор после ответа','The oil contract after the reply','Ответ США не завершает наш выбор. Согласованный переход сохраняет поставки ценой компенсаций. Новые партнёры требуют новых переговоров. Односторонний пересмотр ускоряет внутренний заказ, но нарушает снабжение и ухудшает отношения.','The American reply does not end our choices. An agreed transition preserves supplies at the cost of compensation. New partners require new negotiations. Unilateral revision accelerates domestic orders but disrupts supply and worsens relations.',[
 ('Выполнить согласованный компенсационный переход','Implement the agreed compensation transition','add_political_power = -35 add_timed_idea = { idea = aof_v03_compensated_trade days = 730 }','has_country_flag = aof_oil_compromise_accepted'),
 ('Искать других инвесторов без войны','Seek other investors without war','add_political_power = -40 country_event = { id = aof_v03_regions.1 days = 1 }'),
 ('Провести односторонний пересмотр','Revise the terms unilaterally','set_country_flag = aof_mex_unilateral_oil add_timed_idea = { idea = aof_v03_mex_supply_disruption days = 365 } '+MIL+' if = { limit = { country_exists = USA } add_opinion_modifier = { target = USA modifier = aof_v03_diplomatic_pressure } } '+call('USA',10)),
])
mx.node('oil_outcome','Самостоятельность после нефтяного спора','Independence after the oil dispute',-5,7,['oil_settlement'],oil_event,available='OR = { has_country_flag = aof_oil_compromise_accepted has_country_flag = aof_oil_compromise_refused }')
for tree,key,ru,en in [
 (ar,'counterconference','Первенство Бразилии не обязывает нас отказываться от сотрудничества. Предложим равноправную конференцию независимым соседям: каждый вправе принять условия, предложить свои или отказаться.','Brazilian primacy need not end cooperation. We will invite independent neighbours to an equal conference; each may accept, counteroffer or refuse.'),
 (ar,'counterdefence','Ответившие на нашу конференцию правительства получат отдельное предложение оборонительного союза. Участие в обсуждении не заменяет их согласия на военные обязательства.','Governments participating in our conference receive a separate defence proposal. Joining talks never substitutes for consent to military obligations.'),
 (mx,'oil_outcome','Полученный ответ открывает выбор между согласованными компенсациями, переговорами с другими инвесторами и односторонним пересмотром. Последний ускорит внутренний заказ ценой перебоев снабжения и ухудшения отношений.','The reply opens a choice between agreed compensation, talks with other investors and unilateral revision. The latter accelerates domestic orders at the cost of supply disruption and relations.')]:
    tree.find(key)['desc_ru']=ru;tree.find(key)['desc_en']=en

# Explanatory text describes each programme's political bargain rather than
# treating all branches as interchangeable factory ladders.
CONTEXT={
('KAZ','entry'):('Независимость уже существует, но учреждения и связи остаются разобщёнными. Общая служба должна заменить чрезвычайный сбор средств и личное покровительство.','Independence already exists, but institutions and connections remain fragmented. Common services must replace emergency levies and personal patronage.'),
('KAZ','service'):('Ежедневная работа республики требует подготовленных служащих и доступного образования. Общество должно видеть результат съезда за пределами заседаний.','Daily republican government needs trained officials and accessible education. Society must see the congress’s results beyond its meetings.'),
('KAZ','constitution'):('Законность укрепляет доверие разных общин, но запрещает центру обходить местные гарантии ради быстрого приказа. Суд и выборное управление делают этот компромисс устойчивым.','Legality builds trust among communities but prevents the centre from bypassing local guarantees for a quick order. Courts and elected government make this compromise durable.'),
('KAZ','land'):('Кооперация и земельный компромисс расширяют поддержку образования и переработки. Это договорная реформа, а не принудительная коллективизация; внутренний капитал остаётся ограниченным.','Cooperation and a land compromise broaden support for education and processing. This is negotiated reform rather than forced collectivisation; domestic capital remains limited.'),
('KAZ','mandate'):('Чрезвычайный мандат концентрирует оборонные заказы и охрану узлов. Гражданские силы платят ограничением своего влияния; после организации армии вопрос о возврате полномочий останется открытым.','Emergency authority concentrates defence orders and junction security. Civilians pay through reduced influence; after the army is organised, returning the mandate remains an open question.'),
('KAZ','industry'):('Известные недра ещё не образуют собственной промышленной цепочки. Сначала нужны материалы исследований и дороги, затем переработка, инструмент и машиностроение. Проект не создаёт вымышленных запасов ресурсов.','Known deposits do not yet form a domestic industrial chain. Records and roads come first, followed by processing, tools and machine building. This project does not invent resource reserves.'),
('KAZ','diverse'):('Разделённые заказы дороже и медленнее исключительного контракта. Зато собственный институт и совместимость оборудования уменьшают зависимость от одного иностранного заказчика.','Divided orders cost more and take longer than an exclusive contract. A domestic institute and equipment compatibility reduce dependence on one foreign customer.'),
('KAZ','caspian'):('Морская программа требует действительно проверенного Каспийского пути, контролируемого побережья и согласия Кавказа. Она дополняет внутреннюю дорогу; отказ партнёра не закрывает сухопутную альтернативу.','The maritime programme requires a verified Caspian route, controlled coastline and Caucasian consent. It complements the inland road; a partner’s refusal leaves the overland alternative open.'),
('KAZ','siberia'):('Сухопутная связь с независимой Сибирью остаётся полноценной альтернативой морской программе. Военный договор требует встречного согласия и не объединяет страны автоматически.','An overland connection to independent Siberia is a complete alternative to the maritime programme. Military cooperation requires a reply and never automatically merges the countries.'),
('KAZ','army'):('Республика должна содержать армию на огромных расстояниях. Младшие командиры, ремонт и снабжение предшествуют моторизации; собственная техника требует работающих мастерских.','The republic must maintain an army across great distances. Junior officers, repairs and supply precede motorisation; domestic equipment requires functioning workshops.'),
('CAU','compact'):('Федерация сохраняет страну через права субъектов и согласованный бюджет. Устойчивое согласие дороже быстрого приказа, зато транзит не должен обогащать только центральное ведомство.','The federation holds together through constituent rights and an agreed budget. Durable consent costs more time than a quick order; transit must not enrich only the central office.'),
('CAU','central'):('Единые армия, таможня и управление дорогами ускоряют координацию. Региональные элиты требуют гарантий; централизация не означает неизбежного распада, но имеет политическую цену.','A common army, customs service and roads administration accelerate coordination. Regional elites demand guarantees; centralisation has a political cost without making collapse inevitable.'),
('CAU','neutral'):('Правила прохода не должны превращать федерацию в чужую базу. Отказ от иностранных гарнизонов требует собственной охраны и заранее установленных правил на случай чужой войны.','Passage rules must not turn the federation into somebody else’s base. Rejecting foreign garrisons requires our own security forces and rules for another country’s war.'),
('SIB','civil'):('Сибирская государственность должна обслуживать жителей, а не оставаться временным военным штабом. Региональное согласие укрепляет доверие, но внешние коридоры зависят от самостоятельного решения соседей.','Siberian statehood must serve its residents rather than remain a temporary headquarters. Regional consent builds trust, while external corridors depend on neighbours’ independent decisions.'),
('SIB','russia'):('Общее гражданство не оправдывает нового похода. Конференция предлагает договор согласившимся республикам, а их отказ сохраняет независимость без автоматической войны.','Common citizenship does not justify another march. The conference offers a treaty to willing republics; refusal preserves their independence without automatic war.'),
('SIB','directory'):('Командование охраняет узлы и быстро восстанавливает магистраль. Приоритет приказа и военных мастерских ослабляет гражданскую легитимность и доверие регионов.','Command guards junctions and rapidly restores the trunk line. Military orders and workshops take priority at the cost of civilian legitimacy and regional trust.'),
('SOV','recovery'):('Гражданская война уже закончилась. Жизнеспособное государство требует хлеба, товаров и выполнимого плана; внутреннее восстановление ограничивает ресурсы для внешней революции.','The civil war has already ended. A viable state needs bread, goods and a workable plan; domestic recovery limits resources for revolution abroad.'),
('SOV','treaty'):('Признание отдельного правительства должно иметь практический смысл. Торговля и оборона предлагаются независимым соседям, которые могут сохранить нейтралитет или отказаться.','Recognising a separate government must have practical meaning. Trade and defence are offered to independent neighbours, who may stay neutral or refuse.'),
('SOV','pressure'):('Революционное давление развивает армию и внешние связи движений, но отнимает ресурсы у внутреннего восстановления. Соседи получают основания готовить оборонительные соглашения.','Revolutionary pressure strengthens the army and foreign movements but diverts resources from domestic recovery. Neighbours gain reasons to prepare defensive agreements.'),
('NAF','neutral'):('Нейтралитет — активная политика защиты независимости. Собственные учебные части и охрана торговли должны заменить иностранные базы, а не открыть очередной чужой фронт.','Neutrality actively defends independence. Domestic training units and trade security must replace foreign bases rather than open another foreign front.'),
('NAF','citizen'):('Общая победа должна стать общим гражданством, школами и федеральным бюджетом. Равноправие участников требует согласования, но делает государство повседневным опытом жителей.','Common victory must become common citizenship, schools and a federal budget. Equality among members requires agreement but makes the state part of everyday life.'),
('NAF','voice'):('Посредничество и подготовка специалистов дают независимым странам партнёра без новой опеки. Просьба о военной помощи позднее проверит пределы нашего нейтралитета.','Mediation and specialist training offer independent states a partner without new tutelage. A later request for military aid will test the limits of our neutrality.'),
('CMT','residents'):('Представительство жителей заменяет чрезвычайное управление. Переход защищает труд и гражданские права, но требует договориться с подрядчиками, от которых пока зависит занятость.','Resident representation replaces emergency administration. The transition protects labour and civil rights but requires terms with contractors who still provide employment.'),
('CMT','board'):('Долгий контракт быстро возвращает производство и защищает коридоры. Корпоративный кабинет сохраняет конфликт между прибылью поставщиков и представительством населения.','A long contract quickly restores production and protects corridors. Corporate government preserves the conflict between suppliers’ profits and popular representation.'),
('CMT','patrons'):('Старые обязательства не исчезают с окончанием войны. Переговоры о новой внешней гарантии могут дать безопасность, но не должны скрывать цену самостоятельности.','Old obligations do not disappear when war ends. Negotiating a new foreign guarantee may bring security but must expose the cost to autonomy.'),
('MEX','law'):('Предсказуемые сроки пересмотра защищают труд, собственность и самостоятельность. Контроль возвращается медленнее, зато нефтяной спор получает договорную развязку с реальным правом США отказать.','Predictable revision schedules protect labour, property and independence. Control returns more slowly, while the oil dispute gains a negotiated outcome that the United States may refuse.'),
('MEX','oil'):('Доход от нефти должен стать переработкой и местными кадрами. Компенсационные переговоры позволяют отстаивать контроль без обязательной войны; их исход зависит и от США.','Oil income must become refining and local expertise. Compensation negotiations defend control without inevitable war; their outcome also depends on the United States.'),
('MEX','officers'):('Общая армия защищает дороги и промыслы быстрее разрозненных гарнизонов. Военный переход имеет цену для гражданской политики и должен закончиться явным выбором о возврате власти.','A common army guards roads and oilfields faster than political garrisons. Military transition costs civilian influence and must end in an explicit choice about returning power.'),
('BRA','republic'):('Экспортная выручка не заменяет общего государства. Выборные правила и гражданское управление должны связать рынки и довести федеральную власть до провинций.','Export income does not replace a common state. Electoral rules and civilian administration must connect markets and carry federal government into the provinces.'),
('BRA','officers'):('Офицерская модернизация концентрирует инфраструктуру и промышленный заказ. Скорость общего плана оплачивается риском постоянной военной власти; переходный кабинет должен решить, выполнено ли обещание.','Officer-led modernisation concentrates infrastructure and industrial orders. The common plan’s speed risks permanent military government; the transitional cabinet must answer for its promise.'),
('BRA','federal'):('Гарантии региональных правительств позволяют строить общие дороги без единоличного центра. Согласие укрепляет федерацию, но замедляет единую мобилизацию.','Regional guarantees allow common roads without personal central rule. Consent strengthens the federation but slows unified mobilisation.'),
('ARG','industry'):('Старый покупатель больше не гарантирует доход. Переработка, машины и торговые верфи превращают экспортную выручку в самостоятельную цепочку ценой краткосрочного потребления.','The old buyer no longer guarantees income. Processing, machines and merchant yards turn export revenue into an independent chain at the cost of short-term consumption.'),
('ARG','league'):('Конференция должна оставлять каждому участнику голос и право отказа. Арбитраж и добровольная безопасность противопоставляют сотрудничество опеке сильнейшего.','The conference must preserve every participant’s voice and right to refuse. Arbitration and voluntary security offer cooperation instead of tutelage by the strongest.'),
('ARG','atlantic'):('Морской заказ быстро усиливает внешнюю роль, но забирает ресурсы у внутренней промышленной программы. Влияние через порты не делает войну с Бразилией обязательной.','Naval orders quickly strengthen external influence but take resources from domestic industry. Port-based influence does not make war with Brazil inevitable.'),
('CHI','agreement'):('Объединение требует согласия региональных правительств. Общие пошлины, снабжение и дипломатия создают республику без обязательного подчинения одному генералу.','Union requires regional governments’ consent. Common customs, supplies and diplomacy build a republic without compulsory obedience to a single general.'),
('CHI','army'):('Единый штаб прекращает независимые каналы оружия, но поход создаёт новые обязательства и конфликты. После военного приоритета остаётся выбор гражданского правительства или постоянного командования.','A common staff ends independent arms channels, but campaigning creates new obligations and conflicts. Military priority must lead to a choice between civilian government and permanent command.'),
('CHI','land'):('Сельские движения дают государству поддержку и внутреннее снабжение. Местная реформа собственности может закончиться социальной республикой или революционной властью — это разные решения.','Rural movements provide support and domestic supply. Local property reform can lead to a social republic or revolutionary government: these are different decisions.'),
}
import re
for tree in [k,c,s,v,n,m,mx,b,ar,ch]:
    for node in tree.nodes:
        key=node['id'][len(tree.prefix):];stem=re.sub(r'\d+$','',key)
        context=CONTEXT.get((tree.tag,stem))
        if context:
            node['desc_ru']=node['ru']+'. '+context[0]
            node['desc_en']=node['en']+'. '+context[1]
        for lang in ['ru','en']:
            if node.get('details_'+lang):node['desc_'+lang]=node.get('desc_'+lang,node[lang])+ ' '+node['details_'+lang]
            if node.get('final_desc_'+lang):node['desc_'+lang]=node['final_desc_'+lang]
    for ident,descriptions in national_descriptions(tree.tag,tree.nodes).items():
        for node in tree.nodes:
            if node['id']==ident:node['desc_ru'],node['desc_en']=descriptions
    tree.save()

write('common/ideas/aof_v03_nations.txt','ideas = { country = {\n'+''.join(f' {key} = {{ picture = {idea_picture(key)} allowed = {{ always = yes }} allowed_civil_war = {{ always = yes }} removal_cost = -1 modifier = {{ {mods} }} }}\n' for key,mods in IDEAS.items())+'} }\n')
event_ids=[re.search(r'country_event = \{ id = (aof_nations\.\d+)',body).group(1) for body in EVENTS]
assert len(event_ids)==len(set(event_ids)), 'Duplicate generated national event IDs'
write('events/aof_v03_nations.txt','add_namespace = aof_nations\n'+''.join(EVENTS))
localize('aof_v03_nations',LOC)
if __name__=='__main__':print(COUNTS,'total',sum(COUNTS.values()),'ideas',len(IDEAS),'events',len(EVENTS))
