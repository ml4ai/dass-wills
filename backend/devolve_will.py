""" devolve_will.py -- devolve (execute) a will """

import argparse
import sys
import pickle
from collections import defaultdict
from hashlib import sha256
import re
from ORACLES.generate_tree import *
from schemas.model.wm.wm_will_model import WMWillModel
import copy
import ast
from gpt_req import *

################################################################################
#                                                                              #
#                                  UTILITIES                                   #
#                                                                              #
################################################################################


def cmd_line_invocation():
    desc_text = """Retrieve a will given a testator ID and perform 
    the following actions:\n
    - retrieve directives \n
    - validate thier conditions \n 
    - execute the validated directives."""
    parser = argparse.ArgumentParser(description=desc_text)
    parser.add_argument(
        "-p",
        "--path-to-will",
        type=str,
        required=True,
        help="Input path to the will's [pickle] object.",
    )
    parser.add_argument(
        "-d",
        "--path-to-database",
        type=str,
        default="ORACLES/people_db.json",
        required=False,
        help="Input path to the people's database.",
    )
    parser.add_argument(
        "-o",
        "--save-output-json",
        type=str,
        required=False,
        help="Output path to the save the asset division json.",
    )


    # to-do: use testator ID for will's location
    # parser.add_argument('-t', '--testator', type=str,
    # help="[to-do] Input testator ID.
    # This is to retrieve will using testator's ID.")
    args = parser.parse_args()
    return args


def compute_hash(obj_bytes):
    """Computes SHA-256 hash of the input string"""
    hash_digest = sha256(obj_bytes).hexdigest()
    return hash_digest


def load_will(path):
    """Load the given pickle file and return the Will object."""
    with open(path, "rb") as f:
        will_object = pickle.load(f)
        print(f"... Successfully loaded will from file {path}.")
    f.close()
    return will_object


def load_json_obj(path):
    """Load the given json file and return the dict object."""
    with open(path, "rb") as f:
        obj = json.load(f)
        print(f"... Successfully loaded json obj from file {path}.")
    f.close()
    return obj

def save_json_obj(obj, path):
    """Save the given dict object to a JSON file."""
    with open(path, "w") as f:
        json.dump(obj, f, indent=4)
        print(f"... Successfully saved JSON object to file {path}.")


def parse_llm_dict(dict_text):
    try:
        dict_text_processed=dict_text.replace('```python','').replace('```','')
        converted_dict = ast.literal_eval(dict_text_processed)
        return converted_dict
    except:
        return {}
################################################################################
#                                                                              #
#                              VALIDATION CHECKS                               #
#                                                                              #
################################################################################
def find_benficiariers(directive, db):
    """Find and validate the beneficiary from the database.
    Currently is based on matching fullname against the database."""

    # remove special characters except period
    pattern_clean_name = r'[^\w\s.]'
    beneficiaries = directive._beneficiaries
    people_dict = {re.sub(pattern_clean_name, '', person["full_name"]): person for person in db["people"]}
    output_beneficiaries=[]
    for person in beneficiaries:
        len_b=len(output_beneficiaries)
        found=False
        cleaned_name = re.sub(pattern_clean_name, '', person.name)
        if cleaned_name in people_dict:
            output_beneficiaries.append(people_dict[cleaned_name])
            found=True
            # break
        if not found:
            print(f"Error. Beneficiary {cleaned_name} not found in db. Exiting the system ... ")
            sys.exit(1)

    return output_beneficiaries

