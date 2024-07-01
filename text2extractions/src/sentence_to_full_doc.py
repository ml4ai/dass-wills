import re
import json
import spacy
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
            # ak: currently I'm just assuming that the longest text with capitalization will be the testator's name
            longest_with_cap = ""
            current_longest = 0
            for key in entity["texts"].keys():
                if len(key) > current_longest and key[0].isupper():
                    longest_with_cap = key
                    current_longest = len(key)
            new_dict['testator_name'] = longest_with_cap
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
