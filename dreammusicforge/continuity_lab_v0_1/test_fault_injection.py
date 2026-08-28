from apex_continuity_simulator import *


def run_case(name, mutator):
    contract = BoundaryContract(name, 'curtain_wipe', 0.7)
    source = SubjectState()
    target = SubjectState()
    mutator(target)
    frames, coverage = transition_full_wipe('red_stage', 'blue_ocean', 21, source, 'curtain')
    return verify_transition(frames, coverage, contract, source, target)


cases = [
    run_case('control', lambda s: None),
    run_case('identity drift', lambda s: setattr(s, 'identity_id', 'SUBJECT_B')),
    run_case('footwear drift', lambda s: setattr(s, 'footwear_id', 'different_shoes')),
    run_case('wardrobe drift', lambda s: setattr(s, 'wardrobe_id', 'different_dress')),
    run_case('camera/scale drift', lambda s: setattr(s, 'scale', 1.09)),
    run_case('screen position drift', lambda s: setattr(s, 'x', 0.58)),
    run_case('motion phase drift', lambda s: setattr(s, 'phase', 0.26)),
]

assert cases[0]['pass'] is True
for result in cases[1:]:
    assert result['pass'] is False, result
