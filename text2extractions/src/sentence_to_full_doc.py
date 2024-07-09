import re
import json
import spacy
import difflib
from collections import OrderedDict
from fuzzywuzzy import fuzz


def process_json(extracted_info, input_path):
    sentence = 0
    new_dict = {'file_name': input_path, 'testator_name': "", 'execution_date': "", 'full_text': "", 'extractions': {}}
    new_dict['extractions']['entities'] = []
    new_dict['extractions']['events'] = []
    for info in extracted_info:
        data = json.loads(info)
        print("assembling " + str(sentence + 1) + "th sentence in progress!")

        # first sentence is simple -- just add everything
        if sentence == 0:
            new_dict['full_text'] = data['text']

            # process entities
            for entity in data['entities']:
                entity_dict = {}
                new_id = "e" + str(len(new_dict['extractions']['entities']) + 1)
                entity_dict['id'] = new_id
                entity_dict['type'] = entity['type']
                entity_dict['texts'] = {}
                for text in entity['texts']:
                    entity_dict['texts'][text] = []
                    char_offsets = get_word_offsets(data['text'], text)
                    for offset in char_offsets:
                        id_char = {"sentence_id": sentence, "character_offsets": offset}
                        entity_dict['texts'][text].append(id_char)
                new_dict['extractions']['entities'].append(entity_dict)

            # process events
            new_events = []
            for event in data['events']:
                original_ordered_event = OrderedDict(event)
                new_key = 'sentence_id'
                new_value = sentence

                # Create a new OrderedDict with the added key-value pair at the specified index
                new_ordered_dict = OrderedDict(
                    list(original_ordered_event.items())[:2] +
                    [(new_key, new_value)] +
                    list(original_ordered_event.items())[2:]
                )
                new_events.append(dict(new_ordered_dict))
            new_dict['extractions']['events'] = new_events

        # from second sentence, things get complicated
        else:
            entity_id_map = {}
            dict_len = len(new_dict['full_text'])

            # add the text to "full text"
            new_dict['full_text'] += " " + data['text']

            # process entities
            for entity in data['entities']:
                entity_dict = {}
                # check if the entity type overlaps with any of the existing entities
                same_type = False
                for prev_entity in new_dict['extractions']['entities']:
                    # if there's an overlapping type, we need to check for if they refer to the same entity
                    if entity['type'] == prev_entity['type']:
                        same_type = True
                        # if it's the testator, we don't have to check (there's ought to be only one Testator)
                        if entity['type'] == "Testator":
                            original_id = entity['id']
                            new_id = prev_entity['id']
                            entity_id_map[original_id] = new_id

                            text_key_match = False
                            for text in entity['texts']:
                                for key, value in list(prev_entity['texts'].items()):
                                    if text == key:
                                        text_key_match = True
                                        char_offsets = get_word_offsets(data['text'], key)
                                        for offset in char_offsets:
                                            global_offset = [num + dict_len for num in offset]
                                            id_char = {"sentence_id": sentence, "character_offsets": global_offset}
                                            prev_entity['texts'][key].append(id_char)
                                if not text_key_match:
                                    prev_entity['texts'][text] = []
                                    char_offsets = get_word_offsets(data['text'], text)
                                    for offset in char_offsets:
                                        global_offset = [num + dict_len for num in offset]
                                        id_char = {"sentence_id": sentence, "character_offsets": global_offset}
                                        prev_entity['texts'][text].append(id_char)

                # if it's not a testator, we need to do a coreference resolution
                if same_type and entity['type'] != 'Testator':
                    coref_res = x_sentence_coref_res(new_dict['extractions']['entities'], entity, new_dict['full_text'])

                    # if it turns out that there's no antecedent, just add them as new entities
                    if not coref_res:
                        original_id = entity['id']
                        new_id = "e" + str(len(new_dict['extractions']['entities']) + 1)
                        entity_id_map[original_id] = new_id

                        entity_dict['id'] = new_id
                        entity_dict['type'] = entity['type']
                        entity_dict['texts'] = {}

                        for text in entity['texts']:
                            entity_dict['texts'][text] = []
                            char_offsets = get_word_offsets(data['text'], text)
                            for offset in char_offsets:
                                global_offset = [num + dict_len for num in offset]
                                id_char = {"sentence_id": sentence, "character_offsets": global_offset}
                                entity_dict['texts'][text].append(id_char)
                        new_dict['extractions']['entities'].append(entity_dict)

                    # if there's antecedent, append the entity to that antecedent
                    else:
                        for e in new_dict['extractions']['entities']:
                            if e['id'] == coref_res:
                                original_id = entity['id']
                                new_id = e['id']
                                entity_id_map[original_id] = new_id

                                text_key_match = False
                                for text in entity['texts']:
                                    for key, value in list(e['texts'].items()):
                                        if text == key:
                                            text_key_match = True
                                            char_offsets = get_word_offsets(data['text'], key)
                                            for offset in char_offsets:
                                                global_offset = [num + dict_len for num in offset]
                                                id_char = {"sentence_id": sentence, "character_offsets": global_offset}
                                                e['texts'][key].append(id_char)
                                    if not text_key_match:
                                        e['texts'][text] = []
                                        char_offsets = get_word_offsets(data['text'], text)
                                        for offset in char_offsets:
                                            global_offset = [num + dict_len for num in offset]
                                            id_char = {"sentence_id": sentence, "character_offsets": global_offset}
                                            e['texts'][text].append(id_char)

                # if it's a new type, we can just add them as new entities
                elif not same_type:
                    original_id = entity['id']
                    new_id = "e" + str(len(new_dict['extractions']['entities']) + 1)
                    entity_id_map[original_id] = new_id

                    entity_dict['id'] = new_id
                    entity_dict['type'] = entity['type']
                    entity_dict['texts'] = {}
                    for text in entity['texts']:
                        entity_dict['texts'][text] = []
                        char_offsets = get_word_offsets(data['text'], text)
                        for offset in char_offsets:
                            global_offset = [num + dict_len for num in offset]
                            id_char = {"sentence_id": sentence, "character_offsets": global_offset}
                            entity_dict['texts'][text].append(id_char)
                    new_dict['extractions']['entities'].append(entity_dict)

            if 'events' in data.keys():
                for event in data['events']:
                    event['id'] = "v" + str(len(new_dict['extractions']['events']) + 1)
                    update_id = update_dict_with_id_map(event, entity_id_map)

                    original_ordered_event = OrderedDict(update_id)
                    new_key = 'sentence_id'
                    new_value = sentence

                    # Create a new OrderedDict with the added key-value pair at the specified index
                    new_ordered_dict = OrderedDict(
                        list(original_ordered_event.items())[:2] +
                        [(new_key, new_value)] +
                        list(original_ordered_event.items())[2:]
                    )

                    new_dict['extractions']['events'].append(dict(new_ordered_dict))
        sentence += 1
    for entity in new_dict['extractions']['entities']:
        if entity['type'] == "Date":
            new_dict['execution_date'] = list(entity["texts"].keys())[-1]
        if entity['type'] == "Testator":
            proper_noun = find_proper_noun(entity["texts"].keys())
            new_dict['testator_name'] = proper_noun
    return new_dict


