"""
Test suite for exit trigger translation (EXIT-01 through EXIT-07).

Tests cover:
- EXIT-01: Weight triggers convert to volumetric targets
- EXIT-02: Time triggers convert to time targets
- EXIT-03: Pressure triggers convert to pressure targets
- EXIT-04: Flow triggers convert to flow targets
- EXIT-05: Comparison operators map correctly
- EXIT-06: Relative time triggers convert to absolute values
- EXIT-07: All trigger types convert in single pass
- Unsupported type warnings
- Duplicate trigger deduplication
"""

import pytest
from translate_profile.translator import translate_profile


def make_profile_with_triggers(triggers: list[dict]) -> dict:
    """Create a minimal test profile with specified exit triggers."""
    return {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 36,
        'stages': [{
            'name': 'Test Phase',
            'key': 'Extraction',
            'type': 'pressure',
            'dynamics': {'points': [[0, 9]], 'over': 'time', 'interpolation': 'linear'},
            'exit_triggers': triggers,
        }],
    }


# EXIT-01: Weight triggers convert to volumetric targets
def test_weight_to_volumetric():
    """EXIT-01: Weight triggers should convert to volumetric targets."""
    profile = make_profile_with_triggers([
        {'type': 'weight', 'value': 36, 'relative': False, 'comparison': '>='}
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['type'] == 'volumetric'
    assert targets[0]['value'] == 36
    assert targets[0]['operator'] == 'gte'


# EXIT-02: Time triggers convert to time targets
def test_time_to_time():
    """EXIT-02: Time triggers should convert to time targets."""
    profile = make_profile_with_triggers([
        {'type': 'time', 'value': 25, 'relative': False, 'comparison': '>='}
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['type'] == 'time'
    assert targets[0]['value'] == 25
    assert targets[0]['operator'] == 'gte'


# EXIT-03: Pressure triggers convert to pressure targets
def test_pressure_to_pressure():
    """EXIT-03: Pressure triggers should convert to pressure targets."""
    profile = make_profile_with_triggers([
        {'type': 'pressure', 'value': 9, 'relative': False, 'comparison': '>='}
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['type'] == 'pressure'
    assert targets[0]['value'] == 9
    assert targets[0]['operator'] == 'gte'


# EXIT-04: Flow triggers convert to flow targets
def test_flow_to_flow():
    """EXIT-04: Flow triggers should convert to flow targets."""
    profile = make_profile_with_triggers([
        {'type': 'flow', 'value': 2, 'relative': False, 'comparison': '>='}
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['type'] == 'flow'
    assert targets[0]['value'] == 2
    assert targets[0]['operator'] == 'gte'


# EXIT-05: Comparison operators map correctly
@pytest.mark.parametrize("meticulous_op,gaggimate_op", [
    ('>=', 'gte'),
    ('<=', 'lte'),
    ('>', 'gt'),
    ('<', 'lt'),
])
def test_operator_mapping(meticulous_op, gaggimate_op):
    """EXIT-05: Comparison operators should map correctly."""
    profile = make_profile_with_triggers([
        {'type': 'weight', 'value': 36, 'relative': False, 'comparison': meticulous_op}
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['operator'] == gaggimate_op


# EXIT-06: Relative time triggers convert to absolute values
def test_relative_time_conversion():
    """EXIT-06: Relative time triggers should convert to absolute values."""
    # Multi-point stage: first segment 10s (0→10), second segment 15s (10→25)
    profile = {
        'name': 'Test Profile',
        'id': 'test',
        'author': 'Test',
        'author_id': 'test',
        'temperature': 93,
        'final_weight': 36,
        'stages': [{
            'name': 'Test Phase',
            'key': 'Extraction',
            'type': 'pressure',
            'dynamics': {'points': [[0, 9], [10, 9]], 'over': 'time', 'interpolation': 'linear'},
            'exit_triggers': [
                # Relative time trigger should convert to absolute: 10 + 5 = 15
                {'type': 'time', 'value': 5, 'relative': True, 'comparison': '>='},
            ],
        }],
    }
    result, _ = translate_profile(profile)
    # The target should be on the second (final) segment
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['type'] == 'time'
    assert targets[0]['value'] == 15  # 10 + 5 = 15 (absolute time)


# EXIT-07: All trigger types convert in single pass
def test_multiple_trigger_types():
    """EXIT-07: All trigger types should convert in a single pass."""
    profile = make_profile_with_triggers([
        {'type': 'weight', 'value': 36, 'relative': False, 'comparison': '>='},
        {'type': 'time', 'value': 25, 'relative': False, 'comparison': '>='},
        {'type': 'pressure', 'value': 9, 'relative': False, 'comparison': '>='},
        {'type': 'flow', 'value': 2, 'relative': False, 'comparison': '>='},
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 4
    types = [t['type'] for t in targets]
    assert 'volumetric' in types
    assert 'time' in types
    assert 'pressure' in types
    assert 'flow' in types


# Unsupported type warning test
def test_unsupported_type_warning():
    """Unsupported trigger types should generate warnings."""
    profile = make_profile_with_triggers([
        {'type': 'piston_position', 'value': 50, 'relative': False, 'comparison': '>='}
    ])
    
    with pytest.warns(UserWarning, match=r'\[Unsupported\].*piston_position.*not supported'):
        translate_profile(profile)


# Deduplication test
def test_duplicate_trigger_deduplication():
    """Duplicate trigger types should be deduplicated (first kept, others skipped)."""
    profile = make_profile_with_triggers([
        {'type': 'weight', 'value': 36, 'relative': False, 'comparison': '>='},
        {'type': 'weight', 'value': 30, 'relative': False, 'comparison': '>='},  # Duplicate
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    # Should only have 1 target (first weight trigger kept, duplicate skipped)
    assert len(targets) == 1
    assert targets[0]['type'] == 'volumetric'
    assert targets[0]['value'] == 36  # First trigger value


# Test multiple unsupported types generate warnings
def test_multiple_unsupported_types():
    """Multiple unsupported types should each generate warnings."""
    profile = make_profile_with_triggers([
        {'type': 'piston_position', 'value': 50, 'relative': False, 'comparison': '>='},
        {'type': 'power', 'value': 100, 'relative': False, 'comparison': '>='},
    ])
    
    with pytest.warns(UserWarning) as warning_list:
        translate_profile(profile)
    
    # Should have warnings for both unsupported types
    warning_messages = [str(w.message) for w in warning_list]
    assert any('piston_position' in msg for msg in warning_messages)
    assert any('power' in msg for msg in warning_messages)


# Test mixed supported and unsupported types
def test_mixed_supported_and_unsupported_types():
    """Supported types should convert while unsupported generate warnings."""
    profile = make_profile_with_triggers([
        {'type': 'weight', 'value': 36, 'relative': False, 'comparison': '>='},
        {'type': 'piston_position', 'value': 50, 'relative': False, 'comparison': '>='},
        {'type': 'time', 'value': 25, 'relative': False, 'comparison': '>='},
    ])
    
    with pytest.warns(UserWarning, match=r'\[Unsupported\].*piston_position.*not supported'):
        result, _ = translate_profile(profile)
    
    targets = result['phases'][0]['targets']
    # Should have 2 targets (weight and time)
    assert len(targets) == 2
    types = [t['type'] for t in targets]
    assert 'volumetric' in types
    assert 'time' in types
    assert 'piston_position' not in types


# Test absolute time triggers preserve their values
def test_absolute_time_preserved():
    """Absolute time triggers (relative=False) should preserve their values."""
    profile = make_profile_with_triggers([
        {'type': 'time', 'value': 30, 'relative': False, 'comparison': '>='}
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    assert len(targets) == 1
    assert targets[0]['type'] == 'time'
    assert targets[0]['value'] == 30  # Value should be preserved as-is


# Test all comparison operators with different trigger types
@pytest.mark.parametrize("trigger_type,trigger_value", [
    ('weight', 36),
    ('time', 25),
    ('pressure', 9),
    ('flow', 2),
])
def test_all_operators_with_all_types(trigger_type, trigger_value):
    """All comparison operators should work with all trigger types."""
    profile = make_profile_with_triggers([
        {'type': trigger_type, 'value': trigger_value, 'relative': False, 'comparison': '>='},
        {'type': trigger_type, 'value': trigger_value, 'relative': False, 'comparison': '<='},
        {'type': trigger_type, 'value': trigger_value, 'relative': False, 'comparison': '>'},
        {'type': trigger_type, 'value': trigger_value, 'relative': False, 'comparison': '<'},
    ])
    result, _ = translate_profile(profile)
    targets = result['phases'][0]['targets']
    
    # Due to deduplication, only first trigger of each type should be kept
    assert len(targets) == 1
    assert targets[0]['type'] == (
        'volumetric' if trigger_type == 'weight' else trigger_type
    )
    assert targets[0]['operator'] == 'gte'  # First operator used
