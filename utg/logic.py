# coding: utf-8

from utg import relations as r


def get_property_relations():
    return [relation
            for relation in r.__dict__.itervalues()
            if relation != r.WORD_PROPERTY and isinstance(relation, type) and issubclass(relation, r.WORD_PROPERTY)]


def get_default_properties():
    values = {}

    for relation in get_property_relations():
        values[relation] = relation.records[0]

    values[r.WORD_TYPE] = None

    return values

def get_verbose_to_relations():
    values = {}

    for relation in get_property_relations():
        for record in relation.records:
            values[record.verbose_id] = record

    return values


def _keys_generator(left, right, restrictions):
    from utg.data import PRESETS

    if not right:
        yield []
        return

    central, right = right[0], right[1:]

    # if property is in preset
    for preset_owner, preset_slave in PRESETS.iteritems():
        if preset_slave._relation == central and preset_owner in left:
            for tail in _keys_generator(left + [preset_slave], right, restrictions):
                yield [preset_slave] + tail
            return

    # if property in restrictions
    for used_property in left:
        if used_property in restrictions and central in restrictions[used_property]:
            for tail in _keys_generator(left + [None], right, restrictions):
                yield [None] + tail
            return

    for record in central.records:
        for tail in _keys_generator(left + [record], right, restrictions):
            yield [record] + tail

    return


def _get_cache(schema, restrictions):
    cache = {}
    inverted_cache = []

    for i, key in enumerate(_keys_generator([], schema, restrictions=restrictions)):
        cache[tuple(key)] = i
        inverted_cache.append(tuple(key))

    return cache, inverted_cache


def _populate_key_with_presets(key, schema):
    from utg.data import PRESETS

    replaces = {}

    for property in key:
        if property not in PRESETS:
            continue

        replace = PRESETS[property]
        replaces[replace._relation] = replace

    if not replaces:
        return

    for index, property_group in enumerate(schema):
        if property_group in replaces:
            key[index] = replaces[property_group]


def get_caches(restrictions):

    caches = {}
    inverted_caches = {}

    for word_type in r.WORD_TYPE.records:
        cache, inverted_cache = _get_cache(word_type.schema, restrictions[word_type])

        caches[word_type] = cache
        inverted_caches[word_type] = inverted_cache


    return caches, inverted_caches


def get_nearest_key(key, available_keys):
    best_key = None
    best_similarity = -1

    for available_key in available_keys:
        current_similarity = 0
        for index, (key_property, available_key_property) in enumerate(zip(key, available_key)):
            if key_property == available_key_property:
                current_similarity += (1 + 0.01 * index) # first elements in schema has less priority

        if current_similarity > best_similarity:
            best_similarity = current_similarity
            best_key = available_key

    return best_key


def _raw_keys_generator(left, key, schema):
    from utg.data import PRESETS

    if not key:
        yield []
        return

    schema_head, schema_tail = schema[0], schema[1:]
    key_head, key_tail = key[0], key[1:]

    # if head is in preset
    for preset_owner, preset_slave in PRESETS.iteritems():
        if preset_slave == key_head and preset_owner in left:
            key_head = None
            break


    if key_head is not None:
        for tail in _raw_keys_generator(left + [key_head], key_tail, schema_tail):
            yield [key_head] + tail
        return

    for head in schema_head.records:
        for tail in _raw_keys_generator(left + [head], key_tail, schema_tail):
            yield [head] + tail

    return


def _get_raw_cache(keys, schema):
    cache = {}

    for index, key in enumerate(keys):
        for raw_key in _raw_keys_generator([], key, schema):
            cache[tuple(raw_key)] = index

    return cache


def get_raw_caches(inverted_caches):
    caches = {}

    for word_type in r.WORD_TYPE.records:
        cache = _get_raw_cache(inverted_caches[word_type], word_type.schema)

        caches[word_type] = cache

    return caches


def pretty_format_current_keys_cache():
    import pprint

    from utg import data

    return pprint.pformat(data.WORDS_CACHES)