def validate_and_evaluate_conditions(directive, assets,beneficiaries, db,testator,region='AZ'):
    """Find and validate the conditions of each directive.
    Return divison of assets to each party involved"""

    print(f"Processing Directive: {directive.serialized_text}")
    beneficiares_to_sent = [person['full_name'] for person in beneficiaries]
    children = []
    for person in db['people']:
        if person['id'] in testator['children_ids']:
            children.append(person['full_name'])
    identifier, evals, rule_text = process_rule(directive.serialized_text, assets, testator, beneficiares_to_sent,children)
    division = defaultdict(dict)

    if identifier in [0,1]:
        assert (beneficiaries)  # beneficiares are available
        assert (assets) # assets to bequeath are available
        shares = []
        for asset in assets:
            asset_dict = defaultdict(int)
            asset_name = asset['name']
            for person in beneficiaries:
                equal_division = round(1/len(beneficiaries),5)
                if person['alive']!='true':
                    print(f'Person {person["full_name"]} not alive. Dividing asset: {asset_name} per stirpes to thier children.')
                    divide_by_stirpes(person,db['people'],shares,asset_name, equal_division)
                    continue
                asset_dict[person['full_name']]=equal_division
                division[asset_name].update(asset_dict)
        for (person,share,asset_name) in shares:
            division[asset_name][person]=share

    elif identifier  == [3,6]:
        assert (beneficiaries)  # beneficiares are available
        assert (assets) # assets to bequeath are available
        # assert (all([person["alive"]=='true' for person in beneficiaries])) # all beneficiares are alive
        # ensuring the shares, beneficiares, and assets are valid
        shares = []
        for (benef, _, share) in evals:
            match = False
            for person in beneficiaries:
                if person['full_name']==benef:

                    match = True
            if not match:
                
                return {}
        for (_, asset_n, share) in evals:
            match = False
            for asset in assets:
                if asset['name'] == asset_n:
                    match = True
            if not match:
                return {}
        for person, asset_name, share in evals:
            
            # Convert share to a percentage if necessary
            f_share = float(share)
            if f_share > 1:
                f_share /= 100
            
            for person_real in beneficiaries:
                if person == person_real['full_name']:
                    if person_real['alive'] != 'true':
                        print(f'Person {person_real["full_name"]} not alive. Dividing asset: {asset_name} per stirpes to their children.')
                        divide_by_stirpes(person_real, db['people'],  shares, asset_name, f_share)
                    else:
                        division[asset_name][person] = f_share
                    break  

        # Update the division with any remaining shares
        for person, share, asset_name in shares:
            division[asset_name][person] = share


    elif identifier==5:
        assert (beneficiaries)
        assert (assets)
        # assert (all([person["alive"]=='true' for person in beneficiaries])) # all beneficiares are alive
        unalive_people = evals[1]
        people_db = db ['people']
        shares = []
        for person_x in unalive_people:
            for person_y in people_db:
                if person_x ==person_y['full_name']:
                    if person_y['alive']=='true':
                        print(f'\n... Directive cannot be executed because {person_x} is still alive.\n')
                        return {}

        for asset in assets:
            asset_dict = defaultdict(int)
            asset_name = asset['name']
            for person in beneficiaries:
                if person['alive']!='true':
                    print(f'Person {person["full_name"]} not alive. Dividing asset: {asset_name} per stirpes to thier children.')
                    divide_by_stirpes(person,db['people'],shares,asset_name, equal_division)
                    continue
                equal_division = round(1/len(beneficiaries),2)
                asset_dict[person['full_name']]=equal_division
                division[asset_name].update(asset_dict)
        for (person,share,asset_name) in shares:
            division[asset_name][person]=share


    elif identifier==11:
        assert (beneficiaries)
        assert (assets)
        # assert (all([person["alive"]=='true' for person in beneficiaries])) # all beneficiares are alive
        age_reqs_condition = evals[1]
        people_db = db ['people']
        shares = []
        for person_x, age in age_reqs_condition:
            for person_y in people_db:
                if person_x ==person_y['full_name']:
                    if person_y['age']<age:
                        print(f'\n... Directive cannot be executed because {person_x} is still less than age: {age}.\n')
                        return {}

        for asset in assets:
            asset_dict = defaultdict(int)
            asset_name = asset['name']
            for person in beneficiaries:
                if person['alive']!='true':
                    print(f'Person {person["full_name"]} not alive. Dividing asset: {asset_name} per stirpes to thier children.')
                    divide_by_stirpes(person,db['people'],shares,asset_name, equal_division)
                    continue
                equal_division = round(1/len(beneficiaries),2)
                asset_dict[person['full_name']]=equal_division
                division[asset_name].update(asset_dict)
        for (person,share,asset_name) in shares:
            division[asset_name][person]=share


    for asset, asset_people in division.items():
        people_div = list(asset_people.keys())        
        for person in people_div:
            div_person_value = float(asset_people[person])
            real_person = next((p for p in db['people'] if p['full_name'] == person), None)
            if real_person and int(real_person['age']) < 18:
                del division[asset][person]
                division[asset][f"{person} (through custodian)"] = div_person_value


    return division,identifier, rule_text

def validate_will(will):
    """Validate the hash of will."""
    """To-do: add better validation using RSA private key validation."""
    checksum = will.checksum
    will.checksum = None
    current_hash = compute_hash(pickle.dumps(will))
    will.checksum = checksum
    if current_hash == checksum:
        print(f"... [STUB] Successful will checksum validation; checksum:{checksum}")
    else:
        print("... [STUB] error: will validation failed due to invalid hash.")
        # sys.exit(1)

def find_testator(will_obj, db,alive_test=False): ## set alive_test to true for realistic checking
    """Find and validate the assets of the testator from the db."""
    pattern_clean_name = r'[^\w\s.]'
    people_dict = {re.sub(pattern_clean_name, '', person["full_name"]): person for person in db["people"]}
    testaor=will_obj.testator
    cleaned_name = re.sub(pattern_clean_name, '', testaor.name)
    if cleaned_name in people_dict:
        if alive_test: ## mat
            if people_dict[cleaned_name]['alive']=='true':
                    print("... error: testator still alive. Cannot proceed further.")
        return people_dict[cleaned_name]
    print("... error: Could not find testator.")
    sys.exit(1)

