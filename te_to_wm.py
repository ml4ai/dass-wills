""" te_to_wm.py --
Convert text extractions to will model representation """

import argparse
import sys, os
import pickle
import json
import datetime


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
        print(f"... Successfully saved \
Will Model pickle object to file {path}")


def find_obj_with_id(list_of_objs, target_id):
    """Returns the obj given an id"""
    for item in list_of_objs:
        if item._id == target_id:
            return item
    print(f"error: no object found with id: {target_id}")
    return None


def find_objs_with_id(list_of_objs, target_ids):
    """Returns the objs given an id"""
    objs=[]
    for target_id in target_ids:
        for item in list_of_objs:
            if item._id == target_id:
                objs.append(item)
    if len(objs)==0:
        print(f"error: no object found with id: {target_id}")
    return objs


def find_objs_with_id(list_of_objs, target_ids):
    """Returns the objs given an id"""
    objs=[]
    for target_id in target_ids:
        for item in list_of_objs:
            if item._id == target_id:
                objs.append(item)
    if len(objs)==0:
        print(f"error: no object found with id: {target_id}")
    return objs


def find_unused(te_obj, used):
    """Returns the unused items in will extractions."""
    unused=[]
    total_items=[]
    for type in te_obj:
        for item in te_obj[type]:
            total_items.append(item)
            if item['id'] not in used:
                unused.append(item)
    print(f"... Total items unused: {len(unused)} out of: {len(total_items)}")
    return unused

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


def extract_assets(te):
    """Returns a list of assets given a te dict."""

    assets = []
    for entity in te["entities"]:
        if entity["type"] == "Asset":
            asset_name = ", ".join(entity["texts"])
            asset_id = entity["id"]
            print(
                f"""... extracted asset with id: {asset_id} \
and name: {asset_name}"""
            )
            assets.append(WMAsset(name=asset_name, id=asset_id))
    return assets


def extract_beneficiaries(te):
    """Returns a list of beneficiaries given
    a te dict. gets the name by first index.
    to-do: currently handles single beneficiary,
    add logic for multiple."""

    beneficiaries = []
    for entity in te["entities"]:
        if entity["type"] == "Beneficiary":
            beneficiary_name = list(entity["texts"].keys())[0]
            beneficiary_id = entity["id"]
            print(
                f"""... extracted beneficiary with\
 id: {beneficiary_id} and name: {beneficiary_name}"""
            )
            beneficiaries.append(
                WMPerson(
                    name=beneficiary_name,
                    id=beneficiary_id, dass_type="Beneficiary"
                )
            )
    return beneficiaries


def extract_conditions(te):
    """Returns a list of conditions given
    a te dict. gets the text by first index."""

    conditions = []
    for entity in te["entities"]:
        if entity["type"] == "Condition":
            condition_text = list(entity["texts"].keys())[0]
            condition_id = entity["id"]
            print(
                f"""... extracted condition with\
 id: {condition_id} and text: {condition_text}"""
            )
            conditions.append(
                WMConditional(
                    condition=condition_text,
                    id=condition_id
                )
            )
    return conditions

def extract_testaor(te,used):
    """Returns a the name of the testator.
    currently gets the testator name by the
    first index."""

    for entity in te["entities"]:
        if entity["type"] == "Testator":
            testator_name = list(entity["texts"].keys())[0]
            testator_id = entity["id"]
            print(
                f"""... extracted testator with id:\
 {testator_id} and name: {testator_name}"""
            )
            used.append(testator_id)
            return WMPerson(name=testator_name,
            id=testator_id, dass_type="Testator")
    print("Error: no testator found")
    return None

def extract_executor(te,used):
    """Returns a the name of the executor.
    currently gets the executor name by the
    first index."""

    for entity in te["entities"]:
        if entity["type"] == "Executor":
            executor_name = list(entity["texts"].keys())[0]
            executor_id = entity["id"]
            print(
                f"""... extracted executor with id:\
 {executor_id} and name: {executor_name}"""
            )
            used.append(executor_id)
            return WMPerson(name=executor_name,
            id=executor_id, dass_type="executor")
    print("Error: no executor found")
    return None
################################################################################
#                                                                              #
#                               Fetch  Directives                              #
#                                                                              #
################################################################################


def infer_directives(te, beneficairies, assets,conditions,used):
    """Returns a list of beneficiaries given a te dict,
    beneficairies, and assets.
    to-do: currently handles single beneficiary, add 
    logic for multiple."""
    directives = []
    bequeath_types = ["BequestAsset","Bequest"]  ## add more types here
    for event in te["events"]:
        if event["type"] in bequeath_types:
            if event["type"] in ["BequestAsset",'Bequest'] :
                d_id = event["id"]
                d_type = event["type"]
                asset_id = event["Asset"]
                benefactor_id = event["Beneficiary"]
                condition_id = event["Condition"]
                if type(condition_id)==list:
                    conditions_asset=find_objs_with_id(conditions,
                condition_id)
                    
                else:
                    conditions_asset=[find_obj_with_id(conditions,
                condition_id)]
                conditions_ids=[condition._id for condition in conditions_asset] 
                beneficiary = find_obj_with_id(beneficairies,
                benefactor_id)
                asset = find_obj_with_id(assets, asset_id)
                bequeath_directive = WMDirectiveBequeath(
                    beneficiaries=[beneficiary], assets=[asset],
                    conditions=conditions_asset
                )
                
                used.append(asset_id)
                used.append(benefactor_id)
                used.extend(conditions_ids)

                condition_texts=[condition._condition for condition in conditions_asset]
                conditions_full_text=', and '.join(condition_texts)
                bequeath_directive.type = d_type
                print(f"... infered directive with id: {d_id}")
                print(
                    f"""... directive: Bequest asset \
"{asset._name}" to "{beneficiary._name}" with following condition/s: {conditions_full_text}."""
                )
                directives.append(bequeath_directive)

    return directives


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

    used_ids=[] # to keep track of what's used and what's not

    executor=extract_executor(te_obj['extractions'],used_ids)
    testator = extract_testaor(te_obj['extractions'],used_ids)
    beneficiaries = extract_beneficiaries(te_obj['extractions'])
    conditions= extract_conditions(te_obj['extractions'])
    assets = extract_assets(te_obj['extractions'])
    directives = infer_directives(te_obj['extractions'], beneficiaries,
            assets,conditions,used_ids)
    unused=find_unused(te_obj['extractions'], used_ids)
    unused_ids=[item['id'] for item in unused]

    ## to-do: add will's date ; this is 
    # due to the lack of the date in existing will tes
    print(f"... the following items ids are unused from TE json: {unused_ids}")
    today_date = datetime.date.today()

    will_model = WMWillModel(
        text=te_obj['full_text'], _date=today_date,
        directives=directives, testator=testator,executor=executor 
    )
    save_pickle_object(will_model, path_to_wm_obj)


if __name__ == "__main__":
    main()