"""Deterministic DesignBook v0.3 national campaign authoring."""
from contentlib import write, localize, render_tree, capital_building
from ideaicons import idea_picture
LOC={}; IDEAS={}; EVENTS=[]; COUNTS={}
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
    ident='aof_nations.'+str(number);LOC[ident+'.t']=(ru,en);LOC[ident+'.d']=(dr,de)
    s=f'country_event = {{ id = {ident} title = {ident}.t desc = {ident}.d picture = GFX_aof_event_kazakhstan_development is_triggered_only = yes\n'
    for i,(r,e,fx) in enumerate(options):
        key=ident+'.'+chr(97+i);LOC[key]=(r,e);s+=' option = { name = '+key+' ai_chance = { factor = 1 } '+fx+' }\n'
    EVENTS.append(s+'}\n');return 'country_event = { id = '+ident+' days = 1 }'
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
    tree.save()

write('common/ideas/aof_v03_nations.txt','ideas = { country = {\n'+''.join(f' {key} = {{ picture = {idea_picture(key)} allowed = {{ always = yes }} allowed_civil_war = {{ always = yes }} removal_cost = -1 modifier = {{ {mods} }} }}\n' for key,mods in IDEAS.items())+'} }\n')
write('events/aof_v03_nations.txt','add_namespace = aof_nations\n'+''.join(EVENTS))
localize('aof_v03_nations',LOC)
if __name__=='__main__':print(COUNTS,'total',sum(COUNTS.values()),'ideas',len(IDEAS),'events',len(EVENTS))