def find_assets(directive,testator):
    """Find and validate the assets of the testator from the db."""
    assets_directive=directive._assets
    output_assets=[]

    if len(assets_directive) == 1:
        llm_query=f'Give a boolean answer yes or no ONLY in lowercase. Evaluate whether the asset name "{assets_directive[0].name.lower()}" means ALL the rest of property ?'
        query_ans=''
        while (query_ans not in ['yes','no']):
            query_ans=query_llm(llm_query)
        if (query_ans =='yes'):
            for asset_t in testator['assets']:
                output_assets.append(asset_t)
            return output_assets
    for asset in assets_directive:
        match=False
        for asset_t in testator['assets']:
            llm_query=f'Give a boolean answer yes or no ONLY in lowercase. Evaluate whether the asset name "{asset.name.lower()}" matches with the following asset (it does not have to be exact spelling match): {asset_t} ?'
            query_ans=''
            while (query_ans not in ['yes','no']):
                query_ans=query_llm(llm_query)
            if (query_ans =='yes'):
                output_assets.append(asset_t)
                match=True
                break
        if not match:
            ## comment this out later
            
            random_asset=copy.deepcopy(asset_t)
            random_asset['name']=', '.join([asset.name for asset in assets_directive])
            if random_asset not in output_assets:
                output_assets.append(random_asset)
            print(f"... error: Could not find testator's asset/s {random_asset['name']} from database. Continuing for now ...")
            # sys.exit(1)
    return output_assets

def validate_directive(directive,testator,db):
    """Validate the given directive using the condition in will."""
    """To-do: add better validation."""
    beneficiaries=find_benficiariers(directive, db)
    print(f"... Successfully validated beneficiaries of directive {directive._id}.")
    assets=find_assets(directive, testator)
    print(f"... Successfully validated assets of directive {directive._id}.")
    conditions=directive.conditions
    ## to-do add code to validate conditions

    return True, assets, beneficiaries

################################################################################
#                                                                              #
#                              Execution Code                                  #
#                                                                              #
################################################################################
def execute_directive(directive, assets, beneficiaries,testator,db,available_assets):
    """Execute the directive by transferring
    the asset to the corresponding entity."""
    """To-do: link real life oracle here."""

    beneficiary_names = ', '.join([str(b['full_name']) for b in beneficiaries])
    try:
        asset_division, id,rule_text = validate_and_evaluate_conditions(directive,assets,beneficiaries,db,testator)
    except:
        return {}
    stub_text=''
    valid=True
    
    if asset_division:
        for asset_name, asset_details in asset_division.items():
            stub_text+=f"\nAsset: {asset_name}\n"
            for person, proportion in asset_details.items():
                available_assets[asset_name]['allocation']+=proportion
                available_assets[asset_name]['allocation'] = round(available_assets[asset_name]['allocation'],2)
                if available_assets[asset_name]['allocation']>1.02: ## the allocation might exceed by a bit
                    valid=False
                    break
                stub_text+=f"... [STUB] {person} is transferred {proportion * 100}% of the asset.\n"
    if valid:
        print(stub_text)
    else:
        print("The directive cannot be executed because one or more assets are already allocated.")
        return {}
    div = {}
    div [str(directive._id)]=asset_division
    div[str(directive._id)]['rule_applied_id']=id
    div[str(directive._id)]['rule_applied_text']= rule_text.strip().split('\n')[0]

    return div

def divide_by_stirpes(root_beneficiary, people_db, shares, asset_name, current_percentage=1):
    """
    Calculate the stirpes of an asset according to the number of beneficiaries.
    """
    children_ids = root_beneficiary.get("children_ids", [])
    stirped_percentage = current_percentage / len(children_ids) if children_ids else 0

    for b_id in children_ids:
        person = next((p for p in people_db if p['id'] == b_id), None)
        if person:
            if person["alive"] == "true":
                shares.append((person["full_name"], stirped_percentage,asset_name))
            else:
                divide_by_stirpes(person, people_db, shares, asset_name,stirped_percentage)


################################################################################
#                                                                              #
#                              Driver Code                                     #
#                                                                              #
################################################################################
def main():
    """Load the will, validate its hash,
    validate each directive,
    and execute the validated directives."""

    args = cmd_line_invocation()
    path_to_will = args.path_to_will
    db_path = args.path_to_database
    output_json_path = args.save_output_json
    will_object = load_will(path_to_will)
    db = load_json_obj(db_path)
    
    # validate hash of the will
    validate_will(will_object)

    # validate directives
    testator=find_testator(will_object,db)
    print(f"... Successfully validated testator: {testator['full_name']}.")

    validated_directives = []
    available_assets={}
    for directive in will_object._directives:
        validation, assets,beneficiaries=validate_directive(directive,testator, db)
        if validation:
            validated_directives.append((assets,beneficiaries,directive))
            for asset in assets:
                if asset['name'] not in available_assets:
                    asset_c=asset.copy()
                    available_assets[asset_c['name']]=asset_c
    if len(validated_directives) == 0:
        print("No directives to execute.")
        sys.exit(0)

    # execute directives
    for asset in available_assets:
       available_assets[asset]['allocation']=0
    divison_global = {}

    for a, b, d in validated_directives:
        div = execute_directive(d, a, b,testator, db,available_assets)
        divison_global.update(div)
    print("... Overall Division of Assets:")
    pprint.pprint(divison_global)

    if output_json_path:
        save_json_obj(divison_global, output_json_path)

if __name__ == "__main__":
    main()
