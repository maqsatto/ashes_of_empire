from contentlib import write,localize,render_tree,capital_building
from ideaicons import idea_picture
LOC={}; IDEAS={}; COUNTS={}
def idea(k,ru,en,mods):
 k='aof_v03_'+k; IDEAS[k]=mods; LOC[k]=(ru,en); LOC[k+'_desc']=(ru+' — действующие национальные условия и обязательства.',en+' — current national conditions and commitments.'); return k
def add(k): return 'add_ideas = aof_v03_'+k
def timed(k,days=365): return f'add_timed_idea = {{ idea = aof_v03_{k} days = {days} }}'
def bonus(cat): return f'add_tech_bonus = {{ name = aof_v03_applied_bonus bonus = 0.5 uses = 1 category = {cat} }}'
def dip(event,target=None):
 s=f'country_event = {{ id = aof_diplomacy.{event} days = 1 }}'
 if target: s=f'{target} = {{ {s} }}'
 return f'if = {{ limit = {{ country_exists = {target} NOT = {{ has_war_with = {target} }} }} {s} }}' if target else s
LOC['aof_v03_applied_bonus']=('Прикладная программа','Applied programme')
for args in [
('usa_profit','Прибыль великого десятилетия','Profits of the Great Decade','production_speed_buildings_factor = 0.08'),
('usa_contracts','Контракты уходящей войны','Contracts of the Departing War','consumer_goods_factor = 0.05'),
('usa_universities','Университеты нового мира','Universities of the New World','research_speed_factor = 0.05'),
('usa_credit','Республика кредиторов','Republic of Creditors','production_factory_max_efficiency_factor = 0.06 stability_factor = -0.03'),
('usa_welfare','Внутренний гражданский заказ','Domestic Civilian Orders','production_speed_industrial_complex_factor = 0.12 production_speed_arms_factory_factor = -0.08'),
('usa_labor','Договор с рабочими','Labour Compact','stability_factor = 0.08'),
('usa_antitrust','Роспуск крупных объединений','Breaking Up the Trusts','production_factory_max_efficiency_factor = -0.08 political_power_gain = 0.15'),
('usa_business','Социальный договор корпораций','Corporate Social Compact','production_factory_max_efficiency_factor = 0.08 political_power_gain = -0.10'),
('usa_oceans','Порядок двух океанов','Order of Two Oceans','industrial_capacity_dockyard = 0.12 production_speed_arms_factory_factor = -0.05'),
('usa_tutelage','Доктрина опеки','Doctrine of Tutelage','war_support_factor = 0.08 stability_factor = -0.04'),
('usa_tanks','Серийное танкостроение','Serial Tank Manufacture','production_factory_max_efficiency_factor = 0.05'),
('usa_repair','Ремонтные службы','Repair Services','supply_consumption_factor = -0.06'),
('usa_convoys','Охрана океанских путей','Ocean Route Protection','industrial_capacity_dockyard = 0.06'),
('usa_project','Крупный лабораторный заказ','Major Laboratory Order','research_speed_factor = 0.03 consumer_goods_factor = 0.03'),
('jap_labs','Лаборатории империи','Laboratories of the Empire','research_speed_factor = 0.05'),
('jap_obligations','Обязательства перед протекторатами','Protectorate Commitments','consumer_goods_factor = 0.04'),
('jap_commands','Самостоятельность полевых командований','Independent Field Commands','political_power_gain = -0.15 war_support_factor = 0.05'),
('jap_treaty','Договорная сфера','Treaty Sphere','stability_factor = 0.08 production_speed_arms_factory_factor = -0.05'),
('jap_land','Материковая ставка','Continental Commitment','army_org_factor = 0.07 industrial_capacity_dockyard = -0.12 consumer_goods_factor = 0.03'),
('jap_sea','Тихоокеанский поворот','Pacific Turn','industrial_capacity_dockyard = 0.12 production_speed_arms_factory_factor = -0.10'),
('jap_logistics','Материковые пути снабжения','Continental Supply Routes','supply_consumption_factor = -0.08'),
('jap_garrison','Обязательства материковых гарнизонов','Continental Garrison Commitments','consumer_goods_factor = 0.04 stability_factor = -0.03'),
('jap_pressure','Сохранить поддержку группировок','Retain Armed Clients','war_support_factor = 0.08 stability_factor = -0.04'),
('jap_shipping','Флот снабжения','Supply Fleet','industrial_capacity_dockyard = 0.06 supply_consumption_factor = -0.03'),
('jap_engineers','Следующее поколение инженеров','Next Generation of Engineers','research_speed_factor = 0.03'),
('jap_inquiry','Смешанная комиссия','Joint Inquiry','political_power_gain = -0.05 stability_factor = 0.03'),
]: idea(*args)

