"""ODD scenario space and requirement-derived boundary predicates for Phase B.

Dimensions follow the ODD conditions of EU 2022/1426 Annex II point 3.1.4.1 plus speed.
The discrete levels chosen for each dimension are an experimental design decision of
this study (documented here); a level is 'boundary-exercising' when it lies at or beyond
the operating-condition boundary named by the linked requirement.

Requirement IDs refer to the corpus extraction (eu1426_statements.csv) and to
UN Regulation No 157 (OJ L 82, 9.3.2021) paragraph numbers.
"""
DIMENSIONS = {
    'precipitation': ['none', 'rain', 'snow'],
    'lighting':      ['day', 'dusk', 'night', 'low_sun_glare'],
    'visibility':    ['clear', 'mist', 'fog'],
    'road_markings': ['clear', 'worn', 'absent'],
    'road_category': ['motorway_separated', 'dual_carriageway', 'single_carriageway'],
    'speed_kmh':     ['40', '60', '70'],
}
DIM_NAMES = list(DIMENSIONS)

# Each predicate: id, source requirement, and a test on a scenario dict -> True if the
# scenario exercises (reaches or crosses) the boundary the requirement refers to.
PREDICATES = [
    ('P1', 'EU1426-039 (Annex II 3.1.4.1(a) precipitation)', lambda s: s['precipitation'] in ('rain', 'snow')),
    ('P2', 'EU1426-040 (Annex II 3.1.4.1(b) time of day)',   lambda s: s['lighting'] in ('dusk', 'night')),
    ('P3', 'EU1426-041 (Annex II 3.1.4.1(c) light intensity)', lambda s: s['lighting'] in ('night', 'low_sun_glare')),
    ('P4', 'EU1426-042 (Annex II 3.1.4.1(d) fog, mist)',     lambda s: s['visibility'] in ('mist', 'fog')),
    ('P5', 'EU1426-043 (Annex II 3.1.4.1(e) road and lane markings)', lambda s: s['road_markings'] in ('worn', 'absent')),
    ('P6', 'EU1426-044 (Annex II 3.1.4.1(f) road category)', lambda s: s['road_category'] != 'motorway_separated'),
    ('P7', 'UN R157 para 5.2.3.1 (maximum speed 60 km/h)',   lambda s: s['speed_kmh'] in ('60', '70')),
    ('P8', 'UN R157 para 7.1.3 (conditions reducing detection range)',
           lambda s: s['visibility'] == 'fog' or s['precipitation'] == 'snow' or s['lighting'] == 'low_sun_glare'),
]
