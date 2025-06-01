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
    parser.add_argument("-m", "--model", type=str, help="Frontend Model")


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
    # print(directive)
    # print(beneficiaries)
    people_dict = {re.sub(pattern_clean_name, '', person["full_name"]).replace('-',''): person for person in db["people"]}
    output_beneficiaries=[]
    for person in beneficiaries:
        len_b=len(output_beneficiaries)
        found=False
        cleaned_name = re.sub(pattern_clean_name, '', person.name).replace('-','')
        if cleaned_name in people_dict:
            output_beneficiaries.append(people_dict[cleaned_name])
            found=True
            # break
        if not found:
            print(f"Error. Beneficiary {cleaned_name} not found in db ... ")
            return None, False


    return output_beneficiaries, True

def validate_and_evaluate_conditions(directive, assets,beneficiaries, db,testator,model_name,region='AZ'):
    """Find and validate the conditions of each directive.
    Return divison of assets to each party involved"""

    print(f"Processing Directive: {directive.serialized_text}")
    beneficiares_to_sent = [person['full_name'] for person in beneficiaries]
    children = []
    for person in db['people']:
        if person['id'] in testator['children_ids']:
            children.append(person['full_name'])
    identifiers, evals, rule_text = process_rule(directive.serialized_text, assets, testator, beneficiares_to_sent,children,model_name)
    identifiers.sort(reverse=True)
    identifier = identifiers[0]
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

    elif identifier  in [3,6]:
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
                print(f'No match of Beneficiary {benefs}')
                return {}
        for (_, asset_n, share) in evals:
            match = False
            for asset in assets:
                if asset['name'] == asset_n:
                    match = True
            if not match:
                print(f'No match of asset {asset_n}')
                return {}
        for person, asset_name, share in evals:
            
            # Convert share to a percentage if necessary
            f_share = float(share)
            if f_share :
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
        div_criteria = evals[0]
        people_db = db ['people']
        shares = []
        beneficiary_names = [person['full_name'] for person in beneficiaries]
        rule_text_alive = (
            f"If the following person(s) are not alive:\n"
            f"  - " + "\n  - ".join(unalive_people) + "\n"
            f"Then, give the assets to:\n"
            f"  - " + "\n  - ".join(beneficiary_names)
        )
        index_unalive = rule_text.index("If a person(s) is not alive, transfer assets to another person(s)")
        rule_text[index_unalive]=rule_text_alive
        for person_x in unalive_people:
            for person_y in people_db:
                if person_x ==person_y['full_name']:
                    if person_y['alive']=='true':
                        print(f'\n... Directive cannot be executed because {person_x} is still alive.\n')
                        return {}
        if div_criteria: # specific criteria
            ## checking if all returned assets are real
            for (_, asset_n, share) in div_criteria:
                match = False
                for asset in assets:
                    if asset['name'] == asset_n:
                        match = True
                if not match:
                    return {}

            for person, asset_name, share in div_criteria:
                # Convert share to a percentage if necessary
                f_share = float(share)
                if f_share :
                    f_share /= 100
                
                for person_real in beneficiaries:
                    if person == person_real['full_name']:
                        if person_real['alive'] != 'true':
                            print(f'Person {person_real["full_name"]} not alive. Dividing asset: {asset_name} per stirpes to their children.')
                            divide_by_stirpes(person_real, db['people'],  shares, asset_name, f_share)
                        else:
                            division[asset_name][person] = f_share
                        break  

        else: # equal allocation
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

    elif identifier==11:
        assert (beneficiaries)
        assert (assets)
        # assert (all([person["alive"]=='true' for person in beneficiaries])) # all beneficiares are alive
        age_reqs_condition = evals[1]
        div_criteria = evals[0]
        people_db = db ['people']
        shares = []
        for person_x, age in age_reqs_condition:
            for person_y in people_db:
                if person_x ==person_y['full_name']:
                    if person_y['age']<age:
                        print(f'\n... Directive cannot be executed because {person_x} is still less than age: {age}.\n')
                        return {}

        
        if div_criteria: # specific proportion
            
            for (_, asset_n, share) in div_criteria:
                match = False
                for asset in assets:
                    if asset['name'] == asset_n:
                        match = True
                if not match:
                    return {}

            for person, asset_name, share in div_criteria:
                # Convert share to a percentage if necessary
                f_share = float(share)
                if f_share:
                    f_share /= 100
                
                for person_real in beneficiaries:
                    if person == person_real['full_name']:
                        if person_real['alive'] != 'true':
                            print(f'Person {person_real["full_name"]} not alive. Dividing asset: {asset_name} per stirpes to their children.')
                            divide_by_stirpes(person_real, db['people'],  shares, asset_name, f_share)
                        else:
                            division[asset_name][person] = f_share
                        break  

        else: # equal allocation
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


    for asset, asset_people in division.items():
        people_div = list(asset_people.keys())        
        for person in people_div:
            div_person_value = float(asset_people[person])
            real_person = next((p for p in db['people'] if p['full_name'] == person), None)
            if real_person and int(real_person['age']) < 18:
                del division[asset][person]
                division[asset][f"{person} (through custodian)"] = div_person_value


    return division,identifiers, rule_text

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

