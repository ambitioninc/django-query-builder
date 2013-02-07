def value_for_keypath(dict, keypath):
    """
    Returns the value of a keypath in a dictionary
    if the keypath exists or None if the keypath
    does not exist.

    >>> value_for_keypath({}, '')
    {}
    >>> value_for_keypath({}, 'fake')

    >>> value_for_keypath({}, 'fake.path')

    >>> value_for_keypath({'fruit': 'apple'}, '')
    {'fruit': 'apple'}
    >>> value_for_keypath({'fruit': 'apple'}, 'fruit')
    'apple'
    >>> value_for_keypath({'fruit': 'apple'}, 'fake')

    >>> value_for_keypath({'fruit': 'apple'}, 'fake.path')

    >>> value_for_keypath({'fruits': {'apple': 'red', 'banana': 'yellow'}}, '')
    {'fruits': {'apple': 'red', 'banana': 'yellow'}}
    >>> value_for_keypath({'fruits': {'apple': 'red', 'banana': 'yellow'}}, 'fruits')
    {'apple': 'red', 'banana': 'yellow'}
    >>> value_for_keypath({'fruits': {'apple': 'red', 'banana': 'yellow'}}, 'fruits.apple')
    'red'
    >>> value_for_keypath({'fruits': {'apple': {'color': 'red', 'taste': 'good'}}}, 'fruits.apple')
    {'color': 'red', 'taste': 'good'}
    >>> value_for_keypath({'fruits': {'apple': {'color': 'red', 'taste': 'good'}}}, 'fruits.apple.color')
    'red'
    >>> value_for_keypath({'fruits': {'apple': {'color': 'red', 'taste': 'good'}}}, 'fruits.apple.taste')
    'good'
    """

    if len(keypath) == 0:
        return dict

    keys = keypath.split('.')
    value = dict
    for key in keys:
        if key in value:
            value = value[key]
        else:
            return None

    return value


def set_value_for_keypath(item, keypath, value, create_if_needed=False, delimeter='.'):
    """
    Sets the value for a keypath in a dictionary
    if the keypath exists. This modifies the
    original dictionary.

    >>> set_value_for_keypath({}, '', None)

    >>> set_value_for_keypath({}, '', 'test value')

    >>> set_value_for_keypath({'fruit': 'apple'}, '', None)

    >>> set_value_for_keypath({'fruit': 'apple'}, '', 'test value')

    >>> set_value_for_keypath({'fruit': 'apple'}, 'fruit', None)
    {'fruit': None}
    >>> set_value_for_keypath({'fruit': 'apple'}, 'fruit', 'test value')
    {'fruit': 'test value'}
    >>> set_value_for_keypath({'fruit': 'apple'}, 'fake', None)

    >>> set_value_for_keypath({'fruit': 'apple'}, 'fake', 'test value')

    >>> set_value_for_keypath({'fruit': {'apple': 'red'}}, 'fruit.apple', 'green')
    {'fruit': {'apple': 'green'}}
    >>> set_value_for_keypath({'fruit': {'apple': 'red'}}, 'fruit.apple', None)
    {'fruit': {'apple': None}}
    >>> set_value_for_keypath({'fruit': {'apple': {'color': 'red'}}}, 'fruit.apple.fake', 'green')

    >>> set_value_for_keypath({'fruit': {'apple': {'color': 'red'}}}, 'fruit.apple.color', 'green')
    {'fruit': {'apple': {'color': 'green'}}}

    >>> set_value_for_keypath({'fruit': {'apple': {'color': 'red'}}}, 'fruit.apple.color', {'puppies': {'count': 10, 'breed':'boxers'}})
    {'fruit': {'apple': {'color': {'puppies': {'count': 10, 'breed': 'boxers'}}}}}

    >>> set_value_for_keypath({'fruit': {'apple': {'color': 'red'}}}, 'fruit.apple.animals', {'puppies': {'count': 10, 'breed':'boxers'}}, create_if_needed=True)
    {'fruit': {'apple': {'color': 'red', 'animals': {'puppies': {'count': 10, 'breed': 'boxers'}}}}}

    """

    if len(keypath) == 0:
        return None

    keys = keypath.split(delimeter)
    if len(keys) > 1:
        key = keys[0]

        if create_if_needed:
            item[key] = item.get(key, {})

        if key in item:
            if set_value_for_keypath(item[key], delimeter.join(keys[1:]), value,
                                     create_if_needed=create_if_needed, delimeter=delimeter):
                return item

        return None

    if create_if_needed:
        item[keypath] = item.get(keypath, {})

    if keypath in item:
        item[keypath] = value
        return item
    else:
        return None
