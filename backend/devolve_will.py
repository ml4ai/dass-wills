""" devolve_will.py -- devolve (execute) a will """

import argparse
import sys
import pickle
from hashlib import sha256
import re
from ORACLES.generate_tree import *
from schemas.model.wm.wm_will_model import WMWillModel
import copy
import ast
from gpt_req import query_llm

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
        for text in person.source_text:
            cleaned_name = re.sub(pattern_clean_name, '', text)
            if cleaned_name in people_dict:
                output_beneficiaries.append(people_dict[cleaned_name])
    # if (len_b == len(output_beneficiaries)):
    #     print("... Could not beneficiary/ies",list(person.source_text.keys()),f" in directive: {directive._id}.")
    #         # sys.exit(1)
    #     for person  in beneficiaries:
    #         random_person=copy.deepcopy(people_dict[list(people_dict.keys())[0]])
    #         random_person['full_name']=list(person.source_text.keys())[0]
    #         output_beneficiaries.append(random_person)

    return output_beneficiaries

def validate_and_evaluate_conditions(directive, assets,beneficiaries, db,region='AZ'):
    """Find and validate the conditions of each directive.
    Return divison of assets to each party involved"""

    
    rules_text="""Rules abstraction:
        Division: 
            - by stirpes
            requirements:
                - people involved   
                - condition identifier 
                - family tree
                - divisible assets (boolean)
                - alive status of all persons involved in the directives

            - equally
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)

            - equally (minus people who are not alive)
            requirements:
                - people involved   
                - condition identifier
                - divisible assets (boolean)
                - alive status of all persons involved in the directives

            - by a certain proportion to each person
            requirements:
                - people involved   
                - condition identifier
                - proportions
                - divisible assets (boolean)

            - by a certain proportion to each person (minus people who are not alive)
            requirements:
                - people involved   
                - condition identifier
                - proportions
                - divisible assets (boolean)
                - alive status of all persons involved in the directives


        If-else:
            - if person a is not alive, transfer assets to person b
            requirements:
                - people involved   
                - condition identifier
                - alive status of persons a and b
            
            - if nobody is alive to bequeath, transfer assets as per state's law (default: transfer to state)
            requirements:
                - condition identifier
                - people involved   
                - alive status of all persons involved in the directives
                - state's law

        Bequeath whatever's left:
            - give all assets to one person
            requirements:
                - people involved   
                - condition identifier
                - state of all assets of testator
            
            - give all assets to multiple people
            requirements:
                - people involved   
                - condition identifier
                - state of all assets of testator
                - alive status of all persons involved in the directives

            - give (all assets - assets bequeath in previous directives) to one person
            requirements:
                - people involved   
                - condition identifier
                - state of all assets of testator
            
            - give all assets (in a certain location) to one person
                requirements:
                - people involved   
                - condition identifier
                - state of all assets of testator in certain locations
    """
    
    """  Requirements (union):
    - people involved   
    - state of all assets of testator in certain locations
    - state of all assets of testator
    - alive status of all persons involved in the directives
    - divisible assets (boolean)
    - state's default law
    - condition identifier
    """
    # an identifier is helpful in identifying a general rule/kind given a specfic directive (text)

    # for example:
    # Give all assets in a certain location to one person could be written as:
    # T hereby declare that all of my assets in Area 57 be transferred to person X after my death.
    # I bequeath my property that I own near Nevade in Area 57 to my son.
    # After my demise, I request person Y to transfer my house in Nevada to person X, who is my son, in case he survives me.

    # if identifier_x:
    #    if region == {certainState}:  ## e.g., AZ, TN, NY
    #       assert (requirements)
    #       evaluate conditions and division
    #       return division of assets to each party involved

    
    identifier= directive._identifier if hasattr(directive, '_identifier')  else 'division.equally' 
    example_output="""{'Rule': 'equally', 'Assets': { 'AssetX': 'Proportions': {'PersonX': 0.5, 'PersonY': 0.5}}}"""
    llm_query='Based on the provided rules and abstractions, assets, and beneficiaries, process the given directive text. Identify the name of the Rule to be applied and calculate the proportion share of each party involved. Return ONLY and ONLY a python dictionary as plain text. The example output is: {example_output}. Assets: {a}. Beneficiaries: {b}. Directive: {directive_text}. Rules: '+rules_text
    division={}
    dict_directive={}
    while dict_directive=={}:
        llm_query_dir=llm_query.format(directive_text=directive.serialized_text,example_output=example_output,a=assets,b= beneficiaries)
        llm_query_output= query_llm(llm_query_dir)
        # print(llm_query_output)
        dict_directive = parse_llm_dict(llm_query_output)
    print(f"Directive text: {directive.serialized_text}")

    # if identifier=='division.equally': 
    #     if region=='AZ':
    #         assert (beneficiaries)  # beneficiares are available
    #         assert (assets) # assets to bequeath are available
    #         assert (all([person["alive"]=='true' for person in beneficiaries])) # all beneficiares are alive
    #         for asset in assets:
    #             for person in beneficiaries:
    #                 if person['full_name'] not in division:
    #                     division[person['full_name']]={'assets':[]}
    #                 asset_to_bequeath={'asset':asset['name'],
    #                 'share':1/len(beneficiaries)} # equal distribution
    #                 division[person['full_name']]['assets'].append(asset_to_bequeath)

    #     elif identifier=='division.proporton': 
    #         if region=='AZ':
    #             assert (beneficiaries)  # beneficiares are available
    #             assert (assets) # assets to bequeath are available
    #             assert (all([person['alive']=='true' for person in beneficiaries])) # all beneficiares are alive
    #             for asset in assets:
    #                 for person in beneficiaries:
    #                     if person['full_name'] not in division:
    #                         division[person['full_name']]={'assets':[]}
    #                     share=directive.shares[person['full_name']]
    #                     asset_to_bequeath={'asset':asset['name'],
    #                     'share':share} # equal distribution
    #                     division[person['full_name']]['assets'].append(asset_to_bequeath)

    return dict_directive

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

