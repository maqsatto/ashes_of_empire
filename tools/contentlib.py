"""Deterministic authoring helpers; not required by the running mod."""
from pathlib import Path
from functools import lru_cache
from focusicons import focus_icon
import json, re

ROOT = Path(__file__).resolve().parents[1]

def write(path, text, bom=False):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace('\r\n', '\n').encode('utf-8-sig' if bom else 'utf-8')
    if not p.exists() or p.read_bytes() != data:
        p.write_bytes(data)

def q(text):
    return json.dumps(text, ensure_ascii=False)

@lru_cache(maxsize=2)
def native_localisation_keys(lang):
    base=Path('C:/Hearts of Iron IV/localisation')/lang
    keys=set()
    for p in base.rglob('*.yml'):
        keys.update(re.findall(r'^\s+([^\s:#]+):',p.read_text(encoding='utf-8-sig'),re.M))
    return keys

def localize(stem, entries):
    """entries: {key: (Russian, English)}; each stem owns its keys."""
    for lang, index in [('russian', 0), ('english', 1)]:
        native=native_localisation_keys(lang)
        write(f'localisation/{lang}/{stem}_l_{lang}.yml',
              f'l_{lang}:\n' + ''.join(f' {key}: {q(pair[index])}\n' for key,pair in entries.items() if key not in native), True)
        overrides={key:pair for key,pair in entries.items() if key in native}
        if overrides:
            write(f'localisation/replace/{stem}_l_{lang}.yml',
                  f'l_{lang}:\n'+''.join(f' {key}: {q(pair[index])}\n' for key,pair in overrides.items()),True)

def render_tree(tree_id, tags, nodes, default=False):
    """Nodes: id, ru, en, desc_ru/en, pre(list AND or nested OR lists), excludes,
    x,y,cost(days/7), effect, available, branch, bypass, ai, icon, extra."""
    country = 'factor = 1' if default else 'factor = 0 modifier = { add = 10000 OR = { ' + ' '.join('tag = '+t for t in tags) + ' } }'
    text = f'focus_tree = {{\n id = {tree_id}\n country = {{ {country} }}\n default = {"yes" if default else "no"}\n reset_on_civilwar = no\n'
    if nodes:
        text += f' initial_show_position = {{ focus = {nodes[0]["id"]} }}\n'
    # Keep absolute coordinates nonnegative, as in the native generic tree.
    # This preserves relative branch spacing and avoids a left-clamped camera.
    x_offset=-min(0,min((n.get('x',0) for n in nodes),default=0))
    loc = {}
    for n in nodes:
        ident=n['id']
        assert ident.startswith('aof_'), ident
        loc[ident]=(n['ru'],n['en'])
        loc[ident+'_desc']=(n.get('desc_ru',n['ru']),n.get('desc_en',n['en']))
        pre=''.join(' prerequisite = { '+ ' '.join('focus = '+i for i in (p if isinstance(p,list) else [p]))+' }\n' for p in n.get('pre',[]))
        ex=' mutually_exclusive = { '+' '.join('focus = '+i for i in n['excludes'])+' }\n' if n.get('excludes') else ''
        optional=''.join(f' {key} = {{ {n[value]} }}\n' for key,value in [('available','available'),('allow_branch','branch'),('bypass','bypass')] if n.get(value))
        text += f''' focus = {{
  id = {ident}
  icon = {focus_icon(n)}
  x = {n.get('x',0)+x_offset}
  y = {n.get('y',0)}
  cost = {n.get('cost',5)}
{pre}{ex}{optional}  ai_will_do = {{ factor = {n.get('ai',1)} }}
  completion_reward = {{ {n.get('effect','add_political_power = 25')} }}
  {n.get('extra','')}
 }}
'''
    return text+'}\n',loc

def capital_building(kind='industrial_complex', level=1):
    """Use explicit tooltip at country scope; keep state effects hidden."""
    key={'industrial_complex':'aof_capital_civilian_factory','arms_factory':'aof_capital_military_factory','infrastructure':'aof_capital_infrastructure'}.get(kind)
    slot='' if kind=='infrastructure' else f'add_extra_state_shared_building_slots = {level}'
    tooltip=f'custom_effect_tooltip = {key}' if key and level==1 else ''
    return f'{tooltip} hidden_effect = {{ capital_scope = {{ {slot} add_building_construction = {{ type = {kind} level = {level} instant_build = yes }} }} }}'