def government(family,elections=True):
 families=['democratic','communism','fascism','neutrality','aof_social_democracy','aof_conservatism']
 pops=' '.join(k+' = '+str(70 if k==family else 6) for k in families)
 return 'set_popularities = { '+pops+' } set_politics = { ruling_party = '+family+' elections_allowed = '+('yes' if elections else 'no')+' }'

def tree(tag):
 nodes=[]; prefix='aof_v03_'+tag.lower()+'_'
 def node(k,ru,en,x,y,effect,pre=None,ex=None,cost=5,desc=None,available=None):
  n=dict(id=prefix+k,ru=ru,en=en,x=x,y=y,effect=effect,cost=cost)
  if pre:n['pre']=[([prefix+t for t in p] if isinstance(p,list) else prefix+p) for p in pre]
  if ex:n['excludes']=[prefix+t for t in ex]
  if available:n['available']=available
  n['desc_ru']=desc[0] if desc else ru+'. Завершение программы меняет действующие условия; точные выгоды и издержки приведены ниже.'
  n['desc_en']=desc[1] if desc else en+'. Completing this programme changes national conditions; benefits and costs are listed below.'
  nodes.append(n)
 def chain(items,x,start,pre=None):
  last=pre
  for i,(k,ru,en,e) in enumerate(items):node(k,ru,en,x,start+i,e,[last] if last else None);last=k
  return last
 if tag=='USA':
  chain([('order','Последний военный заказ','The Last War Order','add_political_power = 35'),('audit','Проверить европейские обязательства','Audit European Obligations','add_political_power = 40'),('commission','Комиссия по мирной перестройке','Peace Conversion Commission','remove_ideas = aof_v03_usa_contracts'),('profits','Кому принадлежит прибыль войны?','Who Owns the Profits of War?','add_stability = 0.03')],8,0)
  # The initial political choice takes 84 days, while applied programmes are open immediately.
  for n in nodes:n['cost']=3
  roots=['credit','welfare','oceans']
  for k,ru,en,x,e in [('credit','Неприкосновенность внешних договоров','Sanctity of Foreign Contracts',2,add('usa_credit')+' add_political_power = -50'),('welfare','Прибыль должна работать дома','Profits Must Work at Home',8,add('usa_welfare')),('oceans','Наш предел — Западное полушарие','Our Limit Is the Western Hemisphere',14,add('usa_oceans'))]:node(k,ru,en,x,4,e,['profits'],[t for t in roots if t!=k])
  chain([('export','Экспортировать не только товары','Export More Than Goods',dip(21,'KAZ')),('debts','Долги в обмен на восстановление','Debts for Reconstruction',capital_building()),('standards','Стандарты американского производства','American Production Standards',bonus('industry')),('long_contracts','Страна долгих контрактов','Country of Long Contracts','add_political_power = 100')],2,5,'credit')
  node('flag','Договор важнее флага','The Treaty Before the Flag',0,9,'add_stability = 0.05 add_political_power = 60',['long_contracts'],['investments'])
  node('investments','Защита вложений — государственный интерес','Investment Protection Is a State Interest',4,9,'add_war_support = 0.08 add_stability = -0.04 '+dip(11,'MEX'),['long_contracts'],['flag'])
  chain([('civilian','Гражданский заказ вместо военного','Civilian Orders Replace War Orders',capital_building()),('labor','Договор с рабочими организациями','Compact with Labour Organisations',add('usa_labor')+' add_political_power = -50'),('education','Университеты для всей страны','Universities for the Whole Country','add_research_slot = 1'),('prosperity','Достаток без чужой войны','Prosperity Without Foreign War','add_stability = 0.05 add_war_support = -0.03')],8,5,'welfare')
  node('trusts','Разделить крупные объединения','Break Up the Trusts',6,9,timed('usa_antitrust',540)+' add_political_power = 75',['prosperity'],['business'])
  node('business','Социальный договор с крупным бизнесом','A Social Compact with Big Business',10,9,add('usa_business'),['prosperity'],['trusts'])
  chain([('coasts','Защитить оба побережья','Defend Both Coasts','navy_experience = 25'),('conference','Американская морская конференция','American Maritime Conference',dip(120,'MEX')+' add_political_power = -35')],14,5,'oceans')
  node('neighbors','Соседи, а не передовые базы','Neighbours and Partners',12,7,'add_stability = 0.05 '+dip(11,'MEX'),['conference'],['tutelage'])
  node('tutelage','Доктрина опеки','Doctrine of Tutelage',16,7,add('usa_tutelage')+' add_political_power = 50',['conference'],['neighbors'])
  node('continent','Континент, не зависящий от Европы','A Continent Independent of Europe',14,8,capital_building('infrastructure')+' add_political_power = 75',[['neighbors','tutelage']])
  chain([('labs','Открытые двери лабораторий','Open Laboratory Doors',bonus('electronics')),('production','Перевести открытия в производство','Bring Discoveries into Production',bonus('industry')),('machine','Станок должен повторять деталь','A Machine Must Repeat the Part',bonus('industry')),('school','Национальная инженерная школа','National Engineering School','add_research_slot = 1 country_event = { id = aof_v03_pacific.1 days = 30 }')],20,0)
  chain([('tank','Американский лёгкий танк','American Light Tank',bonus('armor')+' army_experience = 15'),('trials','Испытания без парадных условий','Trials Without Parade Conditions','army_experience = 25'),('repair','Ремонт важнее рекорда','Repair Before Records',add('usa_repair')),('series','Не тысяча прототипов, а серия','Series Production, Not a Thousand Prototypes',add('usa_tanks')),('motor_age','Армия автомобильного века','Army of the Motor Age',bonus('motorized_equipment')+' army_experience = 30')],24,0)
  node('ports','Порты двух океанов','Ports of Two Oceans',28,0,'navy_experience = 15')
  node('routes','Удержать путь','Hold the Route',27,1,add('usa_convoys'),['ports'],['project'])
  node('project','Доставить силу','Deliver Power',29,1,bonus('naval_equipment')+' navy_experience = 25',['ports'],['routes'])
  node('exercises','Учения за пределами базы','Exercises Beyond the Base',28,2,'navy_experience = 35',[['routes','project']])
 else:
  chain([('demands','Свести требования материка','Reconcile Continental Demands','add_political_power = 35'),('treaties','Две зависимости — два договора','Two Dependencies, Two Treaties','add_stability = 0.02'),('voice','Кто говорит от имени империи?','Who Speaks for the Empire?','add_political_power = 40'),('policy','Единая внешняя политика','A Unified Foreign Policy','country_event = { id = aof_v03_pacific.2 days = 14 }')],8,0)
  for n in nodes:n['cost']=3
  roots=['cabinet','mandate','pacific']
  for k,ru,en,x,e in [('cabinet','Гражданский кабинет определяет курс','The Civilian Cabinet Sets the Course',2,add('jap_treaty')+' remove_ideas = aof_v03_jap_commands'),('mandate','Полевое командование получает мандат','A Mandate for Field Command',8,add('jap_land')+' add_stability = -0.03'),('pacific','Море важнее глубины фронта','The Sea Before the Depth of the Front',14,add('jap_sea')+' remove_ideas = aof_v03_jap_commands')]:node(k,ru,en,x,4,e,['policy'],[t for t in roots if t!=k])
  chain([('local','Равный голос местных администраций','An Equal Voice for Local Administrations','add_political_power = -50 add_stability = 0.04'),('vlad','Пересмотреть договор с Владивостоком','Revise the Vladivostok Treaty',dip(41,'FER')),('man_convention','Маньчжурская промышленная конвенция','Manchurian Industrial Convention',dip(51,'MAN')),('intermediaries','Договор с китайскими посредниками','Treaty with Chinese Intermediaries','add_political_power = 50')],2,5,'cabinet')
  node('end_support','Прекратить поддержку вооружённых групп','End Support for Armed Groups',0,9,'add_stability = 0.05 add_war_support = -0.05',['intermediaries'],['pressure'])
  node('pressure','Сохранить давление','Maintain Pressure',4,9,add('jap_pressure'),['intermediaries'],['end_support'])
  node('sphere','Сфера, которой выгодно существовать','A Sphere Worth Maintaining',2,10,'remove_ideas = aof_v03_jap_obligations add_political_power = 75',[['end_support','pressure']])
  chain([('man_army','Маньчжурия — основа материковой армии','Manchuria as the Base of the Continental Army',dip(51,'MAN')+' army_experience = 20'),('roads','Дороги к китайским узлам','Roads to Chinese Junctions',add('jap_logistics')),('intervene','От субсидий к прямому участию','From Subsidies to Direct Participation',add('jap_garrison')+' army_experience = 30'),('corridor','Коридор безопасности','A Security Corridor',bonus('infantry_weapons')+' add_war_support = 0.05'),('order','Новый материковый порядок','A New Continental Order',capital_building('arms_factory'))],8,5,'mandate')
  node('china_treaty','Соглашение с китайским правительством','Agreement with a Chinese Government',6,10,'remove_ideas = aof_v03_jap_garrison add_stability = 0.05 add_political_power = -75',['order'],['domination'])
  node('domination','Добиваться прямого доминирования','Pursue Direct Domination',10,10,'add_stability = -0.05 add_war_support = 0.10 if = { limit = { country_exists = CHI NOT = { has_war_with = CHI } } create_wargoal = { type = puppet_wargoal_focus target = CHI } }',['order'],['china_treaty'])
  chain([('supply','Флот снабжения, а не только боя','A Fleet for Supply as Well as Battle',add('jap_shipping')),('deck','Палуба становится аэродромом','The Deck Becomes an Airfield',bonus('naval_air')),('gateway','Владивосток как ворота, не плацдарм','Vladivostok as a Gateway',dip(41,'FER')),('indian','Индийский океан без сухопутной оккупации','The Indian Ocean Without Land Occupation','navy_experience = 35')],14,5,'pacific')
  node('maritime','Порядок морских договоров','An Order of Maritime Treaties',12,9,'if = { limit = { country_exists = USA NOT = { has_war_with = USA } } USA = { country_event = { id = aof_diplomacy.60 days = 1 } } } add_political_power = -50',['indian'],['exclusive'])
  node('exclusive','Тихоокеанская исключительность','Pacific Exclusivity',16,9,'add_war_support = 0.08 add_stability = -0.04 navy_experience = 35',['indian'],['maritime'])
  chain([('chairs','Пригласить кафедры','Invite Academic Departments',bonus('electronics')),('translate','Бюро технического перевода','Technical Translation Bureau',bonus('industry')),('yards','Лаборатории вместе с верфями','Laboratories Beside Shipyards',bonus('naval_equipment')),('instruments','Собственные приборы','Domestic Instruments',bonus('electronics')),('engineers','Следующее поколение инженеров','The Next Generation of Engineers',add('jap_engineers')+' add_research_slot = 1')],20,0)
  node('alash','Промышленное партнёрство с Алаш','Industrial Partnership with Alash',24,0,dip(31,'KAZ'))
 # Government changes follow explicit institutional settlements, not applied science/naval choices.
 milestones = {'USA': {'prosperity':10,'continent':11,'long_contracts':12}, 'JAP': {'sphere':13,'domination':14}}
 for n in nodes:
  short=n['id'].removeprefix(prefix)
  if short in milestones[tag]: n['effect'] += ' country_event = { id = aof_v03_pacific.'+str(milestones[tag][short])+' days = 1 }'
  if tag=='JAP' and short=='mandate': n['effect'] += ' '+government('neutrality',False)
  if tag=='JAP' and short=='china_treaty': n['effect'] = 'add_political_power = -75 if = { limit = { country_exists = CHI NOT = { has_war_with = CHI } } CHI = { country_event = { id = aof_diplomacy.150 days = 1 } } }'
 script,loc=render_tree('aof_v03_'+tag.lower(),[tag],nodes); LOC.update(loc);write('common/national_focus/aof_v03_'+tag.lower()+'.txt',script); COUNTS[tag]=len(nodes)
