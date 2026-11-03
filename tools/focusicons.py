"""Pure, deterministic native HOI4 focus-icon selection; no I/O or artwork.

Integration: ``from focusicons import focus_icon`` then ``focus_icon(node)``.
An authored nonempty ``node['icon']`` always wins. The fallback vocabulary is
limited to twelve sprites verified in installed 1.19 interface/goals.gfx and their
DDS files. Keys/labels/effects supply hints only; no gameplay is changed.
"""
import re

ICONS = {
    'constitution': 'GFX_goal_generic_national_unity',
    'diplomacy': 'GFX_goal_generic_alliance',
    'research': 'GFX_goal_generic_scientific_exchange',
    'infrastructure': 'GFX_goal_generic_construct_infrastructure',
    'civilian': 'GFX_goal_generic_construct_civ_factory',
    'military_factory': 'GFX_goal_generic_construct_mil_factory',
    'production': 'GFX_goal_generic_production',
    'army': 'GFX_goal_generic_army_doctrines',
    'armor': 'GFX_goal_generic_army_tanks',
    'navy': 'GFX_goal_generic_navy_cruiser',
    'air': 'GFX_goal_generic_air_fighter',
    'neutrality': 'GFX_goal_generic_neutrality_focus',
}


def _has(pattern, text):
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def focus_icon(node):
    """Return an explicit icon or a semantic native icon for an authoring node.

    Labels outrank incidental reward effects: a diplomatic industrial convention
    remains a handshake, and an army school receiving a factory remains military.
    Generic descriptions are excluded because they mention unrelated subjects.
    A plain initial congress/census defaults to institutions.
    """
    if node.get('icon'):
        return node['icon']
    label = ' '.join(str(node.get(k, '')) for k in ('ru', 'en', 'text')).lower()
    ident = str(node.get('id', '')).replace('_', ' ').lower()
    effect = str(node.get('effect', '')).lower()

    # Specific policy subjects come before broad words such as school or supply.
    if _has(r'нейтрал|невмешатель|neutral|non.interference', label):
        return ICONS['neutrality']
    if _has(r'танк|брон|\barmou?r|\btank|прототип', label):
        return ICONS['armor']
    if _has(r'диплом|переговор|конвенц|партн[её]р|соглашен|договор|конференц|посредник|арбитраж|гаранти|alliance|treaty|negotiat|partner|convention|conference|mediat|arbitrat|guarantee', label):
        return ICONS['diplomacy']
    if _has(r'флот|морск|океан|порт|гаван|верф|побереж|кораб|палуб|конво|\bnaval|\bnavy|\bfleet|\bmaritime|\bsea\b|ocean|\bport\b|harbou?r|shipyard|shipbuilding|coast|convoy|\bdeck\b', label):
        return ICONS['navy']
    if _has(r'авиа|л[её]т|самол[её]т|небо|аэродром|\bair\b|aircraft|aviation|flying|\bskies\b|airfield', label):
        return ICONS['air']
    if _has(r'дорог|железнодор|инфраструкт|транспорт|соединить|электроснаб|\broad|railway|infrastructure|transport|connect|electric', label):
        return ICONS['infrastructure']
    if _has(r'арсенал|оружейн|воен.*завод|\barsenal|arms factory|military factory', label):
        return ICONS['military_factory']
    if _has(r'арм|военн|команд|гарнизон|развед|рубеж|оборон|снабжен|мобилиз|учени[яй]|\barmy|military|command|garrison|reconnaiss|frontier|defen[cs]|supply|mobilis|mobiliz|exercise|logistic', label):
        return ICONS['army']
    if _has(r'наук|исслед|уч[её]н|университет|учител|учил|школ|инженер|лаборатор|институт|прибор|кафедр|открыти|образован|техническ|\bresearch|scien|universit|teacher|school|engineer|laborator|institute|instrument|academic|discover|education|technical', label):
        return ICONS['research']
    if _has(r'производ|переработ|мастерск|серийн|серия|станок|станк|ремонт|детал|добыч|нефт|сырь|\bproduction|manufactur|processing|workshop|serial|\bseries|machine tool|\brepair|\bpart\b|extract|\boil\b|raw.material', label):
        return ICONS['production']
    if _has(r'промышл|фабрик|завод|предприят|строит|\bindustr|factory|factories|enterprise|construct', label):
        return ICONS['civilian']
    if _has(r'конститу|парламент|съезд|граждан|республик|кабинет|бюджет|перепис|земель|местн|труд|полномоч|приоритет|прибыл|constitution|parliament|congress|civilian|republic|cabinet|budget|census|agrarian|local|labour|labor\b|powers|priorit|profits', label):
        return ICONS['constitution']

    # Effect and identifier hints cover short/figurative titles without assigning
    # every political +stability reward the same incidental military icon.
    for pattern, category in [
        (r'type\s*=\s*infrastructure|capital_infrastructure|\binfrastructure\b', 'infrastructure'),
        (r'type\s*=\s*arms_factory|capital_military_factory', 'military_factory'),
        (r'type\s*=\s*industrial_complex|capital_civilian_factory', 'civilian'),
        (r'aof_diplomacy\.|add_opinion_modifier', 'diplomacy'),
        (r'navy_experience|naval_|dockyard', 'navy'),
        (r'air_experience|air_equipment|light_fighter', 'air'),
        (r'category\s*=\s*armor|\btank\b', 'armor'),
        (r'army_experience|land_doctrine|logistics_tech', 'army'),
        (r'add_tech_bonus|research_slot|research_speed|electronics|\bengineers\b', 'research'),
        (r'\bseries\b|\bproduction\b|factory_efficiency', 'production'),
    ]:
        if _has(pattern, effect+' '+ident):
            return ICONS[category]
    return ICONS['constitution']
