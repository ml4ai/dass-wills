import re
import json
import spacy
import difflib
from collections import OrderedDict
from fuzzywuzzy import fuzz

nlp_core = spacy.load("en_core_web_sm")
nlp_coref = spacy.load("en_coreference_web_trf")


def get_global_offsets(text, target_word, full_text_len):
    char_offsets = get_word_offsets(text, target_word)
    return [[num + full_text_len for num in offset] for offset in char_offsets]


def store_entity_texts(entity_dict, text_key, offsets, sentence):
    entity_dict['texts'][text_key] = [{'sentence_id': sentence, 'character_offsets': offset} for offset in offsets]


def create_updated_entity(new_id, dict_to_add, entity_dict, full_text_len, data, entity, sentence):
    entity_dict.update({'id': new_id, 'type': entity['type'], 'texts': {}})
    for text in entity['texts']:
        offsets = get_global_offsets(data['text'], text, full_text_len)
        store_entity_texts(entity_dict, text, offsets, sentence)
    dict_to_add['extractions']['entities'].append(entity_dict)


def add_or_update_entities(entity_id_map, dict_to_add, full_text_len, data, entity, prev_entity, sentence):
    original_id = entity['id']
    if prev_entity:
        entity_id_map[original_id] = prev_entity['id']
        for text in entity['texts']:
            offsets = get_global_offsets(data['text'], text, full_text_len)
            if text in prev_entity['texts']:
                # Append new offsets instead of overwriting
                prev_entity['texts'][text].extend([{'sentence_id': sentence, 'character_offsets': offset} for offset in offsets])
            else:
                prev_entity['texts'][text] = [{'sentence_id': sentence, 'character_offsets': offset} for offset in offsets]
    else:
        new_id = "e" + str(len(dict_to_add['extractions']['entities']) + 1)
        create_updated_entity(new_id, dict_to_add, {}, full_text_len, data, entity, sentence)


def add_events(entity_id_map, dict_to_add, sentence, data):
    if sentence == 0:
        dict_to_add['extractions']['events'] = [
            update_event_dicts(event, sentence) for event in data['events']
        ]
    else:
        for event in data['events']:
            event['id'] = "v" + str(len(dict_to_add['extractions']['events']) + 1)
            event = update_dict_with_id_map(event, entity_id_map)
            dict_to_add['extractions']['events'].append(update_event_dicts(event, sentence))


def update_event_dicts(event, sentence):
    event_dict = OrderedDict(event)
    event_dict.update({'sentence_id': sentence})
    return dict(event_dict)


def process_json(extracted_info, input_path):
    sentence = 0
    new_dict = {
        'file_name': input_path,
        'testator_name': "",
        'execution_date': "",
        'full_text': "",
        'extractions': {'entities': [], 'events': []}
    }

    for info in extracted_info:
        data = json.loads(info)
        print(f"Assembling {sentence + 1}th sentence in progress!")

        entity_id_map = {}
        full_text_len = len(new_dict['full_text'])

        if sentence == 0:
            new_dict['full_text'] = data['text']
        else:
            new_dict['full_text'] += " " + data['text']

        for entity in data['entities']:
            prev_entity = next(
                (e for e in new_dict['extractions']['entities'] if e['type'] == entity['type']), None
            )
            if prev_entity and entity['type'] == "Testator":
                add_or_update_entities(entity_id_map, new_dict, full_text_len, data, entity, prev_entity, sentence)
            elif prev_entity:
                coref_res = x_sentence_coref_res(new_dict['extractions']['entities'], entity, new_dict['full_text'])
                add_or_update_entities(entity_id_map, new_dict, full_text_len, data, entity, prev_entity if coref_res else None, sentence)
            else:
                new_id = "e" + str(len(new_dict['extractions']['entities']) + 1)
                create_updated_entity(new_id, new_dict, {}, full_text_len, data, entity, sentence)

        if 'events' in data:
            add_events(entity_id_map, new_dict, sentence, data)

        sentence += 1

    update_testator_and_date(new_dict)

    return new_dict


def update_testator_and_date(new_dict):
    for entity in new_dict['extractions']['entities']:
        if entity['type'] == "Date":
            new_dict['execution_date'] = list(entity["texts"].keys())[-1]
        if entity['type'] == "Testator":
            proper_noun = find_proper_noun(entity["texts"].keys())
            new_dict['testator_name'] = proper_noun


def get_word_offsets(text, target_word):
    if target_word[0] == "[" and target_word[-1] == "]":
        pattern = re.compile(re.escape(target_word), re.IGNORECASE)
    elif target_word[-1] in {".", "%"}:
        pattern = re.compile(r'\b' + re.escape(target_word), re.IGNORECASE)
    else:
        pattern = re.compile(r'\b' + re.escape(target_word) + r'\b|\b' + re.escape(target_word) + r'(?=,)', re.IGNORECASE)

    return [(match.start(), match.end()) for match in re.finditer(pattern, text)]


