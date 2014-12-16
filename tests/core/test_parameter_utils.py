import pytest

from flex.serializers.core import ParameterSerializer
from flex.parameters import (
    filter_parameters,
    find_parameter,
    merge_parameter_lists,
)
from flex.constants import (
    INTEGER,
    STRING,
    PATH,
    QUERY,
)


ID_IN_PATH = {
    'name': 'id', 'in': PATH, 'description': 'id', 'type': INTEGER, 'required': True,
}
USERNAME_IN_PATH = {
    'name': 'username', 'in': PATH, 'description': 'username', 'type': STRING, 'required': True
}
PAGE_IN_QUERY = {
    'name': 'page', 'in': QUERY, 'description': 'page', 'type': STRING
}
PAGE_SIZE_IN_QUERY = {
    'name': 'page_size', 'in': QUERY, 'description': 'page_size', 'type': INTEGER,
}


#
# filter_parameters tests
#
@pytest.mark.parametrize(
    'lookup_kwargs,expected',
    (
        ({'in': PATH, 'name': 'id'}, ID_IN_PATH),
        ({'in': PATH, 'name': 'username'}, USERNAME_IN_PATH),
        ({'in': QUERY, 'type': INTEGER}, PAGE_SIZE_IN_QUERY),
        ({'name': 'page'}, PAGE_IN_QUERY),
    ),
)
def test_filtering_parameters(lookup_kwargs, expected):
    serializer = ParameterSerializer(many=True, data=[
        ID_IN_PATH,
        USERNAME_IN_PATH,
        PAGE_IN_QUERY,
        PAGE_SIZE_IN_QUERY,
    ])
    assert serializer.is_valid(), serializer.errors
    parameters = serializer.save()

    results = filter_parameters(parameters, **lookup_kwargs)

    assert len(results) == 1
    for key in lookup_kwargs:
        assert results[0][key] == expected[key]


#
# find_parameter tests
#
@pytest.mark.parametrize(
    'lookup_kwargs,expected',
    (
        ({'in': PATH, 'name': 'id'}, ID_IN_PATH),
        ({'in': PATH, 'name': 'username'}, USERNAME_IN_PATH),
        ({'in': QUERY, 'type': INTEGER}, PAGE_SIZE_IN_QUERY),
        ({'name': 'page'}, PAGE_IN_QUERY),
    ),
)
def test_find_parameter(lookup_kwargs, expected):
    serializer = ParameterSerializer(many=True, data=[
        ID_IN_PATH,
        USERNAME_IN_PATH,
        PAGE_IN_QUERY,
        PAGE_SIZE_IN_QUERY,
    ])
    assert serializer.is_valid(), serializer.errors
    parameters = serializer.save()

    actual = find_parameter(parameters, **lookup_kwargs)
    for key in lookup_kwargs:
        assert actual[key] == expected[key]


def test_find_parameter_errors_when_multiple_found():
    serializer = ParameterSerializer(many=True, data=[
        ID_IN_PATH,
        USERNAME_IN_PATH,
        PAGE_IN_QUERY,
        PAGE_SIZE_IN_QUERY,
    ])
    assert serializer.is_valid(), serializer.errors
    parameters = serializer.save()

    #sanity check
    sanity = filter_parameters(parameters, in_=PATH)
    assert len(sanity) == 2

    with pytest.raises(ValueError):
        find_parameter(parameters, in_=PATH)


def test_find_parameter_errors_when_no_match_found():
    serializer = ParameterSerializer(many=True, data=[
        ID_IN_PATH,
        USERNAME_IN_PATH,
        PAGE_IN_QUERY,
        PAGE_SIZE_IN_QUERY,
    ])
    assert serializer.is_valid(), serializer.errors
    parameters = serializer.save()

    #sanity check
    assert not filter_parameters(parameters, name='not-in-parameters')

    with pytest.raises(ValueError):
        find_parameter(parameters, name='not-in-parameters')


def test_merge_parameters_uses_last_write_wins():
    duplicate_a = {
        'name': 'duplicate',
        'in': PATH,
        'description': 'duplicate_a',
        'type': INTEGER,
        'required': True
    }
    duplicate_b = {
        'name': 'duplicate',
        'in': PATH,
        'description': 'duplicate_b',
        'type': STRING,
        'required': True
    }
    main_serializer = ParameterSerializer(many=True, data=[
        ID_IN_PATH,
        USERNAME_IN_PATH,
        duplicate_a,
        PAGE_IN_QUERY,
    ])
    assert main_serializer.is_valid(), main_serializer.errors
    main_parameters = main_serializer.save()

    sub_serializer = ParameterSerializer(many=True, data=[
        duplicate_b,
        PAGE_SIZE_IN_QUERY,
    ])
    assert sub_serializer.is_valid(), sub_serializer.errors
    sub_parameters = sub_serializer.save()

    merged_parameters = merge_parameter_lists(main_parameters, sub_parameters)

    assert len(merged_parameters) == 5

    assert find_parameter(merged_parameters, description='duplicate_b')
    assert not filter_parameters(merged_parameters, description='duplicate_a')
    assert find_parameter(merged_parameters, in_=PATH, name='id')
    assert find_parameter(merged_parameters, in_=PATH, name='username')
    assert find_parameter(merged_parameters, in_=QUERY, name='page')
    assert find_parameter(merged_parameters, in_=QUERY, name='page_size')
