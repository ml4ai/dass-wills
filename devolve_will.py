""" devolve_will.py -- devolve (execute) a will """

import argparse
import sys
import pickle
from hashlib import sha256
import re
from ORACLES.generate_tree import *
from schemas.model.wm.wm_will_model import WMWillModel

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
        if (len_b == len(output_beneficiaries)):
            print("... Could not beneficiary/ies",list(person.source_text.keys()),f" in directive: {directive._id}.")
            sys.exit(1)

    return output_beneficiaries

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
        sys.exit(1)

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
    if len(assets_directive) == 1 and assets_directive[0].name.lower() =='all my property':
        for asset_t in testator['assets']:
            output_assets.append(asset_t)
        return output_assets
    for asset in assets_directive:
        match=False
        for asset_t in testator['assets']:
            if asset_t['name'] == asset.name:
                output_assets.append(asset_t)
                match=True
                break
        if not match:
            print(f"... error: Could not find testator's asset {asset.name} from database .")
            sys.exit(1)
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
def execute_directive(directive, assets, beneficiaries):
    """Execute the directive by transferring
    the asset to the corresponding entity."""
    """To-do: link real life oracle here."""
    beneficiary_names = ', '.join([str(b['full_name']) for b in beneficiaries])
    asset_names=str([a['name'] for a in assets])
    print(
        f"... [STUB] Transferring assets: '{asset_names}' to beneficiaries: \
{beneficiary_names}"
    )


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
        
        execute_directive(d, a, b)


if __name__ == "__main__":
    main()
