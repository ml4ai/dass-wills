""" te_to_wm.py --
Convert text extractions to will model representation """

import argparse
import sys, os
import pickle
import json
import datetime
import re
from pprint import pprint
import hashlib

################################################################################
#                                                                              #
#                                  UTILITIES                                   #
#                                                                              #
################################################################################


def path_to_module_name(path):
    """Returns the name of the module given its
    path based on the Schema; essentially converts
    snake_case to CamelCase"""
    file_name = path.split("/")[-1]
    module_name = None
    if "wm" in file_name or "te" in file_name:
        module_name = file_name.split(".")[0]
        module_name = module_name.split("_")
        module_name = [
            (
                word.upper()
                if (word.startswith("wm") or word == "te")
                else word.capitalize()
            )
            for word in module_name
        ]
        module_name = "".join(module_name)
    return module_name


def cmd_line_invocation():
    desc_text = """Convert text extractions to 
    will model representation."""
    parser = argparse.ArgumentParser(description=desc_text)
    parser.add_argument(
        "-t",
        "--path-to-te",
        type=str,
        required=True,
        help="Input path to the will's text extractions json file.",
    )

    parser.add_argument(
        "-o",
        "--path-to-wm-obj",
        type=str,
        required=True,
        help="Output path to the converted will model's pickle file.",
    )

    parser.add_argument(
        "-x",
        "--highlight",
        action="store_true",
        help="Highlight the text used from the will.\
        The attributes related to part of the \
        text is passed for further processing. ",
    )

    parser.add_argument(
        "-p",
        "--provenance",
        action="store_true",
        help="Print the source text of each extracted attribute.",
    )

    parser.add_argument(
        "-s",
        "--serialize",
        action="store_true",
        help="Print the serialized version of each directive.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity.",
    )

    args = parser.parse_args()
    return args


def load_json_object(path):
    """Load the dict object from the json file."""
    with open(path, "rb") as f:
        obj = json.load(f)
        print(f"... Successfully loaded json from file {path}")
    f.close()
    return obj


def save_pickle_object(obj, path):
    """Save an object as a pickle file."""
    with open(path, "wb") as f:
        pickle.dump(obj, f)
        print(
            f"... Successfully saved \
Will Model pickle object to file {path}"
        )


def find_obj_with_id(list_of_objs, target_ids):
    """Returns the obj given an id"""
    if not isinstance(target_ids, list):
        # Single ID case
        for item in list_of_objs:
            if item._id == target_ids:
                return item
        print(f"Error: No object found with ID: {target_ids}")
        return None

    # Multiple IDs case
    objs = [item for item in list_of_objs if item._id in target_ids]
    
    if not objs:
        print(f"Error: No objects found with IDs: {target_ids}")
    
    return objs

def get_obj_str(obj):
    """Returns the string identifier of an obj"""
    if not type(obj) == list:
        return str(obj)
    else:
        strd_output=','.join(obj)
        return strd_output

def find_unused(te_obj, used):
    """Returns the unused items in will extractions."""
    unused = []
    total_items = []
    unused_types = {}
    for type_obj in te_obj:
        for item in te_obj[type_obj]:
            total_items.append(item)
            if item["id"] not in used:
                type_item=get_obj_str(item["type"])
                if type_item not in unused_types:
                    unused_types[type_item] = [item["id"]]
                else:
                    unused_types[type_item].append(item["id"])
                unused.append(item)
    print(f"... Total items unused: {len(unused)} out of: {len(total_items)}")
    return unused, unused_types


def remove_surplus_assets(input_string):
    """Removes surplus asset names given an asset name string."""
    pattern = re.compile(r"\ball\b.*?(property|estate)")
    match = pattern.search(input_string)
    if match:
        concise_property = "All the rest of " + match.group(1).strip().capitalize()
        if ' in ' in input_string:
            concise_property = concise_property+' in ' +str(input_string.split(' in ')[1:])
        elif ' inside ' in input_string:
            concise_property = concise_property+' in ' +str(input_string.split(' inside ')[1:])

        return concise_property
    return input_string