def find_testator(directive, db,alive_test=False): ## set alive_test to true for realistic checking
    """Find and validate the assets of the testator from the db."""
    pattern_clean_name = r'[^\w\s.]'
    people_dict = {re.sub(pattern_clean_name, '', person["full_name"]): person for person in db["people"]}
    testaor=directive.testator

    for text in testaor.source_text:
        cleaned_name = re.sub(pattern_clean_name, '', text)
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

        llm_query=f'Give a boolean answer yes or no ONLY in lowercase. Tell whether the asset name "{assets_directive[0].name.lower()}" means all the rest of property ?'
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
            llm_query=f'Give a boolean answer yes or no ONLY in lowercase. Tell whether the asset name "{asset.name.lower()}" matches with the following asset: {asset_t} ?'
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
            print(f"... error: Could not find testator's asset {asset.name} from database .")
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
def execute_directive(directive, assets, beneficiaries,db):
    """Execute the directive by transferring
    the asset to the corresponding entity."""
    """To-do: link real life oracle here."""
    beneficiary_names = ', '.join([str(b['full_name']) for b in beneficiaries])

    
    asset_division = validate_and_evaluate_conditions(directive,assets,beneficiaries,db)
    
    for asset_name, asset_details in asset_division['Assets'].items():
        print(f"Asset: {asset_name}")
        for person, proportion in asset_details['Proportions'].items():
            print(f"... [STUB] {person} is transferred {proportion * 100}% of the asset.")



def divide_by_stirpes(beneficiaries, current_percentage=100):
    """Calculate the stirpes of asset as per the
    number of beneficiaries."""

    for beneficiary in beneficiaries["children"]:
        stirped_percentage = current_percentage / len(beneficiaries["children"])
        if beneficiary["alive"] == "true":
            beneficiary["asset_percentage"] = stirped_percentage
        else:
            beneficiary["asset_percentage"] = 0
            divide_by_stirpes(beneficiary, stirped_percentage)


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
    will_object = load_will(path_to_will)
    db = load_json_obj(db_path)
    
    # validate hash of the will
    validate_will(will_object)

    # validate directives
    testator=find_testator(will_object,db)
    print(f"... Successfully validated testator: {testator['full_name']}.")

    validated_directives = []
    for directive in will_object._directives:
        validation, assets,beneficiaries=validate_directive(directive,testator, db)
        if validation:
            validated_directives.append((assets,beneficiaries,directive))
    if len(validated_directives) == 0:
        print("No directives to execute.")
        sys.exit(0)

    # execute directives

    for a, b, d in validated_directives:
        
        execute_directive(d, a, b, db)


if __name__ == "__main__":
    main()
