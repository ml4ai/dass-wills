""" te_to_wm.py --
Convert text extractions to will model representation """

import argparse
import sys, os
import pickle
import json
import datetime
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
            word.upper()
            if (word.startswith("wm") or word == "te")
            else word.capitalize()
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
        "-p",
        "--provenance",
        action="store_true",
        help="Show the source text of each extracted attribute.",
    )

    parser.add_argument(
        "-s",
        "--serialize",
        action="store_true",
        help="Show the serialized string of each directive.",
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


def find_obj_with_id(list_of_objs, target_id):
    """Returns the obj given an id"""
    for item in list_of_objs:
        if item._id == target_id:
            return item
    print(f"error: no object found with id: {target_id}")
    return None


def find_objs_with_id(list_of_objs, target_ids):
    """Returns the objs given an id"""
    objs = []
    for target_id in target_ids:
        for item in list_of_objs:
            if item._id == target_id:
                objs.append(item)
    if len(objs) == 0:
        print(f"error: no object found with id: {target_id}")
    return objs


def find_objs_with_id(list_of_objs, target_ids):
    """Returns the objs given an id"""
    objs = []
    for target_id in target_ids:
        for item in list_of_objs:
            if item._id == target_id:
                objs.append(item)
    if len(objs) == 0:
        print(f"error: no object found with id: {target_id}")
    return objs


def find_unused(te_obj, used):
    """Returns the unused items in will extractions."""
    unused = []
    total_items = []
    unused_types = {}
    for type in te_obj:
        for item in te_obj[type]:
            total_items.append(item)
            if item["id"] not in used:
                if item["type"] not in unused_types:
                    unused_types[item["type"]] = [item["id"]]
                else:
                    unused_types[item["type"]].append(item["id"])
                unused.append(item)
    print(f"... Total items unused: {len(unused)} out of: {len(total_items)}")
    return unused, unused_types


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


def extract_assets(te,prov=False):
    """Returns a list of assets given a te dict."""

    assets = []
    for entity in te["entities"]:
        if entity["type"] == "Asset":
            asset_name = ", ".join(entity["texts"])
            asset_id = entity["id"]
            if prov:
                print(
                f"""... extracted asset with id: {asset_id} \
and name: {asset_name}"""
            )
            asset=WMAsset(name=asset_name, id=asset_id)
            asset.source_text=entity['texts']
            if prov:
                print(f"... source text from will: {asset.source_text}\n")
            assets.append(asset)
    return assets


def extract_beneficiaries(te,prov=False):
    """Returns a list of beneficiaries given
    a te dict. gets the name by first index.
    to-do: currently handles single beneficiary,
    add logic for multiple."""

    beneficiaries = []
    for entity in te["entities"]:
        if entity["type"] == "Beneficiary":
            beneficiary_name = list(entity["texts"].keys())[0]
            beneficiary_id = entity["id"]
            if prov:
                print(
                f"""... extracted beneficiary with\
 id: {beneficiary_id} and name: {beneficiary_name}"""
            )
            beneficiary=WMPerson(
                    name=beneficiary_name, id=beneficiary_id, dass_type="Beneficiary"
                )
            beneficiary.source_text=entity['texts']
            if prov:
                print(f"... source text from will: {beneficiary.source_text}\n")
            beneficiaries.append(beneficiary)
    return beneficiaries


def extract_conditions(te,prov=False):
    """Returns a list of conditions given
    a te dict. gets the text by first index."""

    conditions = []
    for entity in te["entities"]:
        if entity["type"] == "Condition":
            condition_text = list(entity["texts"].keys())[0]
            condition_id = entity["id"]
            if prov:
                print(
                f"""... extracted condition with\
 id: {condition_id} and text: {condition_text}"""
            )
            condition=WMConditional(condition=condition_text, id=condition_id)
            condition.source_text=entity["texts"]
            conditions.append(condition)
            if prov:
                print(f"... source text from will: {condition.source_text}\n")

    return conditions


def extract_testaor(te, used,prov=False):
    """Returns a the name of the testator.
    currently gets the testator name by the
    first index."""

    for entity in te["entities"]:
        if entity["type"] == "Testator":
            testator_name = list(entity["texts"].keys())[0]
            testator_id = entity["id"]
            if prov:
                print(
                f"""... extracted testator with id:\
 {testator_id} and name: {testator_name}"""
            )
            used.append(testator_id)
            testator=WMPerson(name=testator_name, id=testator_id, dass_type="Testator")
            testator.source_text=entity["texts"]

            if prov:
                print(f"... source text from will: {testator.source_text}\n")

            return testator
    print("Error: no testator found")
    return None


def extract_executors(te, used,prov=False):
    """Returns the list of executors.
    currently gets the executor name by the
    first index."""

    executors = []
    for entity in te["entities"]:
        if entity["type"] == "Executor":
            executor_name = list(entity["texts"].keys())[0]
            executor_id = entity["id"]
            if prov:
                print(
                f"""... extracted testator with\
 id: {executor_id} and name: {executor_name}"""
                )
            
            
            executor=WMPerson(name=executor_name, id=executor_id, dass_type="Executor")
            executor.source_text=entity["texts"]
            if prov:
                print(f"... source text from will: {executor.source_text}\n")
            executors.append(executor)
    return executors


################################################################################
#                                                                              #
#                               Fetch  Directives                              #
#                                                                              #
################################################################################


def infer_directives(te, beneficairies, assets, conditions, executors, used,prov=False, serialize=False):
    """Returns a list of beneficiaries given a te dict,
    beneficairies, and assets.
    to-do: currently handles single beneficiary, add
    logic for multiple."""
    directives = []
    bequeath_types = ["BequestAsset", "Bequest"]  ## add more types here
    for event in te["events"]:
        if event["type"] in bequeath_types:
            if event["type"] in ["BequestAsset", "Bequest"]:
                d_id = event["id"]
                d_type = event["type"]
                asset_id = event["Asset"]
                benefactor_id = event["Beneficiary"]
                condition_id = event["Condition"]
                if "Executor" in event:
                    executor_id = event["Executor"]
                else:
                    executor_id = None
                if type(condition_id) == list:
                    conditions_asset = find_objs_with_id(conditions, condition_id)

                else:
                    conditions_asset = [find_obj_with_id(conditions, condition_id)]
                conditions_ids = [condition._id for condition in conditions_asset]
                beneficiary = find_obj_with_id(beneficairies, benefactor_id)
                asset = find_obj_with_id(assets, asset_id)
                if executor_id:
                    executor = find_obj_with_id(executors, executor_id)
                else:
                    executor = None
                bequeath_directive = WMDirectiveBequeath(
                    beneficiaries=[beneficiary],
                    assets=[asset],
                    executor=executor,
                    conditions=conditions_asset,
                )

                used.append(asset_id)
                used.append(benefactor_id)
                used.extend(conditions_ids)
                if executor_id:
                    used.append(executor_id)

                condition_texts = [
                    condition._condition for condition in conditions_asset
                ]
                conditions_full_text = ", and ".join(condition_texts)
                bequeath_directive.type = d_type
                if prov:
                    print(f"... infered directive with id: {d_id}")
                if serialize:
                    print(
                    f"""... serialized directive: Bequest asset/s \
"{asset._name}" to "{beneficiary._name}" with following condition/s: {conditions_full_text}.\n"""
                    )
                directives.append(bequeath_directive)

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
    provenance=args.provenance
    serialize=args.serialize
    used_ids = []  # to keep track of what's used and what's not

    testator = extract_testaor(te_obj["extractions"], used_ids)

    ## match testator with existing database of people

    ## stub date of birth, to-do: replace with dynamic date
    dob_to_match = "1992-05-15"

    matching_testator = find_person_by_dob_and_name(dob_to_match, testator.name)

    if matching_testator:
        if provenance:
            print(
            f"Matching testator found from peoples db with id: {matching_testator['id']}"
        )
        if args.verbose:
            print(f"Testor detailed info:")
            pprint(matching_testator)
    else:
        print("No matching testator found.")

    ## extract other entities
    executors = extract_executors(te_obj["extractions"], used_ids,provenance)
    beneficiaries = extract_beneficiaries(te_obj["extractions"],provenance)
    conditions = extract_conditions(te_obj["extractions"],provenance)
    assets = extract_assets(te_obj["extractions"],provenance)
    directives = infer_directives(
        te_obj["extractions"], beneficiaries, assets, conditions, executors, used_ids,
        provenance,serialize
    )
    unused_items, unused_types = find_unused(te_obj["extractions"], used_ids)

    if args.verbose:
        print(f"... the following item types and ids are unused from TE json:")
        pprint(unused_types)

    will_model = WMWillModel(
        text=te_obj["full_text"],
        _date=te_obj["execution_date"],
        directives=directives,
        testator=testator,
    )
    ## add willmodel checksum
    will_model.checksum = None
    will_model_bytes = pickle.dumps(will_model)
    will_model.checksum = hashlib.sha256(will_model_bytes).hexdigest()
    print(f"... Will model Checksum: {will_model.checksum}")

    ## Save Will Model
    save_pickle_object(will_model, path_to_wm_obj)


if __name__ == "__main__":
    main()