def highlight_used_text(te_obj, used_ids, sentence_ids=[], highlight=False):
    """Highlight used part of the will."""
    will_text = te_obj["full_text"]
    will_text_list = list(will_text)
    entities = te_obj["extractions"]["entities"]
    all_offsets = []
    for entity in entities:
        if entity["id"] in used_ids:
            texts = entity["texts"]
            for word in texts:
                for offset in entity["texts"][word]:
                    char_offset = offset["character_offsets"]
                    all_offsets.append([char_offset[0], char_offset[1] + 1])
    all_offsets = sorted(all_offsets, key=lambda x: x[0])
    aligned_offsets = []
    prev = None
    for offset in all_offsets:
        if prev != None:
            if prev[1] >= offset[0]:
                offset[0] = prev[1] + 1
            if offset[0] < offset[1]:
                aligned_offsets.append(offset)
            else:
                continue
        else:
            aligned_offsets.append(offset)
        prev = offset
    edit_text_list = list(will_text)
    color_offset = 0
    for offset in aligned_offsets:
        word_from_will = "".join(will_text_list[offset[0] : offset[1]])
        colored_word = "\033[32m" + word_from_will + "\033[0m"
        edit_text_list[offset[0] + color_offset : offset[1] + color_offset] = (
            colored_word
        )
        color_offset += len(colored_word) - len(word_from_will)
    interm_text = "".join(edit_text_list)
    sentences = re.split(r"\. |\.\x1b", interm_text)
    sentences_raw = will_text.split(". ")
    for s_id in sentence_ids:
        given_sentence = sentences_raw[s_id]
        colored_sentence = "\033[32m" + given_sentence + "\033[0m"
        sentences[s_id] = colored_sentence
    final_text = ". ".join(sentences)
    if highlight:
        print("Highlighted used text:\n", final_text)
    return final_text


def fetch_objects(entities, target_ids, used):
    """Returns the list of objects and their names."""

    if target_ids is None:
        return None, None

    objs = find_obj_with_id(entities, target_ids)
    if not objs:
        return None, None

    if isinstance(target_ids, list):
        used.extend(target_ids)
        obj_names = " and ".join(
            [
                obj._name if hasattr(obj, "_name")
                else obj._condition if hasattr(obj, "_condition")
                else ""
                for obj in objs
            ]
        )
    else:
        used.append(target_ids)
        obj_names = objs._name if hasattr(objs, "_name") else objs._condition if hasattr(objs, "_condition") else ""
        objs = [objs]

    return objs, obj_names



def serialize_directive(d_id, asset, beneficiary, condition, executor):
    "A stringbuilder that builds a serialized directive"

    directive_text = f"""... serialized directive with id {d_id}: Bequest asset/s \
'{asset}' to '{beneficiary}'"""

    if condition:
        directive_text += f" with following conditions: {condition}"
    if executor:
        directive_text += f". The name of executor is {executor}"
    directive_text += "."

    return directive_text


################################################################################
#                                                                              #
#                               Importing Modules                              #
#                                                                              #
################################################################################


schema_paths = ["schemas/model/wm", "schemas/model/te"]
for model_path in schema_paths:
    for model_file in os.listdir(model_path):
        module = path_to_module_name(model_file)
        if module:
            import_p1 = f"from {model_path.replace('/','.')}"
            import_p2 = f".{model_file.split('.')[0]} import {module}"
            import_cmd = import_p1 + import_p2
            """ roughly translates to
    from schemas.model.{wm,te}.{model_file} import {module} """
            exec(import_cmd)


################################################################################
#                                                                              #
#                               Extracting entities                            #
#                                                                              #
################################################################################


def extract_assets(te, prov=False, verbose=False):
    """Returns a list of assets given a te dict."""
    assets = []
    entities = te["entities"][0]
    for entity in entities:
        if entity.lower() == 'asset':    
            c_e = entities[entity]
            for asset_e in c_e:
                asset_name = asset_e['description']
                # asset_name = remove_surplus_assets(asset_name.lower()) ## this feature is ignored for now
                asset_id = asset_e["id"]
                if verbose:
                    print(
                        f"""... extracted asset with id: {asset_id} \
    and name: {asset_name}"""
                    )
                asset = WMAsset(name=asset_name, id=asset_id)
                asset.source_text = asset_e['description']
                if prov:
                    print(f"... source text from will: {asset.source_text}\n")
                assets.append(asset)
    return assets


