"""Model coordinate sampling inferred from nine actual HOI4 1.19 errors.

Native integer Z positions sample image row H-1-floor(Z), not floor(H-Z).
Half-pixel-centred Caspian spawns have identical results under both formulas.
These observations establish province lookup, not successful rendering/gameplay.
"""
import math

ENGINE_OBSERVATIONS = (
    (17297, 3797.0, 1536.0, 12143),
    (17310, 3844.0, 1580.0, 4369),
    (17311, 3769.0, 1543.0, 10140),
    (17409, 3627.0, 1584.0, 3265),
    (32495, 3980.0, 1547.0, 10630),
    (32518, 3983.0, 1579.0, 4670),
    (46172, 4028.0, 1384.0, 4845),
    (46240, 3952.0, 1556.0, 10633),
    (47770, 3899.0, 1468.0, 1243),
)


def engine_pixel(x, z, height):
    return math.floor(float(x)), int(height) - 1 - math.floor(float(z))


def province_at_model(image, rgb_to_province, x, z):
    """Sample a numpy RGB image; return None for a position outside its bounds."""
    px, py = engine_pixel(x, z, image.shape[0])
    if not (0 <= px < image.shape[1] and 0 <= py < image.shape[0]):
        return None
    return rgb_to_province.get(tuple(map(int, image[py, px])))


def validate_engine_observations(image, rgb_to_province):
    for line, x, z, expected in ENGINE_OBSERVATIONS:
        actual = province_at_model(image, rgb_to_province, x, z)
        if actual != expected:
            raise RuntimeError(f'Observed engine sample differs at former line {line}: {actual}, expected {expected}')
    return len(ENGINE_OBSERVATIONS)


def audit_model_membership(lines, image, rgb_to_province, membership,
                           affected_states, affected_provinces):
    """Separate our regressions from untouched native floating-harbour records.

    Callers decide whether to fail on affected_mismatches. No row is changed.
    Only provinces with an effective land-state owner participate in this check.
    """
    report = {'affected_mismatches': [], 'outside_mismatches': [],
              'native_floating_harbor_mismatches': []}
    for index, line in enumerate(lines, 1):
        row = line.split(';')
        if len(row) != 7 or not row[0].isdigit():
            continue
        province = province_at_model(image, rgb_to_province, row[2], row[4])
        target = membership.get(province)
        if target is None or target == int(row[0]):
            continue
        item = {'line': index, 'type': row[1], 'province': province,
                'declared_state': int(row[0]), 'sampled_state': target}
        if row[1] == 'floating_harbor':
            group = 'native_floating_harbor_mismatches'
        elif int(row[0]) in affected_states or province in affected_provinces:
            group = 'affected_mismatches'
        else:
            group = 'outside_mismatches'
        report[group].append(item)
    return report


STATE_SITE_TYPES = ('air_base', 'rocket_site_spawn', 'synthetic_refinery',
                    'nuclear_reactor_spawn', 'radar_station', 'fuel_silo',
                    'stronghold_network')
NORMAL_MODEL_TYPES = ('industrial_complex', 'arms_factory', 'anti_air_building',
                      'special_project_facility_spawn', 'supply_node')


def validate_required_sites(lines, image, rgb_to_province, membership, states,
                            required=STATE_SITE_TYPES):
    """Count only sites whose actual sampled land point belongs to their state.

    The installed gun emplacement uses rocket_site_spawn; no invented
    gun_emplacement row or building level is required.
    """
    coverage = {int(s): {kind: 0 for kind in required} for s in states}
    for line in lines:
        row = line.split(';')
        if len(row) != 7 or not row[0].isdigit():
            continue
        sid = int(row[0])
        if sid not in coverage or row[1] not in coverage[sid]:
            continue
        province = province_at_model(image, rgb_to_province, row[2], row[4])
        if membership.get(province) == sid:
            coverage[sid][row[1]] += 1
    missing = [(sid, kind) for sid, kinds in coverage.items()
               for kind, count in kinds.items() if not count]
    if missing:
        raise RuntimeError('Missing valid map model sites: ' + str(missing))
    return coverage
