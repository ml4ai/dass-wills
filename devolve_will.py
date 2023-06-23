""" devolve_will.py -- devolve (execute) a will """

import argparse
import json
import sys
import pickle
from hashlib import sha256
from wills import Person, Will

##################################################################################
#                                                                                #
#                                   UTILITIES                                    #
#                                                                                #
##################################################################################


def cmd_line_invocation():
    parser = argparse.ArgumentParser(
        description="""Retrieve a will given a testator ID and perform the following actions:\n - retrieve directives \n - validate thier conditions \n - execute the validated directives."""
    )
    parser.add_argument(
        "-p",
        "--path-to-will",
        type=str,
        required=True,
        help="Input path to the will's [pickle] object.",
    )
    # to-do: use testator ID for will's location
    # parser.add_argument('-t', '--testator', type=str, help="[to-do] Input testator ID. This is to retrieve will using testator's ID.")
    args = parser.parse_args()
    return args


def compute_hash(string):
    """Computes SHA-256 hash of the input string"""
    hash_digest = sha256(string.encode()).hexdigest()
    return hash_digest


def load_will(path):
    """Load the given pickle file and return the Will object."""
    with open(path, "rb") as f:
        will_object = pickle.load(f)
        print(f"... Successfully loaded will from file {path}.")
    f.close()
    return will_object


##################################################################################
#                                                                                #
#                               VALIDATION CHECKS                                #
#                                                                                #
# Right now the validation checks don't do much.                                 #
#                                                                                #
##################################################################################
def validate_will(will):
    """Validate the hash of will."""
    """To-do: add better validation using RSA private key validation."""
    current_hash = compute_hash(f"{str(will._data)}; {str(will._metadata)}")
    if current_hash == will._hash:
        print("... [STUB] Successful will validation.")
    else:
        print("... [STUB] error: Unsuccesful will validation due to incorrect hash.")
        sys.exit(1)


def validate_directive(directive, asset):
    """Validate the given directive using the condition in will."""
    """To-do: add better validation using by linking real life oracle of the condition here."""

    if directive["if"] == "True":
        print(f"... [STUB] Successful directive validation of '{asset}'.")
        return True
    else:
        print(f"... [STUB] Unsuccessful directive validation of '{asset}'.")
        return False


##################################################################################
#                                                                                #
#                               Execution Code                                   #
#                                                                                #
##################################################################################
def execute_directive(directive, asset):
    """Execute the directive by transferring the asset to the corresponding entity."""
    """To-do: add link real life oracle here."""

    print(
        f"... [STUB] Transferring '{asset}' to {directive['then']['beneficiary']['name']} with id {directive['then']['beneficiary']['id']}."
    )


##################################################################################
#                                                                                #
#                               Driver Code                                      #
#                                                                                #
##################################################################################
def main():
    """Load the will, validate its hash, validate each directive, and execute the validated directives."""

    args = cmd_line_invocation()
    path_to_will = args.path_to_will
    will_object = load_will(path_to_will)
    # validate hash
    validate_will(will_object)

    # validate directives

    validated_directives = []
    for directive in will_object._data._directives:
        if validate_directive(will_object._data._directives[directive], directive):
            validated_directives.append(
                (will_object._data._directives[directive], directive)
            )
    if len(validated_directives) == 0:
        print("No directives to execute.")
        sys.exit(0)

    # execute directives

    for directive, asset in validated_directives:
        execute_directive(directive, asset)


if __name__ == "__main__":
    main()