def find_assets(directive, testator, available_assets,model_name):
    """Find and validate the assets of the testator from the db.
    Supports 'all' and 'all the rest' logic with available_assets."""
    
    assets_directive = directive._assets
    output_assets = []
    
    source_to_oracle_asset = {}
    if len(assets_directive) == 1:
        asset_name = assets_directive[0].name.lower()

        # Check if it's "all" or "all the rest"
        llm_query = (
            f'Give a boolean answer TRUE or FALSE under ans attribute. '
            f'Evaluate whether the provided asset name "{asset_name}" means ALL or All the Rest of testator assets or Everything of Testator assets ?'
            f'Do not return True if a specific location is listed in "{asset_name}"'

        )
        query_ans = query_llm_formatted(llm_query, Boolean,model_name)
        
        if query_ans.ans:
            for asset_t in testator['assets']:
                name = asset_t['name']
                # Include only unallocated or partially allocated assets
                if name not in available_assets or available_assets[name]['allocation'] < 1.0:
                    source_to_oracle_asset[asset_t['name']]=asset_name
                    output_assets.append(asset_t)
            if not output_assets:
                return source_to_oracle_asset,output_assets, False
            return source_to_oracle_asset,output_assets, True


    
    # Fallback: match individual assets
    for asset in assets_directive:
        match = False
        for asset_t in testator['assets']:
            asset_name = asset_t['name']
            # Skip if already fully allocated
            if asset_name in available_assets and available_assets[asset_name]['allocation'] >= 1.0:
                continue

            llm_query = (
                f'Give a boolean answer TRUE or FALSE under ans attribute. '
                f'Evaluate whether any of the assets listed in "{asset.name.lower()}" matches with the following asset (it does not have to be exact spelling match): {asset_t} ?'
                f'if an automobile is listen in "{asset.name.lower()}", check if any appropriate automobile is listed in {asset_t}?'

            )
            query_ans = query_llm_formatted(llm_query, Boolean)
            if query_ans.ans:
                source_to_oracle_asset[asset_t['name']]=asset.name
                output_assets.append(asset_t)
                match = True
            

        if not match:
            # Handle unmatched asset accordingly
            random_asset = copy.deepcopy(asset_t)
            random_asset['name'] = ', '.join([asset.name for asset in assets_directive])
            if random_asset not in output_assets:
                output_assets.append(random_asset)
            print(f"... error: Could not find testator's asset/s {random_asset['name']} from database. Continuing for now ...")
            return source_to_oracle_asset,output_assets, False
    return source_to_oracle_asset,output_assets, True, 