def get_word_offsets(text, target_word):
    offsets = []
    # This is for the special tokens (e.g., [Person-1], [Address-1], etc.)
    if target_word[0] == "[" and target_word[-1] == "]":
        pattern = re.compile(re.escape(target_word), re.IGNORECASE)
        for match in re.finditer(pattern, text):
            offsets.append((match.start(), match.end()))
    elif target_word[-1] == "." or target_word[-1] == "%":
        pattern = re.compile(r'\b' + re.escape(target_word), re.IGNORECASE)
        for match in re.finditer(pattern, text):
            offsets.append((match.start(), match.end()))
    else:
        pattern = re.compile(r'\b' + re.escape(target_word) + r'\b|\b' + re.escape(target_word) + r'(?=,)',
                             re.IGNORECASE)
        for match in re.finditer(pattern, text):
            offsets.append((match.start(), match.end()))
    return offsets


def find_overlapping_items_with_allowance(list1, list2, similarity_threshold=90):
    core = spacy.load("en_core_web_sm")
    overlapping_items = []
    for item1 in list1:
        for item2 in list2:
            similarity = fuzz.ratio(str(item1), item2)
            if similarity >= similarity_threshold:
                core1 = core(str(item1))
                core2 = core(str(item2))
                if len(core1) == 0 and core1[0].pos_ != "PRON" and len(core2) == 0 and core2[0].pos_ != "PRON":
                    overlapping_items.append((str(item1), item2, similarity))
    return overlapping_items


