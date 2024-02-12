import nltk
import argparse
import re
import os
import json
import spacy
import spacy_experimental
from collections import OrderedDict
from nltk.tokenize import sent_tokenize
from fuzzywuzzy import fuzz

def process_json(extracted_info):
    sentence = 0
    new_dict = {}
    new_dict['full_text'] = ""
    new_dict['extractions'] = {}
    new_dict['extractions']['entities'] = []
    new_dict['extractions']['events'] = []
    for info in extracted_info:
        data = json.loads(info)
        print("processing the sentence " + str(sentence))
        if sentence == 0:
            new_dict['full_text'] = data['text']
            for entity in data['entities']:
                entity_dict = {}

                # original_id
                original_id = entity['id']
                new_id = "e"+str(len(new_dict['extractions']['entities'])+1)

                entity_dict['id'] = new_id
                entity_dict['type'] = entity['type']
                entity_dict['texts'] = {}
                for text in entity['texts']:
                    entity_dict['texts'][text] = []
                    char_offsets = get_word_offsets(data['text'], text)
                    for offset in char_offsets:
                        id_char = {}
                        id_char["sentence_id"] = sentence
                        id_char["character_offsets"] = offset
                        entity_dict['texts'][text].append(id_char)
                new_dict['extractions']['entities'].append(entity_dict)

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
        else:
            entity_id_map = {}
            new_dict['full_text'] += " " + data['text']

            for entity in data['entities']:
                entity_dict = {}
                # Check if the entity type overlaps with any of the existing entities
                same_type = False
                for prev_entity in new_dict['extractions']['entities']:
                    if entity['type'] == prev_entity['type']:
                        same_type = True
                        # if it's the testator, we don't have to do coreference resolution! (there's ought to be only one Testator)
                        if entity['type'] == "Testator":
                            original_id = entity['id']
                            new_id = prev_entity['id']
                            entity_id_map[original_id] = new_id

                            for text in entity['texts']:
                                for key, value in list(prev_entity['texts'].items()):
                                    if text == key:
                                        char_offsets = get_word_offsets(data['text'], key)
                                        for offset in char_offsets:
                                            id_char = {}
                                            id_char["sentence_id"] = sentence
                                            id_char["character_offsets"] = offset
                                            prev_entity['texts'][key].append(id_char)
                                    else:
                                        prev_entity['texts'][text] = []
                                        char_offsets = get_word_offsets(data['text'], text)
                                        for offset in char_offsets:
                                            id_char = {}
                                            id_char["sentence_id"] = sentence
                                            id_char["character_offsets"] = offset
                                            prev_entity['texts'][text].append(id_char)

                # if it's not a testator, we need to do a coreference resolution
                if same_type and entity['type'] != 'Testator':
                    coref_res = x_sentence_coref_res(new_dict['extractions']['entities'], entity, new_dict['full_text'])

                    # if it turns out that there's no antecedent, just add them as new entities
                    if coref_res == False:
                        original_id = entity['id']
                        new_id = "e"+str(len(new_dict['extractions']['entities'])+1)
                        entity_id_map[original_id] = new_id

                        entity_dict['id'] = new_id
                        entity_dict['type'] = entity['type']
                        entity_dict['texts'] = {}

                        for text in entity['texts']:
                            entity_dict['texts'][text] = []
                            char_offsets = get_word_offsets(data['text'], text)
                            for offset in char_offsets:
                                id_char = {}
                                id_char["sentence_id"] = sentence
                                id_char["character_offsets"] = offset
                                entity_dict['texts'][text].append(id_char)
                        new_dict['extractions']['entities'].append(entity_dict)

                    # if there's antecedent, append the entity to that antecedent
                    else:
                        for e in new_dict['extractions']['entities']:
                            if e['id'] == coref_res:
                                original_id = entity['id']
                                new_id = e['id']
                                entity_id_map[original_id] = new_id

                                for text in entity['texts']:
                                    for key, value in list(e['texts'].items()):
                                        if text == key:
                                            char_offsets = get_word_offsets(data['text'], key)
                                            for offset in char_offsets:
                                                id_char = {}
                                                id_char["sentence_id"] = sentence
                                                id_char["character_offsets"] = offset
                                                e['texts'][key].append(id_char)
                                        else:
                                            e['texts'][text] = []
                                            char_offsets = get_word_offsets(data['text'], text)
                                            for offset in char_offsets:
                                                id_char = {}
                                                id_char["sentence_id"] = sentence
                                                id_char["character_offsets"] = offset
                                                e['texts'][text].append(id_char)

                # if it's a new type, we can just add them as new entities
                elif not same_type:
                    original_id = entity['id']
                    new_id = "e"+str(len(new_dict['extractions']['entities'])+1)
                    entity_id_map[original_id] = new_id

                    entity_dict['id'] = new_id
                    entity_dict['type'] = entity['type']
                    entity_dict['texts'] = {}
                    for text in entity['texts']:
                        entity_dict['texts'][text] = []
                        char_offsets = get_word_offsets(data['text'], text)
                        for offset in char_offsets:
                            id_char = {}
                            id_char["sentence_id"] = sentence
                            id_char["character_offsets"] = offset
                            entity_dict['texts'][text].append(id_char)
                    new_dict['extractions']['entities'].append(entity_dict)

            if 'events' in data.keys():
                for event in data['events']:
                    event['id'] = "v"+str(len(new_dict['extractions']['events'])+1)
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
    return new_dict

def get_word_offsets(text, target_word):
    offsets = []
    # This is for the special tokens (e.g., [Person-1], [Address-1], etc.)
    if target_word[0] == "[" and target_word[-1] == "]":
      pattern = re.compile(re.escape(target_word), re.IGNORECASE)
      for match in re.finditer(pattern, text):
          offsets.append((match.start(), match.end()))
    else:
      pattern = re.compile(r'\b' + re.escape(target_word) + r'\b|\b' + re.escape(target_word) + r'(?=,)', re.IGNORECASE)
      for match in re.finditer(pattern, text):
          offsets.append((match.start(), match.end()))
    return offsets

def find_overlapping_items_with_allowance(list1, list2, similarity_threshold=70):
    overlapping_items = []
    for item1 in list1:
        for item2 in list2:
            similarity = fuzz.ratio(str(item1), item2)
            if similarity >= similarity_threshold:
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
        # Use the value from the id_map dictionary if it exists, otherwise keep the original value
        if type(value) == list:
          for v in value:
            updated_value = id_map.get(v, v)
            updated_dict[key] = updated_value
        else:
          updated_value = id_map.get(value, value)
          updated_dict[key] = updated_value

    return updated_dict