def extract_beneficiaries(te, prov=False, verbose=False):
    """Returns a list of beneficiaries given
    a te dict. gets the name by first index.
    to-do: currently handles single beneficiary,
    add logic for multiple."""

    beneficiaries = []
    entities = te["entities"][0]
    for entity in entities:
        if entity.lower() == 'beneficiary':    
            c_e = entities[entity]
            for beneficiary_e in c_e:
                beneficiary_name = beneficiary_e['name']
                beneficiary_id = beneficiary_e["id"]
                if verbose:
                    print(
                        f"""... extracted beneficiary with\
    id: {beneficiary_id} and name: {beneficiary_name}"""
                    )
                beneficiary = WMPerson(
                    name=beneficiary_name, id=beneficiary_id, dass_type="Beneficiary"
                )
                beneficiary.source_text = beneficiary_e['name']
                if prov:
                    print(f"... source text from will: {beneficiary.source_text}\n")
                beneficiaries.append(beneficiary)
    return beneficiaries


def extract_conditions(te, prov=False, verbose=False):
    """Returns a list of conditions given
    a te dict. gets the text by first index."""

    conditions = []
    entities = te["entities"][0]
    for entity in entities:
        if entity.lower() == 'condition':    
            c_e = entities[entity]
            for condition_e in c_e:
                condition_text = condition_e['text']
                condition_id = condition_e["id"]
                if verbose:
                    print(
                        f"""... extracted condition with\
    id: {condition_id} and text: {condition_text}"""
                    )
                condition = WMConditional(condition=condition_text, id=condition_id)
                condition.source_text = condition_e['text']
                conditions.append(condition)
                if prov:
                    print(f"... source text from will: {condition.source_text}\n")

    return conditions


def extract_testaor(te, used, prov=False, verbose=False):
    """Returns a the name of the testator.
    currently gets the testator name by the
    first index."""
    entities = te["entities"][0]
    for entity in entities:
        if entity.lower() == 'testator':
            t_entity =  entities[entity]
            testator_name = t_entity['name']
            print(f"Testator: ", testator_name)
            testator_id = t_entity["id"]
            if verbose:
                print(
                    f"""... extracted testator with id:\
 {testator_id} and name: {testator_name}"""
                )
            used.append(testator_id)
            testator = WMPerson(
                name=testator_name, id=testator_id, dass_type="Testator"
            )
            testator.source_text = t_entity['name']

            if prov:
                print(f"... source text from will: {testator.source_text}\n")

            return testator
    print("Error: no testator found")
    return None


def extract_executors(te, used, prov=False, verbose=False):
    """Returns the list of executors.
    currently gets the executor name by the
    first index."""

    executors = []
    entities = te["entities"][0]
    for entity in entities:
        if entity.lower() == 'executor':    
            c_e = entities[entity]
            for executor_e in c_e:
                executor_name = executor_e['name']
                executor_id = executor_e["id"]
                if verbose:
                    print(
                        f"""... extracted testator with\
    id: {executor_id} and name: {executor_name}"""
                    )
                executor = WMPerson(
                    name=executor_name, id=executor_id, dass_type="Executor"
                )
                executor.source_text = executor_name
                if prov:
                    print(f"... source text from will: {executor.source_text}\n")
                executors.append(executor)
    return executors


################################################################################
#                                                                              #
#                               Fetch  Directives                              #
#                                                                              #
################################################################################