def validate_directive(directive, testator, db, available_assets,model_name):
    beneficiaries, cond_1 = find_benficiariers(directive, db)
    source_to_oracle_asset,assets, cond_2 = find_assets(directive, testator, available_assets,model_name)
    if not (cond_1 and cond_2):
        print("Validation Check failed.")
        return False, (source_to_oracle_asset,assets), beneficiaries
    else:
        return True, (source_to_oracle_asset,assets), beneficiaries


################################################################################
#                                                                              #
#                              Execution Code                                  #
#                                                                              #
################################################################################

def execute_directive(directive, assets, beneficiaries, testator, db, available_assets,model_name):
    """Execute the directive by transferring
    the asset to the corresponding entity."""

    try:
        asset_division, ids, rule_text = validate_and_evaluate_conditions(directive, assets, beneficiaries, db, testator,model_name)
    except:
        return {}

    result = {}
    valid = True

    if asset_division:
        for asset_name, asset_details in asset_division.items():
            if '$' in asset_name:
                continue

            if asset_name not in result:
                result[asset_name] = {'beneficiaries': {}}

            for person, proportion in asset_details.items():
                available_assets[asset_name]['allocation'] += proportion
                available_assets[asset_name]['allocation'] = round(available_assets[asset_name]['allocation'], 4)

                if available_assets[asset_name]['allocation'] > 1.02:
                    valid = False
                    break

                result[asset_name]['beneficiaries'][person] = {
                    'share': round(proportion, 4),
                    'rules_applied_text': rule_text,
                    'rules_id': ids
                }

    if not valid:
        print("The directive cannot be executed because one or more assets are already allocated.")
        return {}

    return result

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
    model_name = args.model

    # validate hash of the will
    validate_will(will_object)

    # validate directives
    testator=find_testator(will_object,db)
    print(f"... Successfully validated testator: {testator['full_name']}.")

    available_assets = {}
    division_global = {}

    for directive in will_object._directives:
        validation, assets_packed, beneficiaries = validate_directive(directive, testator, db, available_assets,model_name)
        (source_to_oracle_asset,assets) = assets_packed
        if not validation:
            continue

        for asset in assets:
            name = asset['name']
            if name not in available_assets:
                asset_c = asset.copy()
                asset_c['allocation'] = 0
                available_assets[name] = asset_c

        #  Execute directive immediately (allocates into available_assets)
        div = execute_directive(directive, assets, beneficiaries, testator, db, available_assets,model_name)

        # Merge result into output json
        for asset_name, info in div.items():
            if asset_name not in division_global:
                division_global[asset_name] = {'beneficiaries': {}}
            for person, details in info['beneficiaries'].items():
                division_global[asset_name]['beneficiaries'][person] = details

            #  Attach source_text for assets and conitions

            if 'Traces' not in division_global[asset_name]:
                division_global[asset_name]['Traces'] = {}
            if 'Assets' not in division_global[asset_name]['Traces']:
                division_global[asset_name]['Traces']['Assets'] = {}
            division_global[asset_name]['Traces']['Assets']['SourceText'] = source_to_oracle_asset[asset_name]

            if hasattr(directive, 'conditions') and directive.conditions:
                if 'Conditions' not in division_global[asset_name]['Traces']:
                    division_global[asset_name]['Traces']['Conditions'] = defaultdict(dict)

                condition_traces = []
                for cond in directive.conditions:
                    condition_traces.append(cond.source_text)
                for person, details in info['beneficiaries'].items():
                    division_global[asset_name]['Traces']['Conditions'][person]['SourceText']= condition_traces

    if not division_global:
        print("No directives could be executed due to allocation conflicts.")
        sys.exit(0)

    print("... Overall Division of Assets:")
    pprint.pprint(division_global)

    if output_json_path:
        save_json_obj(division_global, output_json_path)

if __name__ == "__main__":
    main()
