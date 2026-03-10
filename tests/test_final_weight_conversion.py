"""Test final_weight conversion to volumetric target."""

import pytest
from translate_profile.translator import translate_profile


def test_final_weight_converts_to_volumetric_target():
    """final_weight should convert to volumetric target on last phase"""
    profile = {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 38.0,
        'stages': [{
            'name': 'Brew',
            'key': 'brew',
            'type': 'flow',
            'dynamics': {'points': [[0, 11.3]], 'over': 'time', 'interpolation': 'linear'},
            'exit_triggers': [],
            'limits': [],
        }],
    }
    result, _ = translate_profile(profile)
    phases = result['phases']
    
    assert len(phases) == 1
    targets = phases[-1]['targets']
    
    # Should have volumetric target with final_weight value
    volumetric_targets = [t for t in targets if t['type'] == 'volumetric']
    assert len(volumetric_targets) == 1
    assert volumetric_targets[0]['value'] == 38.0
    assert volumetric_targets[0]['operator'] == 'gte'


def test_final_weight_zero_no_target():
    """final_weight of 0 should not create a target"""
    profile = {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 0.0,
        'stages': [{
            'name': 'Brew',
            'key': 'brew',
            'type': 'flow',
            'dynamics': {'points': [[0, 11.3]], 'over': 'time', 'interpolation': 'linear'},
            'exit_triggers': [],
            'limits': [],
        }],
    }
    result, _ = translate_profile(profile)
    phases = result['phases']
    
    targets = phases[-1]['targets']
    volumetric_targets = [t for t in targets if t['type'] == 'volumetric']
    assert len(volumetric_targets) == 0


def test_final_weight_no_duplicate_with_existing_weight_trigger():
    """final_weight should not duplicate if volumetric target already exists"""
    profile = {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 38.0,
        'stages': [{
            'name': 'Brew',
            'key': 'brew',
            'type': 'flow',
            'dynamics': {'points': [[0, 11.3]], 'over': 'time', 'interpolation': 'linear'},
            'exit_triggers': [
                {'type': 'weight', 'value': 36.0, 'relative': False, 'comparison': '>='}
            ],
            'limits': [],
        }],
    }
    result, _ = translate_profile(profile)
    phases = result['phases']
    
    targets = phases[-1]['targets']
    volumetric_targets = [t for t in targets if t['type'] == 'volumetric']
    
    # Should only have one volumetric target (the one from exit_triggers)
    assert len(volumetric_targets) == 1
    assert volumetric_targets[0]['value'] == 36.0


def test_final_weight_on_multiple_phases():
    """final_weight should only be added to the last phase"""
    profile = {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 40.0,
        'stages': [
            {
                'name': 'Preinfusion',
                'key': 'pre',
                'type': 'pressure',
                'dynamics': {'points': [[0, 2.0]], 'over': 'time', 'interpolation': 'linear'},
                'exit_triggers': [],
                'limits': [],
            },
            {
                'name': 'Brew',
                'key': 'brew',
                'type': 'pressure',
                'dynamics': {'points': [[0, 9.0]], 'over': 'time', 'interpolation': 'linear'},
                'exit_triggers': [],
                'limits': [],
            },
        ],
    }
    result, _ = translate_profile(profile)
    phases = result['phases']
    
    assert len(phases) == 2
    
    # First phase should not have volumetric target
    first_targets = phases[0]['targets']
    assert not any(t['type'] == 'volumetric' for t in first_targets)
    
    # Second phase should have volumetric target
    last_targets = phases[-1]['targets']
    volumetric_targets = [t for t in last_targets if t['type'] == 'volumetric']
    assert len(volumetric_targets) == 1
    assert volumetric_targets[0]['value'] == 40.0