def infer_directives(
    te,
    beneficairies,
    assets,
    conditions,
    executors,
    used,
    s_ids,
    prov=False,
    serialize=False,
):
    """Returns a list of beneficiaries given a te dict,
    beneficairies, and assets.
    to-do: currently handles single beneficiary, add
    support for multiple."""
    directives = []
    bequeath_types = ["BequestAsset", "Bequest"]  ## add more types here
    for event in te["events"]:
        type_event=get_obj_str(event["type"])
        try:
            if type_event in bequeath_types:
                # if type_event in ["BequestAsset", "Bequest"]:
                    ## processing entities
                    d_id = event["id"]
                    d_type = type_event
                    asset_id = event["Asset"]
                    benefactor_id = event["Beneficiary"]
                    condition_id = event["Condition"] if "Condition" in event else None
                    condition_id = condition_id if condition_id else None
                    executor_id = event["Executor"] if "Executor" in event else None
                    executor_id = executor_id if executor_id else None
                    beneficiary_fetched, b_name = fetch_objects(
                        beneficairies, benefactor_id, used
                    )
                    asset_fetched, a_name = fetch_objects(assets, asset_id, used)
                    condition_fetched, c_name = fetch_objects(
                        conditions, condition_id, used
                    )
                    executor_fetched, e_name = fetch_objects(executors, executor_id, used)
                    serialized_text = serialize_directive(
                        d_id, a_name, b_name, c_name, e_name
                    )

                    if not (beneficiary_fetched ):
                        print(f'... error fetching beneficiaries of bequest event with id: {d_id}')
                        continue
                    if not (asset_fetched ):
                        print(f'... error fetching assets of bequest event with id: {d_id}')
                        continue
                    ## creating bequeath directive
                    bequeath_directive = WMDirectiveBequeath(
                        beneficiaries=beneficiary_fetched,
                        assets=asset_fetched,
                        executor=executor_fetched,
                        conditions=condition_fetched,
                        serialized_text=serialized_text,
                    )
                    bequeath_directive.type = d_type
                    bequeath_directive._id = d_id
                    ## creating bequeath directive
                    if prov:
                        print(f"... infered directive with id: {d_id}")
                    if serialize:
                        print(serialized_text)
                    print(serialized_text)
                    directives.append(bequeath_directive)
                    
        except Exception as e:
            print(e)
            print("... error processing a bequeath event.")
            pass 
    return directives


################################################################################
#                                                                              #
#                               Match Testator from database                   #
#                                                                              #
################################################################################


def find_person_by_dob_and_name(dob, full_name):
    """Finds a person in the provided data based on
    their date of birth (DOB) and full name.
    """
    ## default path, replace later with dynamic path
    json_file_path = "ORACLES/people_db.json"
    peoples_obj = load_json_object(json_file_path)

    for person in peoples_obj:
        if person["date_of_birth"] == dob and person["full_name"] == full_name:
            return person
    return None


################################################################################
#                                                                              #
#                              Driver Code                                     #
#                                                                              #
################################################################################


def main():
    """Load the te json,
    fetch the testator, assets, and beneficiaries.
    Infer the directives.
    Add all of these to the WM
    Output the WM to a pickle file."""

    args = cmd_line_invocation()
    path_to_te_json = args.path_to_te
    path_to_wm_obj = args.path_to_wm_obj
    te_obj = load_json_object(path_to_te_json)
    provenance = args.provenance
    verbose = args.verbose
    serialize = args.serialize
    highlight = args.highlight
    used_ids = []  # to keep track of what's used and what's not
    sentence_ids = []
    testator = extract_testaor(te_obj["extractions"], used_ids)

    ## extract entities  in the directive
    executors = extract_executors(te_obj["extractions"], used_ids, provenance, verbose)
    beneficiaries = extract_beneficiaries(te_obj["extractions"], provenance, verbose)
    conditions = extract_conditions(te_obj["extractions"], provenance, verbose)
    assets = extract_assets(te_obj["extractions"], provenance, verbose)
    directives = infer_directives(
        te_obj["extractions"],
        beneficiaries,
        assets,
        conditions,
        executors,
        used_ids,
        sentence_ids,
        provenance,
        serialize,
    )
    # unused_items, unused_types = find_unused(te_obj["extractions"], used_ids)
    # highlight_used_text(te_obj, used_ids, sentence_ids, highlight)
    # if args.verbose:
    #     print(f"... the following item types and ids are unused from TE json:")
    #     pprint(unused_types)

    will_model = WMWillModel(
        text='te_obj["full_text"]',
        # text='te_obj["full_text"]',
        _date=te_obj["date_of_will"],
        directives=directives,
        testator=testator,
    )
    ## add willmodel checksum
    will_model.checksum = None
    will_model_bytes = pickle.dumps(will_model)
    will_model.checksum = hashlib.sha256(will_model_bytes).hexdigest()
    ## Save Will Model
    save_pickle_object(will_model, path_to_wm_obj)


if __name__ == "__main__":
    main()