for t in ['USA','JAP']:tree(t)
write('common/ideas/aof_v03_pacific.txt','ideas = { country = {\n'+''.join(f'{k} = {{ picture = {idea_picture(k)} allowed = {{ always = yes }} removal_cost = -1 modifier = {{ {v} }} }}\n' for k,v in IDEAS.items())+'} }\n')
EVENTS='add_namespace = aof_v03_pacific\n'
def event(i,title,desc,options):
 global EVENTS
 p='aof_v03_pacific.'+str(i);LOC[p+'.t']=title;LOC[p+'.d']=desc
 picture={3:'GFX_aof_event_american_science',4:'GFX_aof_event_japanese_orders'}.get(i)
 pic=f' picture = {picture}' if picture else ''
 EVENTS+=f'country_event = {{ id = {p} title = {p}.t desc = {p}.d{pic} is_triggered_only = yes fire_only_once = yes\n'
 for j,(ru,en,e) in enumerate(options):
  key=p+'.'+chr(97+j);LOC[key]=(ru,en);EVENTS+=f'option = {{ name = {key} {e} }}\n'
 EVENTS+='}\n'
event(1,('Профессор хочет домой','The Professor Wants to Go Home'),('Специалист, приехавший во время войны, хочет возглавить восстанавливаемый европейский институт. Здесь уже работают его ученики. Сохранить исключительность, создать партнёрство или довериться собственной школе?','A specialist who arrived during the war wants to lead a recovering European institute. Former students already run the American laboratory. We can fund an exclusive order, build a partnership, or trust our own school.'),[('Удержать крупным заказом.','Retain the professor with a major order.','add_political_power = -75 '+timed('usa_project',540)),('Создать партнёрский институт.','Establish a partner institute.','add_political_power = -35 '+bonus('electronics')+' add_stability = 0.02'),('Назначить подготовленного ученика.','Appoint a trained successor.','add_stability = 0.04 add_political_power = 40')])
event(2,('Приказа из столицы не было','There Was No Order from the Capital'),('Поддерживаемая группировка захватила участок китайской дороги и объявила, что действует ради Японии. Армейские покровители требуют признания; гражданские чиновники опасаются эскалации. Признание не даёт нам чужую территорию.','An armed client seized a section of Chinese railway and claims to act for Japan. Army patrons demand recognition; civilian officials fear escalation. Recognition does not transfer foreign territory to us.'),[('Осудить самовольные действия.','Condemn the unauthorised action.','add_political_power = -60 add_stability = 0.03 add_war_support = -0.05'),('Добиваться смешанного расследования.','Seek a joint investigation.',timed('jap_inquiry',365)+' add_political_power = -25'),('Признать результат.','Recognise the result.','add_war_support = 0.08 add_stability = -0.04 army_experience = 20 add_named_threat = { threat = 2 name = aof_v03_pacific.2.t }')])
event(3,('Мир предъявляет счёт','Peace Presents Its Bill'),('Последняя оплаченная военная накладная лежит на столе кабинета. Деньги и специалисты остаются в стране, но прежние заказы заканчиваются. Конверсия промышленности, спор о прибыли и выбор внешних обязательств определят нашу республику. Наука, танки и флот доступны независимо от политического курса.','The last paid wartime invoice lies before the cabinet. Wealth and specialists remain, but old orders are ending. Industrial conversion, the distribution of profits and foreign commitments will shape our republic. Science, armour and naval programmes remain independent of the political course.'),[('Открыть счета мирного времени.','Open the peacetime accounts.','add_political_power = 25')])
event(4,('Два протектората, две цены','Two Protectorates, Two Prices'),('Маньчжурская администрация требует промышленных вложений, Владивосток — торгового будущего, флот — средств на морские связи, а полевые командования — свободы действий. Это разные договоры и разные общества. Кабинету предстоит выбрать устойчивую сферу, материковый мандат или морской приоритет.','The Manchurian administration needs industrial investment; Vladivostok wants a trading future; the navy needs maritime links; field commands demand freedom of action. These are distinct societies and obligations. The cabinet must choose a treaty sphere, a continental mandate or a maritime priority.'),[('Свести требования перед кабинетом.','Bring the demands before the cabinet.','add_political_power = 25')])
event(10,('Общественный договор достатка','A Social Contract for Prosperity'),('Реформы создали широкую образовательную и гражданскую базу. Сохранить социально-либеральную республику или передать мандат парламентской социал-демократии? Ни один вариант не отменяет выборы.','Reforms have broadened education and civilian prosperity. We can retain a social-liberal republic or give parliamentary social democracy a mandate. Both settlements preserve elections.'),[('Социальный либерализм и гражданские гарантии.','Social liberalism and civil guarantees.',government('democratic')+' add_stability = 0.03 set_country_flag = aof_v03_usa_social_liberal'),('Парламентский социал-демократический мандат.','A parliamentary social-democratic mandate.',government('aof_social_democracy')+' add_political_power = -35 set_country_flag = aof_v03_usa_social_democrat')])
event(11,('Пределы президентской власти','The Limits of Presidential Power'),('Полушарная стратегия требует долговременной власти, но не определяет её форму. Конституционный кабинет сохранит контроль парламента. Чрезвычайное президентское правление отменит выборы и вызовет сопротивление.','A hemispheric strategy needs lasting institutions but does not dictate their form. A constitutional cabinet retains parliamentary oversight. Emergency presidential rule suspends elections and provokes resistance.'),[('Конституционный консервативный кабинет.','A constitutional conservative cabinet.',government('aof_conservatism')+' add_stability = 0.04 set_country_flag = aof_v03_usa_constitutional_oceans'),('Чрезвычайная президентская диктатура.','An emergency presidential dictatorship.',government('neutrality',False)+' add_stability = -0.08 add_war_support = 0.06 set_country_flag = aof_v03_usa_presidential_dictatorship')])
event(12,('Кто контролирует долгие контракты?','Who Controls the Long Contracts?'),('Долгосрочные соглашения дают корпорациям общественный вес. Сохранить выборный надзор или передать управление неподотчётному корпоративному кабинету? Последнее — отдельный авторитарный выбор, а не неизбежный итог рынка.','Long contracts give corporations political weight. We can retain elected oversight or entrust power to an unaccountable corporate cabinet. Authoritarianism is a separate choice, not an inevitable consequence of markets.'),[('Договоры под надзором выборной республики.','Contracts under elected republican oversight.',government('democratic')+' add_stability = 0.03 set_country_flag = aof_v03_usa_market_republic'),('Корпоративный кабинет без парламентского вето.','A corporate cabinet without a parliamentary veto.',government('neutrality',False)+' add_stability = -0.06 add_political_power = 50 set_country_flag = aof_v03_usa_corporate_authoritarian')])
event(13,('Кабинет договорной сферы','The Cabinet of the Treaty Sphere'),('Отношения с протекторатами не заменяют внутреннюю конституцию. Стабильная договорная сфера может опираться на консервативную парламентскую преемственность либо на либеральный гражданский мандат. Монархическая форма сама по себе не отменяется.','Treaties with dependencies do not settle the domestic constitution. A treaty sphere may rest on conservative parliamentary continuity or a liberal civilian mandate. Neither option alone abolishes the monarchy.'),[('Парламентская преемственность.','Parliamentary continuity.',government('aof_conservatism')+' add_stability = 0.04 set_country_flag = aof_v03_jap_constitutional_conservative'),('Либеральный гражданский мандат.','A liberal civilian mandate.',government('democratic')+' add_political_power = 40 set_country_flag = aof_v03_jap_liberal_cabinet')])
event(14,('Мандат или национальная миссия?','A Mandate or a National Mission?'),('Прямое доминирование требует всё новых обязательств. Военное правительство может сохранить ограниченный мандат или провозгласить экспансионистскую национальную миссию, ускорив мобилизацию ценой общественной устойчивости.','Direct domination demands ever more commitments. The military government can retain a limited mandate or declare an expansionist national mission, accelerating mobilisation at the expense of social stability.'),[('Сохранить военное правление без новой доктрины.','Retain military rule without a new doctrine.',government('neutrality',False)+' add_political_power = 30'),('Экспансионистская национальная миссия.','An expansionist national mission.',government('fascism',False)+' add_war_support = 0.10 add_stability = -0.06 set_country_flag = aof_v03_jap_radical_expansion')])
write('events/aof_v03_pacific.txt',EVENTS);localize('aof_v03_pacific',LOC)
print(COUNTS,'ideas',len(IDEAS),'events',9,'loc keys',len(LOC))