def find_overlapping_items_with_allowance(list1, list2, similarity_threshold=90):
    overlapping_items = []
    for item1 in list1:
        for item2 in list2:
            similarity = fuzz.ratio(str(item1), item2)
            if similarity >= similarity_threshold:
                core1, core2 = nlp_core(str(item1)), nlp_core(str(item2))
                if core1 and core1[0].pos_ != "PRON" and core2 and core2[0].pos_ != "PRON":
                    overlapping_items.append((str(item1), item2, similarity))
    return overlapping_items


def x_sentence_coref_res(prev_entities, new_entity, text):
    doc = nlp_coref(text)
    overlap_dict = {
        cluster: len(find_overlapping_items_with_allowance(list(doc.spans[cluster]), new_entity['texts']))
        for cluster in doc.spans
    }

    max_key = max(overlap_dict, key=overlap_dict.get, default=None)
    max_value = overlap_dict.get(max_key, 0)

    if max_value != 0:
        prev_overlap_dict = {
            entity['id']: len(find_overlapping_items_with_allowance(list(max_key), list(entity['texts'].keys())))
            for entity in prev_entities if entity['type'] == new_entity['type']
        }
        return max(prev_overlap_dict, key=prev_overlap_dict.get, default=False)
    return False


def update_dict_with_id_map(input_dict, id_map):
    updated_dict = {}
    for key, value in input_dict.items():
        updated_values = []

        if isinstance(value, list):
            updated_values = [id_map.get(v, v) for v in value]
        elif isinstance(value, dict):
            for k, v in value.items():
                updated_value = id_map.get(k, k)
                if updated_value not in updated_values:
                    updated_values.append(updated_value)
                if isinstance(v, str) and id_map.get(v, v) not in updated_values:
                    updated_values.append(id_map.get(v, v))
        else:
            updated_values = [id_map.get(value, value)]

        updated_dict[key] = updated_values
    return updated_dict


def find_pronouns(condition, char_offsets):
    doc = nlp_core(condition)
    pronouns = {
        token: [(offset, [offset[0] + char_offsets[0], offset[1] + char_offsets[0]]) for offset in get_word_offsets(condition, str(token))]
        for token in doc if token.pos_ == "PRON"
    }
    return pronouns


def find_entity_set(entities, pronoun, char_offset):
    # Loop through the entities to find a matching pronoun with the same character offset
    for entity in entities:
        # Ensure that entity['texts'] is a dictionary
        if isinstance(entity['texts'], dict):
            for text, offsets in entity['texts'].items():
                if text == pronoun:
                    if any(char_offset == offset['character_offsets'] for offset in offsets):
                        return entity['texts']
    return None


def find_proper_noun(entity_set):
    return max(
        (text for text in entity_set if text[0].isupper() or text[0] == "["),
        key=len,
        default=""
    )


def add_proper_noun(condition, char_offset, proper_noun):
    return condition[:char_offset[1] + 1] + f"(={proper_noun})" + condition[char_offset[1]:]


def union_strings(strings):
    total_string = ""
    for string in strings:
        matcher = difflib.SequenceMatcher(None, total_string, string)
        total_string = "".join(
            max(matcher.get_opcodes(), key=lambda x: len(string[x[3]:x[4]]))[0]
            for _, i1, i2, j1, j2 in matcher.get_opcodes()
            if string[j1:j2]
        )
    return total_string


def condition_pronoun_replacement(dictionary):
    for entity in dictionary['extractions']['entities']:
        if entity['type'] == "Condition":
            texts_copy = list(entity['texts'].keys())
            for text in texts_copy:
                char_offsets = entity['texts'][text]
                pronouns = find_pronouns(text, char_offsets[0]['character_offsets'])

                # Create a list of replacements to be applied
                replacements = []

                for pronoun, offsets in pronouns.items():
                    entity_set = find_entity_set(dictionary['extractions']['entities'], str(pronoun), offsets[0][1])
                    if entity_set:
                        proper_noun = find_proper_noun(entity_set)
                        if proper_noun:
                            for offset in offsets:
                                replacements.append({
                                    'start': offset[0][0],
                                    'end': offset[0][1],
                                    'replacement': f"{pronoun} (={proper_noun})"
                                })

                # Sort replacements by start index
                replacements.sort(key=lambda x: x['start'])

                # Apply replacements
                new_condition = []
                last_end = 0

                for rep in replacements:
                    # Append text before the replacement
                    new_condition.append(text[last_end:rep['start']])
                    # Append the replacement text
                    new_condition.append(rep['replacement'])
                    # Update the end position
                    last_end = rep['end']

                # Append any remaining text after the last replacement
                new_condition.append(text[last_end:])
                new_condition = ''.join(new_condition)

                if new_condition != text:
                    # Update the condition with the modified text
                    entity['texts'][new_condition] = char_offsets
                    del entity['texts'][text]

    return dictionary
