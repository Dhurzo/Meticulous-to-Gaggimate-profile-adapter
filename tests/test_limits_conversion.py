"""Test stage limits conversion to pressure targets."""

import pytest
from translate_profile.translator import translate_profile


def test_pressure_limits_convert_to_pressure_targets():
    """limits[].pressure should convert to pressure target"""
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
            'limits': [{'type': 'pressure', 'value': 6.5}],
        }],
    }
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    pressure_targets = [t for t in targets if t['type'] == 'pressure']
    assert len(pressure_targets) == 1
    assert pressure_targets[0]['value'] == 6.5
    assert pressure_targets[0]['operator'] == 'lte'


def test_multiple_pressure_limits():
    """Multiple pressure limits should all be converted"""
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
            'limits': [
                {'type': 'pressure', 'value': 6.5},
                {'type': 'pressure', 'value': 8.0},
            ],
        }],
    }
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    pressure_targets = [t for t in targets if t['type'] == 'pressure']
    assert len(pressure_targets) == 2
    pressure_values = [t['value'] for t in pressure_targets]
    assert 6.5 in pressure_values
    assert 8.0 in pressure_values


def test_empty_limits_no_targets():
    """Empty limits array should not create any targets"""
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
    targets = result['phases'][0]['targets']
    
    pressure_targets = [t for t in targets if t['type'] == 'pressure']
    assert len(pressure_targets) == 0


def test_non_pressure_limits_ignored():
    """Non-pressure limit types should be ignored"""
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
            'limits': [
                {'type': 'flow', 'value': 2.5},
                {'type': 'temperature', 'value': 93},
            ],
        }],
    }
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    # Only volumetric from final_weight should exist
    assert len(targets) == 1
    assert targets[0]['type'] == 'volumetric'


def test_limits_with_exit_triggers():
    """Limits and exit_triggers should both be converted to targets"""
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
                {'type': 'time', 'value': 30, 'relative': False, 'comparison': '>='},
                {'type': 'pressure', 'value': 9, 'relative': False, 'comparison': '>'},
            ],
            'limits': [
                {'type': 'pressure', 'value': 6.5},
            ],
        }],
    }
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    # Should have 4 targets: 2 from exit_triggers + 1 from limits + 1 from final_weight
    assert len(targets) == 4
    
    target_types = {t['type'] for t in targets}
    assert 'time' in target_types
    assert 'pressure' in target_types
    assert 'volumetric' in target_types
    
    # Check that the limit pressure target exists with correct operator
    pressure_targets = [t for t in targets if t['type'] == 'pressure']
    limit_target = [t for t in pressure_targets if t['operator'] == 'lte']
    assert len(limit_target) == 1
    assert limit_target[0]['value'] == 6.5


def test_limits_in_multi_point_stage():
    """Limits should be converted in multi-point stages (on final phase)"""
    profile = {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 38.0,
        'stages': [{
            'name': 'Ramp',
            'key': 'ramp',
            'type': 'pressure',
            'dynamics': {
                'points': [[0, 2.0], [10, 5.0], [20, 9.0]],
                'over': 'time',
                'interpolation': 'linear',
            },
            'exit_triggers': [],
            'limits': [{'type': 'pressure', 'value': 8.0}],
        }],
    }
    result, _ = translate_profile(profile)
    
    # Should have 2 phases from 3 points
    assert len(result['phases']) == 2
    
    # Only the last phase should have the limit target
    first_phase_targets = result['phases'][0]['targets']
    assert len(first_phase_targets) == 0
    
    last_phase_targets = result['phases'][1]['targets']
    pressure_targets = [t for t in last_phase_targets if t['type'] == 'pressure']
    assert len(pressure_targets) == 1
    assert pressure_targets[0]['value'] == 8.0
    assert pressure_targets[0]['operator'] == 'lte'
