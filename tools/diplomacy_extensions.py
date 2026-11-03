"""Reciprocal settlements for the national DesignBook routes; authoring only."""

def register(event, offer, notify, loc, coop, pressure):
    loc['aof_v03_far_eastern_rights']=('Расширение дальневосточных полномочий','Expanded Far Eastern powers')
    pact='diplomatic_relation = { country = FROM relation = non_aggression_pact active = yes }'
    full='is_subject = no has_war = no NOT = { any_owned_state = { NOT = { is_controlled_by = PREV } } }'
    pairs='''OR = {
      AND = { OR = { tag = PRC tag = GXC tag = YUN tag = SHX tag = XSM tag = SIK } FROM = { tag = CHI } }
      AND = { OR = { tag = FER tag = SOV } FROM = { tag = SIB } }
      AND = { OR = { tag = KAZ tag = SIB tag = FER } FROM = { tag = SOV } }
    }'''
    union_guard=full+' FROM = { '+full+' } is_in_faction_with = FROM '+pairs
    event(160,('Предложение общей федерации','An offer of a common federation'),
      ('Партнёр по оборонному союзу предлагает объединить территории и учреждения. Принятие завершит отдельное существование нашей страны: земли и войска перейдут инициатору. Игрок этой страны потеряет отдельное управление. Национальные права передаются только на наших собственных национальных землях. Можно вместо объединения сохранить союз самостоятельных государств.',
       'Our defence partner proposes unifying territory and institutions. Acceptance ends our separate country: our lands and forces pass to the proposer. A player governing this country loses separate control. New cores apply only to our owned core territory. Alternatively, retain a union of sovereign states.'),[
      (('Принять объединение и передать отдельное управление.','Accept union and relinquish separate control.'),
       'every_owned_state = { limit = { is_core_of = ROOT } add_core_of = FROM } FROM = { set_country_flag = aof_voluntary_union_accepted set_cosmetic_tag = aof_voluntary_federation annex_country = { target = ROOT transfer_troops = yes } }',1,union_guard),
      (('Сохранить союз самостоятельных государств.','Retain a union of sovereign states.'),
       coop+' '+pact+' set_country_flag = aof_voluntary_union_limited FROM = { set_country_flag = aof_voluntary_union_limited } '+notify(202),49,''),
      (('Не менять существующие договоры.','Keep our existing treaties.'),
       'FROM = { set_country_flag = aof_voluntary_union_refused } '+notify(203),50,'')],union_guard)
    for f in ['', 'democratic','neutrality','communism','fascism','aof_social_democracy','aof_conservatism']:
        key='aof_voluntary_federation'+('_'+f if f else '')
        loc[key]=('Федерация республик','Federation of Republics')
        loc[key+'_DEF']=('Федерация республик','the Federation of Republics')
        loc[key+'_ADJ']=('Федеративн.','Federal')

    event(170,('Просьба о внешней защите','A request for external protection'),
      ('Коммерческое государство предлагает новые отношения защиты. Мы можем предложить протекторат, гарантировать независимость или отказаться. Передача самостоятельности требует отдельного окончательного согласия его правительства.',
       'The commercial state seeks a new protection agreement. Offer a protectorate, guarantee independence, or decline. Relinquishing sovereignty requires its government’s separate final consent.'),[
      (('Предложить протекторат на окончательное утверждение.','Submit a protectorate for final approval.'),
       'add_political_power = -35 set_country_flag = aof_cmt_protectorate_authorized CMT = { country_event = { id = aof_diplomacy.172 days = 1 } }',20,'is_subject = no CMT = { is_subject = no has_war = no } has_war = no'),
      (('Дать гарантию без подчинения.','Guarantee independence without subordination.'),
       'add_political_power = -20 diplomatic_relation = { country = CMT relation = guarantee active = yes } CMT = { set_country_flag = aof_cmt_protection_limited clr_country_flag = aof_cmt_protection_refused } '+coop+' '+notify(202),55,''),
      (('Не принимать новых обязательств.','Decline new obligations.'),
       'CMT = { set_country_flag = aof_cmt_protection_refused } '+notify(203),25,'')],
      'tag = USA is_subject = no FROM = { tag = CMT exists = yes is_subject = no } NOT = { has_war_with = FROM }')
    event(172,('Последнее слово принадлежит нашему правительству','Our government has the final say'),
      ('США согласились предложить внешнюю защиту. Протекторат сохранит нашу страну, но передаст часть внешней самостоятельности американскому покровителю. Можно утвердить только гарантию независимости или оставить собственную оборону. Никакое решение иностранного кабинета не заменяет нашего согласия.',
       'The United States offers external protection. A protectorate preserves our country but transfers part of its external independence to the American patron. We can approve only an independence guarantee, or retain our own defence. A foreign cabinet’s decision cannot substitute for our consent.'),[
      (('Утвердить протекторат: мы станем зависимым государством.','Approve the protectorate: become a subject.'),
       'USA = { set_autonomy = { target = CMT autonomy_state = autonomy_puppet end_wars = no end_civil_wars = no } } if = { limit = { is_subject_of = USA } set_country_flag = aof_cmt_protection_accepted clr_country_flag = aof_cmt_protection_refused USA = { set_country_flag = aof_cmt_protection_accepted } '+notify(201)+' } else = { set_country_flag = aof_cmt_protection_refused '+notify(203)+' }',20,'is_subject = no has_war = no USA = { is_subject = no has_war = no }'),
      (('Принять только гарантию независимости.','Accept only the independence guarantee.'),
       'USA = { diplomatic_relation = { country = CMT relation = guarantee active = yes } } set_country_flag = aof_cmt_protection_limited clr_country_flag = aof_cmt_protection_refused '+notify(202),60,''),
      (('Сохранить самостоятельную оборону.','Retain independent defence.'),
       'set_country_flag = aof_cmt_protection_refused '+notify(203),20,'')],
      'tag = CMT is_subject = no FROM = { tag = USA exists = yes has_country_flag = aof_cmt_protectorate_authorized } NOT = { has_war_with = FROM }')
    event(171,('Заказы после окончания войны','Orders after the war'),
      ('Коммерческая администрация предлагает продолжить поставки уже для мирного рынка. Долгий заказ требует расходов американского бюджета; короткий контракт оставляет больше риска поставщику. Это закупки, а не иностранная опека.',
       'The commercial administration offers continued supply for the civilian market. A long order costs the American budget; a short contract leaves more risk with the supplier. This is procurement, not foreign tutelage.'),[
      (('Утвердить двухлетний заказ.','Approve a two-year order.'),
       'add_political_power = -40 CMT = { set_country_flag = aof_cmt_procurement_accepted clr_country_flag = aof_cmt_procurement_refused add_timed_idea = { idea = aof_v03_compensated_trade days = 730 } } '+coop+' '+notify(201),45,''),
      (('Предложить только переходный годовой контракт.','Offer only a one-year transition contract.'),
       'add_political_power = -20 CMT = { set_country_flag = aof_cmt_procurement_limited clr_country_flag = aof_cmt_procurement_refused add_timed_idea = { idea = aof_v03_compensated_trade days = 365 } } '+coop+' '+notify(202),35,''),
      (('Отказаться от нового заказа.','Decline the new order.'),
       'CMT = { set_country_flag = aof_cmt_procurement_refused } '+notify(203),20,'')],
      'tag = USA FROM = { tag = CMT exists = yes } NOT = { has_war_with = FROM }')
    event(180,('Посредник по вопросу военного устава','A mediator for the wartime charter'),
      ('Североафриканское содружество предлагает посредничество между администрацией, жителями и поставщиками. Посредник не назначает нам правительство. Принятие открывает совместную подготовку мирных производств; отказ оставляет внутренний спор за нашими учреждениями.',
       'The North African Commonwealth offers mediation between administrators, residents and suppliers. The mediator does not appoint our government. Acceptance opens joint preparation for civilian production; rejection leaves the dispute with our own institutions.'),[
      (('Принять посредничество и обмен специалистами.','Accept mediation and exchange of specialists.'),
       'add_stability = 0.04 set_country_flag = aof_naf_mediation_accepted FROM = { set_country_flag = aof_naf_mediation_accepted add_political_power = 20 } '+coop+' '+notify(201),65,''),
      (('Провести переговоры своими силами.','Conduct talks through our own institutions.'),
       'set_country_flag = aof_naf_mediation_refused FROM = { set_country_flag = aof_naf_mediation_refused } '+notify(203),35,'')],
      'tag = CMT FROM = { tag = NAF exists = yes } NOT = { has_war_with = FROM }')
    event(181,('Предложение помощи Содружества','An offer of Commonwealth assistance'),
      ('Содружество предлагает помощь стране, уже участвующей в африканской войне. Мы определим, нужна ли гражданская поддержка или оружие; затем его кабинет решит, может ли выполнить запрос. Оружие и гарантии означают иной внешнеполитический выбор, чем нейтральное посредничество.',
       'The Commonwealth offers help to a country already involved in an African war. We specify civilian assistance or arms; its cabinet then decides whether it can fulfil the request. Arms and guarantees represent a different foreign policy from neutral mediation.'),[
      (('Запросить гражданскую помощь.','Request civilian assistance.'),
       'set_country_flag = aof_naf_civil_aid_requested clr_country_flag = aof_naf_military_aid_requested NAF = { country_event = { id = aof_nations.30 days = 1 } }',60,''),
      (('Запросить оружие и политическую защиту.','Request arms and political protection.'),
       'set_country_flag = aof_naf_military_aid_requested clr_country_flag = aof_naf_civil_aid_requested NAF = { country_event = { id = aof_nations.30 days = 1 } }',30,''),
      (('Отказаться от внешней помощи.','Decline outside assistance.'),notify(203),10,'')],
      'has_war = yes capital_scope = { is_on_continent = africa } FROM = { tag = NAF exists = yes } NOT = { has_war_with = FROM }')
    event(182,('Посредничество соседней республики','Mediation by the neighbouring republic'),
      ('Алаш предлагает площадку для переговоров о будущем Туркестана. Сохранение общих учреждений и договорённый раздел остаются нашим собственным выбором. Сосед может поддержать переговоры, но не разделить страну своим указом.',
       'Alash offers a forum for talks on Turkestan’s future. Preserving common institutions or agreeing a separation remains our own choice. A neighbour can support talks, but cannot partition our country by decree.'),[
      (('Принять площадку и созвать собственных представителей.','Accept the forum and convene our representatives.'),
       'add_stability = 0.04 set_country_flag = aof_turkestan_mediation_accepted FROM = { set_country_flag = aof_turkestan_mediation_accepted add_political_power = 20 } country_event = { id = aof_v03_regions.33 days = 1 } '+coop+' '+notify(201),65,''),
      (('Обсудить будущее без внешнего посредника.','Discuss our future without an outside mediator.'),
       'set_country_flag = aof_turkestan_mediation_refused FROM = { set_country_flag = aof_turkestan_mediation_refused } '+notify(203),35,'')],
      'tag = TRK is_subject = no has_war = no FROM = { tag = KAZ exists = yes } NOT = { has_war_with = FROM }')
    event(190,('Сибирский договор и японская гарантия','Siberian trade and Japanese protection'),
      ('Сибирь предлагает торговое сотрудничество и поддерживает расширение местных полномочий. Пока действует японская опека, изменение её условий требует ответа Японии. Независимое правительство может заключить договор самостоятельно.',
       'Siberia offers trade cooperation and supports wider local powers. While Japanese protection continues, changing its terms requires Japan’s response. An independent government can conclude the treaty itself.'),[
      (('Согласиться на торговлю и запросить пересмотр опеки.','Accept trade and request revised protection.'),
       'if = { limit = { is_subject_of = JAP } JAP = { country_event = { id = aof_diplomacy.191 days = 1 } } } else = { set_country_flag = aof_siberian_autonomy_accepted SIB = { set_country_flag = aof_siberian_autonomy_accepted add_political_power = 20 } '+coop+' '+notify(201)+' }',65,'OR = { is_subject = no is_subject_of = JAP }'),
      (('Сохранить прежние условия.','Keep the current arrangements.'),
       'SIB = { set_country_flag = aof_siberian_autonomy_refused } '+notify(203),35,'')],
      'tag = FER has_war = no FROM = { tag = SIB exists = yes } NOT = { has_war_with = FROM }')
    event(191,('Цена дальневосточной самостоятельности','The price of Far Eastern self-government'),
      ('Дальневосточное правительство просит согласовать торговлю с Сибирью и пересмотреть японскую гарантию. Можно признать самостоятельность, расширить местные права или оставить военную опеку. Независимость не означает передачи страны Сибири.',
       'The Far Eastern government seeks Siberian trade and revised Japanese protection. Recognise independence, expand local powers, or retain military tutelage. Independence does not transfer the country to Siberia.'),[
      (('Признать самостоятельность и сохранить торговый договор.','Recognise independence and preserve trade.'),
       'set_autonomy = { target = FER autonomy_state = autonomy_free end_wars = no end_civil_wars = no } if = { limit = { FER = { is_in_faction_with = JAP } } remove_from_faction = FER } FER = { set_country_flag = aof_siberian_autonomy_accepted } SIB = { set_country_flag = aof_siberian_autonomy_accepted } add_stability = -0.02 '+notify(201),20,''),
      (('Допустить торговлю и расширить местные полномочия.','Allow trade and expand local powers.'),
       'FER = { add_autonomy_score = { value = 150 localization = aof_v03_far_eastern_rights } } FER = { set_country_flag = aof_siberian_autonomy_limited } SIB = { set_country_flag = aof_siberian_autonomy_limited } '+notify(202),60,''),
      (('Оставить военную гарантию без изменений.','Retain the existing military guarantee.'),
       'SIB = { set_country_flag = aof_siberian_autonomy_refused } '+notify(203),20,'')],
      'tag = JAP has_war = no FROM = { tag = FER is_subject_of = JAP has_war = no } SIB = { exists = yes }')
    participant='if = { limit = { tag = BRA } FROM = { set_country_flag = aof_conference_participant_bra } } else = { FROM = { set_country_flag = aof_conference_participant_arg } }'
    event(91,('Встречное предложение равных условий','A counteroffer of equal terms'),
      ('Приглашённое правительство согласно обсуждать конференцию без признания чужого первенства. Принятие пересматривает наши двусторонние условия; другие приглашённые сохраняют собственное решение. Отказ позволяет партнёру созвать альтернативную мирную конференцию.',
       'The invited government will discuss the conference without recognising another state’s primacy. Acceptance revises our bilateral terms; other invitees retain their own decisions. Rejection lets the partner convene an alternative peaceful conference.'),[
      (('Принять равноправный формат.','Accept an equal partnership.'),
       'clr_country_flag = aof_brazil_hegemonic_conference set_country_flag = aof_conference_counteroffer_accepted FROM = { set_country_flag = aof_conference_participant clr_country_flag = aof_conference_counteroffer_pending } '+participant+' '+coop+' '+notify(201),65,''),
      (('Не пересматривать предложенные условия.','Retain our proposed terms.'),
       'FROM = { set_country_flag = aof_counterconference_mandate clr_country_flag = aof_conference_counteroffer_pending } '+notify(203),35,'')],
      'OR = { tag = BRA tag = ARG } FROM = { exists = yes has_country_flag = aof_conference_counteroffer_pending } NOT = { has_war_with = FROM }')
