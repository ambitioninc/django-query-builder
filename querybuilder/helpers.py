def value_for_keypath(dict, keypath):
    """
    Returns the value of a keypath in a dictionary
    if the keypath exists or None if the keypath
    does not exist.
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


class Empty:
    pass


def copy_instance(instance):
    obj = Empty()
    obj.__class__ = instance.__class__
    # Copy references to everything.
    obj.__dict__ = instance.__dict__.copy()
    return obj