def x_sentence_coref_res(prev_entities, new_entity, text):
    nlp = spacy.load("en_coreference_web_trf")
    doc = nlp(text)
    overlap_dict = {}
    for cluster in doc.spans:
        overlap_list = find_overlapping_items_with_allowance(list(doc.spans[cluster]), new_entity['texts'])
        overlap_dict[doc.spans[cluster]] = len(overlap_list)

    max_key = max(overlap_dict, key=lambda k: overlap_dict[k])
    max_value = overlap_dict[max_key]

    if max_value != 0:
        prev_overlap_dict = {}
        for entity in prev_entities:
            if entity['type'] == new_entity['type']:
                overlap_list = find_overlapping_items_with_allowance(list(max_key), list(entity['texts'].keys()))
                prev_overlap_dict[entity['id']] = len(overlap_list)

        max_prev_key = max(prev_overlap_dict, key=lambda k: prev_overlap_dict[k])
        max_prev_value = prev_overlap_dict[max_prev_key]

        if max_prev_value != 0:
            return max_prev_key
        else:
            return False
    else:
        return False


def update_dict_with_id_map(input_dict, id_map):
    updated_dict = {}
    for key, value in input_dict.items():
        updated_dict[key] = []
        # Use the value from the id_map dictionary if it exists, otherwise keep the original value
        if type(value) == list:
            for v in value:
                updated_value = id_map.get(v, v)
                if updated_value not in updated_dict[key]:
                    updated_dict[key].append(updated_value)
        elif type(value) == dict:
            print("please check! There's a dict inside a dict: " + str(value))
            for k, v in value.items():
                if k in id_map:
                    updated_value = id_map.get(k, k)
                    if updated_value not in updated_dict[key]:
                        updated_dict[key].append(updated_value)
                elif v in id_map:
                    if type(v) == str:
                        updated_value = id_map.get(v, v)
                        if updated_value not in updated_dict[key]:
                            updated_dict[key].append(updated_value)
        else:
            updated_value = id_map.get(value, value)
            if updated_value not in updated_dict[key]:
                updated_dict[key].append(updated_value)
    return updated_dict


def find_pronouns(condition, char_offsets):
    core = spacy.load("en_core_web_sm")
    condition_token = core(condition)
    pronouns = {}
    for token in condition_token:
        if token.pos_ == "PRON":
            token_word_offsets = get_word_offsets(condition, str(token))
            true_word_offset_list = []
            for offset in token_word_offsets:
                true_word_offset = [offset[0] + char_offsets[0], offset[1] + char_offsets[0]]
                true_word_offset_list.append((offset, true_word_offset))
            pronouns[token] = true_word_offset_list
    return pronouns


def find_entity_set(dictionary, pronoun, character_offset):
    for entity in dictionary['extractions']['entities']:
        for text in entity['texts']:
            if text == pronoun:
                for char_offset in entity['texts'][text]:
                    if char_offset['character_offsets'] == character_offset:
                        return entity['texts']


def find_proper_noun(entity_set):
    longest_with_cap = ""
    current_longest = 0
    for text in entity_set:
        # for the anonymized wills
        if text[0] == "[":
            return text
        elif len(text) > current_longest and text[0].isupper():
            longest_with_cap = text
            current_longest = len(text)
    return longest_with_cap


def add_proper_noun(condition, character_offset, proper_noun):
    new_condition = condition[:character_offset[1] + 1] + "(=" + proper_noun + ")" + condition[character_offset[1]:]
    return new_condition


def union_strings(strings):
    n = 0
    total_string = ""
    while n < len(strings):
        string_to_compare = total_string
        total_string = ""
        matcher = difflib.SequenceMatcher(None, string_to_compare, strings[n])
        differences = list(matcher.get_opcodes())
        # Print the differences
        for tag, i1, i2, j1, j2 in differences:
            if tag == "equal":
                total_string += strings[n][j1:j2]
            else:
                if len(string_to_compare[i1:i2]) > len(strings[n][j1:j2]):
                    total_string += string_to_compare[i1:i2]
                else:
                    total_string += strings[n][j1:j2]
        n += 1
    return total_string


def condition_pronoun_replacement(dictionary):
    entities_copy = dictionary['extractions']['entities'][:]

    for entity in entities_copy:
        if entity['type'] == "Condition":
            # Create a copy of the keys to avoid RuntimeError
            texts_copy = list(entity['texts'].keys())
            for text in texts_copy:
                char_offsets = entity['texts'][text][0]['character_offsets']
                pronouns = find_pronouns(text, char_offsets)
                for pronoun in pronouns:
                    for char_offset in pronouns[pronoun]:
                        entity_set = find_entity_set(dictionary, str(pronoun), char_offset[1])
                        if entity_set is not None:
                            proper_noun = find_proper_noun(entity_set)
                            if proper_noun is not None:
                                new_condition = add_proper_noun(text, char_offset[0], proper_noun)
                                condition_list = [list(entity['texts'].keys())[0], new_condition]
                                union_condition = union_strings(condition_list)
                                entity['texts'][union_condition] = entity['texts'].pop(list(entity['texts'].keys())[0])
    return dictionary
