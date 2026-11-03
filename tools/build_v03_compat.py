"""Inert identifier registry for vanilla databases intentionally replaced by AoE.

Authoring tool, never required at runtime. --inspect reads/parses/validates only and
does not write any runtime file. Run without --inspect ONLY with HOI4 closed: new
focus/decision/event database files require a clean batched restart.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import json
import os
import re
import subprocess

from contentlib import ROOT, write

GAME = Path('C:/Hearts of Iron IV')
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}]|(?:[<>!?]=?|=)|[^\s{}=<>!?#"]+')
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_.:-]*\Z')
EVENT_ID = re.compile(r'([A-Za-z_][A-Za-z0-9_.-]*)\.([A-Za-z0-9_]+)\Z')
PREFIX = 'aof_'
PARSE_WARNINGS = []


def parse(path, tolerant=False):
    """Parse assignments and nested blocks, preserving repeated keys.

    Quoted strings and comments are tokenised before braces are considered.
    Bare list atoms are skipped; only assignments matter for identifier metadata.
    Does not execute or carry native effect bodies into generated content.
    """
    text = path.read_text(encoding='utf-8-sig')
    tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith('#')]
    position = 0

    def block(nested=False):
        nonlocal position
        result = []
        while position < len(tokens):
            key = tokens[position]
            position += 1
            if key == '}':
                if not nested:
                    if tolerant:
                        PARSE_WARNINGS.append({'file': str(path), 'issue': 'ignored unmatched top-level closing brace during identifier extraction'})
                        continue
                    raise ValueError(f'{path}: unmatched closing brace')
                return result
            if key == '{':
                block(True)
                continue
            if position >= len(tokens) or tokens[position] not in ('=', '<', '>', '<=', '>=', '!=', '?='):
                continue
            operation = tokens[position]
            position += 1
            if position >= len(tokens):
                raise ValueError(f'{path}: assignment without value: {key}')
            value = tokens[position]
            position += 1
            if value == '{':
                value = block(True)
            elif value == '}':
                raise ValueError(f'{path}: unexpected closing brace after {key}')
            elif value.startswith('"'):
                value = value[1:-1]
            result.append((key.strip('"'), operation, value))
        if nested:
            if tolerant:
                PARSE_WARNINGS.append({'file': str(path), 'issue': 'unclosed native block at EOF during identifier extraction'})
            else:
                raise ValueError(f'{path}: unclosed block')
        return result

    return block()


def scalar(nodes, key):
    values = [v for k, op, v in nodes if k == key and op == '=' and isinstance(v, str)]
    if len(values) > 1:
        raise ValueError(f'duplicate scalar {key}: {values}')
    return values[0] if values else None


def walk(nodes):
    for key, op, value in nodes:
        yield key, op, value
        if isinstance(value, list):
            yield from walk(value)


def collect():
    PARSE_WARNINGS.clear()
    focus_sources = defaultdict(list)
    decision_sources = defaultdict(list)
    event_sources = defaultdict(list)
    namespace_sources = defaultdict(list)
    styles = set()
    source_files = defaultdict(int)
    decision_metadata = {
        'allowed', 'visible', 'available', 'custom_cost_trigger', 'custom_cost_text',
        'on_map_area', 'on_map_mode', 'on_map_mode_change', 'on_start', 'on_end',
        'on_show', 'on_hide', 'on_open', 'on_close', 'on_category_open',
        'on_category_close', 'target_trigger', 'target_root_trigger', 'ai_will_do',
    }
    for path in sorted((GAME / 'common/national_focus').glob('*.txt')):
        nodes = parse(path, tolerant=True)
        source_files['focus'] += 1
        for key, op, value in walk(nodes):
            if key in ('focus', 'shared_focus', 'joint_focus') and isinstance(value, list):
                ident = scalar(value, 'id')
                if ident and not ident.lower().startswith(PREFIX):
                    if not IDENT.fullmatch(ident):
                        raise ValueError(f'{path}: unexpected focus identifier {ident}')
                    focus_sources[ident].append(str(path.relative_to(GAME)))
        for key, op, value in nodes:
            if key == 'style' and isinstance(value, list):
                name = scalar(value, 'name')
                if name:
                    styles.add(name)
    # Category definitions are intentionally not traversed as decision definitions.
    for path in sorted((GAME / 'common/decisions').glob('*.txt')):
        nodes = parse(path, tolerant=True)
        source_files['decision'] += 1
        for category, op, definitions in nodes:
            if not isinstance(definitions, list):
                continue
            for ident, child_op, body in definitions:
                if not isinstance(body, list) or child_op != '=' or ident in decision_metadata:
                    continue
                if ident.lower().startswith(PREFIX):
                    continue
                if not IDENT.fullmatch(ident):
                    raise ValueError(f'{path}: unexpected decision identifier {ident}')
                decision_sources[ident].append(str(path.relative_to(GAME)) + ':' + category)
    for path in sorted((GAME / 'events').glob('*.txt')):
        nodes = parse(path, tolerant=True)
        source_files['event'] += 1
        for key, op, value in nodes:
            if key == 'add_namespace' and isinstance(value, str):
                namespace_sources[value].append(str(path.relative_to(GAME)))
            if not key.endswith('_event') or not isinstance(value, list):
                continue
            ident = scalar(value, 'id')
            if ident and not ident.lower().startswith(('aof_', 'aof.')):
                # Keep numeric old-style IDs if actually present; invent no namespace.
                if not EVENT_ID.fullmatch(ident) and not ident.isdecimal():
                    raise ValueError(f'{path}: unexpected event identifier {ident}')
                event_sources[ident].append((key, str(path.relative_to(GAME))))
    for ident in event_sources:
        match = EVENT_ID.fullmatch(ident)
        if match and match[1].lower() not in {n.lower() for n in namespace_sources}:
            raise ValueError(f'Installed event {ident} lacks an installed add_namespace declaration')
    # Existing AoE identifiers cannot be shadowed by this registry.
    conflicts = []
    for folder, ids, kinds in [
        ('common/national_focus', focus_sources, {'focus', 'shared_focus', 'joint_focus'}),
        ('events', event_sources, None),
    ]:
        for path in (ROOT / folder).glob('*.txt'):
            if path.name == 'aof_compatibility_registry.txt':
                continue
            for key, op, value in walk(parse(path)):
                if isinstance(value, list) and ((kinds and key in kinds) or (kinds is None and key.endswith('_event'))):
                    ident = scalar(value, 'id')
                    if ident in ids:
                        conflicts.append((folder, ident, str(path)))
    for path in (ROOT / 'common/decisions').glob('*.txt'):
        if path.name == 'aof_compatibility_registry.txt':
            continue
        for category, op, definitions in parse(path):
            if isinstance(definitions, list):
                for ident, child_op, body in definitions:
                    if isinstance(body, list) and ident in decision_sources:
                        conflicts.append(('common/decisions', ident, str(path)))
    if conflicts:
        raise ValueError(f'Compatibility IDs collide with active mod definitions: {conflicts[:20]}')
    for kind, items in [('focus', focus_sources), ('decision', decision_sources), ('event', event_sources)]:
        folded = [key.lower() for key in items]
        if len(folded) != len(set(folded)):
            raise ValueError(f'Installed {kind} IDs collide ignoring letter case')
    return focus_sources, decision_sources, event_sources, namespace_sources, styles, source_files


def render(data):
    focuses, decisions, events, namespaces, styles, source_files = data
    warning = '# Inert vanilla identifier registry. No original effects, prerequisites, triggers or plots are restored.\n'
    focus_text = warning + 'focus_tree = {\n id = aof_compatibility\n country = { factor = 0 }\n default = no\n reset_on_civilwar = no\n'
    for ident in sorted(focuses):
        focus_text += f' focus = {{ id = {ident} cost = 1 icon = GFX_goal_generic_political_pressure available = {{ always = no }} }}\n'
    focus_text += '}\n'
    decision_text = warning + 'aof_legacy_compat = {\n'
    for ident in sorted(decisions):
        decision_text += f' {ident} = {{ allowed = {{ always = no }} visible = {{ always = no }} available = {{ always = no }} ai_will_do = {{ factor = 0 }} }}\n'
    decision_text += '}\n'
    category_text = warning + 'aof_legacy_compat = { allowed = { always = no } visible = { always = no } }\n'
    original_namespace_case = {n.lower(): n for n in namespaces}
    used_namespaces = {original_namespace_case[EVENT_ID.fullmatch(i)[1].lower()] for i in events if EVENT_ID.fullmatch(i)}
    event_text = warning + ''.join('add_namespace = ' + n + '\n' for n in sorted(used_namespaces))
    for ident in sorted(events):
        # A hidden no-op of the original event type. Triggered calls cannot run a plot.
        event_type = events[ident][-1][0]
        event_text += f'{event_type} = {{ id = {ident} hidden = yes is_triggered_only = yes trigger = {{ always = no }} option = {{ name = aof_compatibility_noop }} }}\n'
    # Replaced focus folder also contained the default border styles. Register names
    # with native generic sprites, without importing any foreign country focus data.
    style_text = warning
    for name in sorted(styles | {'default_style'}):
        if not IDENT.fullmatch(name):
            raise ValueError(f'Unexpected native style name {name}')
        style_text += f'style = {{ name = {name} '+('default = yes ' if name == 'default_style' else '')+'unavailable = GFX_focus_unavailable completed = GFX_focus_completed available = GFX_focus_can_start current = GFX_focus_current }\n'
    outputs = {
        'common/national_focus/aof_compatibility_registry.txt': focus_text,
        'common/national_focus/00_titlebar_styles.txt': style_text,
        'common/decisions/aof_compatibility_registry.txt': decision_text,
        'common/decisions/categories/aof_compatibility_registry.txt': category_text,
        'events/aof_compatibility_registry.txt': event_text,
    }
    manifest = {
        'source': str(GAME),
        'purpose': 'Unreachable/no-op vanilla identifier metadata; not restored gameplay.',
        'source_file_counts': dict(source_files),
        'native_parse_warnings': PARSE_WARNINGS,
        'counts': {'focuses': len(focuses), 'decisions': len(decisions), 'events': len(events), 'namespaces': len(used_namespaces), 'focus_styles': len(styles | {'default_style'})},
        'focus_sources': dict(sorted(focuses.items())),
        'decision_sources': dict(sorted(decisions.items())),
        'event_sources': {k: [{'type': kind, 'file': p} for kind, p in v] for k, v in sorted(events.items())},
        'namespace_sources': {k: namespaces[k] for k in sorted(used_namespaces)},
        'duplicates_in_installed_source': {
            'focuses': {k: v for k, v in focuses.items() if len(v) > 1},
            'decisions': {k: v for k, v in decisions.items() if len(v) > 1},
            'events': {k: v for k, v in events.items() if len(v) > 1},
        },
        'outputs': list(outputs),
    }
    # Verify authored output syntax without writing any file in --inspect mode.
    for path, text in outputs.items():
        assert text.count('{') == text.count('}'), path
        class MemoryScript:
            def read_text(self, **kwargs):
                return text
            def __str__(self):
                return 'in-memory ' + path
        parse(MemoryScript())
        for prohibited in ['completion_reward =', 'complete_effect =', 'remove_effect =', 'add_ideas =', 'load_focus_tree =', 'declare_war_on =']:
            assert prohibited not in text, (path, prohibited)
    assert len(re.findall(r'\bfocus = \{ id = (\S+)', focus_text)) == len(focuses)
    assert len(re.findall(r'\bid = (\S+)', event_text)) == len(events)
    return outputs, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true', help='Parse, validate, report counts; write NO runtime output.')
    args = parser.parse_args()
    outputs, manifest = render(collect())
    print(json.dumps({'mode': 'READ_ONLY_INSPECTION' if args.inspect else 'GENERATE_WITH_GAME_CLOSED', 'counts': manifest['counts'], 'source_file_counts': manifest['source_file_counts'], 'native_parse_warnings': manifest['native_parse_warnings'], 'duplicate_installed_counts': {k: len(v) for k, v in manifest['duplicates_in_installed_source'].items()}, 'output_paths': manifest['outputs']}, ensure_ascii=False, indent=2))
    if args.inspect:
        print('Validated in memory. No runtime files or manifest written.')
        return
    if os.name != 'nt':
        raise RuntimeError('Runtime generation requires the Windows HOI4 process check; use --inspect for read-only validation.')
    check = subprocess.run(['powershell.exe', '-NoProfile', '-Command', '@(Get-Process -Name hoi4 -ErrorAction SilentlyContinue).Count'], capture_output=True, text=True, check=True)
    if int(check.stdout.strip()) != 0:
        raise RuntimeError('HOI4 is running. No compatibility runtime files were written. Close the game and batch this generation with the planned full restart.')
    for path, text in outputs.items():
        write(path, text)
    write('docs/design_v0_3/COMPATIBILITY_REGISTRY_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
