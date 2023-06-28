#!/usr/bin/env python3

""" create_will.py -- create a will """

import json
import sys
import pickle
from wills import Person, Will

################################################################################
#                                                                              #
#                                  UTILITIES                                   #
#                                                                              #
################################################################################
def export_will(will_object,file_name):
    """Export will object as a pickle file"""

    testator = will_object._data._testator
    outfile = file_name.split(".")[0]+".pickle"
    print(f"... exporting the will object with testator: {testator} to {outfile}")
    
    with open(outfile, 'wb') as handle:
        pickle.dump(will_object, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def publish_loc(testor_id, loc):
    """Publishing the will object"""
    #To do......
    print(f"... [STUB] publishing the location of will object with Testator id:{testor_id}")

def read_will_info(infilename):
    with open(infilename) as json_file:
        json_info = json.load(json_file)

    will_info = {}
    # Extract the relevant data about the will from the input JSON
    t = json_info['testator']
    will_info['testator'] = Person(t['name'], t['id'], t['info'])

    will_info['witnesses'] = {Person(v['name'], v['id'], v['info'])
                              for v in json_info['witnesses']}

    will_info['directives'] = json_info['directives']
    will_info['text'] = json_info['text']
    will_info['date'] = json_info['date']

    return will_info


def read_oracle(filename):
    with open(filename) as json_file:
        json_info = json.load(json_file)

    return json_info


# usage(): print out the command-line options for this code"
def usage():
    sys.stderr.write('Usage: create_will OPTIONS\n')
    sys.stderr.write('OPTIONS:\n')
    sys.stderr.write('  -j will-file    (a JSON file specifying the will)\n')
    sys.stderr.write('  -O oracle-file  (a JSON file specifying the oracle DB\n')
    

# parse_cmd_line(): parse command line options and return a dictionary with
# command-line information.
def parse_cmd_line():
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)

    opts = {'input-json' : None, 'oracle-db' : None}
    i, n = 1, len(sys.argv)
    
    # process command line arguments
    while i < n:
        arg = sys.argv[i]
        if arg == '-j':    # input JSON file
            if i < n-1:
                i += 1
                opts['input-json'] = sys.argv[i]
        elif arg == '-O':    # oracle JSON file
            if i < n-1:
                i += 1
                opts['oracle-db'] = sys.argv[i]
        else:
            sys.stderr.write(f'Unrecognized command-line argument: {arg}\n')

        i += 1

    return opts


# If the code is invoked directly from the command line, it needs to read
# the information supplied via the JSON file specified and pass that on to
# create_will().
def cmd_line_invocation():
    opts = parse_cmd_line()
    if opts['input-json'] is None:
        sys.stderr.write('Input JSON file not specified... aborting\n')
        sys.exit(1)
    elif opts['oracle-db'] is None:
        sys.stderr.write('Oracle JSON file not specified... aborting\n')
        sys.exit(1)

    # Read information about the will and the relevant oracle from the JSON
    # files specified
    will_info = read_will_info(opts['input-json'])
    oracle_info = read_oracle(opts['oracle-db'])
    create_will(will_info, oracle_info, opts)


# age(birthdate, will_date): computes the age of someone born on birthdate
# on will_date.  It assumes that each date is specified as a string of the
# form yyyy-mm-dd, e.g., 2023-02-14.
#
# The age computation used here is based on the code published in
# https://stackoverflow.com/a/9754466/65387.
def age(birthdate, will_date):
    bd_list = birthdate.split('-')
    bd_yr, bd_mo, bd_day = int(bd_list[0]), int(bd_list[1]), int(bd_list[2])

    w_list = will_date.split('-')
    w_yr, w_mo, w_day = int(w_list[0]), int(w_list[1]), int(w_list[2])

    return (w_yr - bd_yr) - ((w_mo, w_day) < (bd_mo, bd_day))


# age_is_ok(): returns whether or not the person specified is age 18 or over
# on the date specified based on the oracle_info given.
def age_is_ok(person, date, oracle_info):
    person_bd = oracle_info[person._id]['born']
    person_age = age(person_bd, date)
    
    if person_age >= 18:
        print(f"      {person}'s age = {person_age} [OK]")
    else:
        print(f"      {person}'s age = {person_age} [UNDERAGE]")

    return (person_age >= 18)


##################################################################################
#                                                                                #
#                               VALIDATION CHECKS                                #
#                                                                                #
##################################################################################

def validate(will_info, oracle_info):
    will_date = will_info['date']
    
    validate_testator(will_info['testator'], will_date, oracle_info)
    
    for w in will_info['witnesses']:
        validate_witness(w, will_date, oracle_info)

        
def validate_testator(testator, will_date, oracle_info):
    print(f'... validating testator [{testator}]:')
    assert age_is_ok(testator, will_date, oracle_info)


def validate_witness(witness, will_date, oracle_info):
    print(f'... validating witness [{witness}]:')
    assert age_is_ok(witness, will_date, oracle_info)


################################################################################
#                                                                              #
#                                WILL CREATION                                 #
#                                                                              #
################################################################################


# create_will(): create a will and publish information about it to persistent
# storage.
#
# Eventually we will get information about the will, e.g., the testator,
# witnesses, directives, etc., from the NLP front end. The details of the
# interface for that remain to be worked out, so for now we assume that
# that information is provided in a JSON file specified via the command-line:
#
#     create_will -j <json-file> -O <oracle-file>

def create_will(will_info, oracle_info, opts):
    testator = will_info['testator']
    witnesses = will_info['witnesses']
    directives = will_info['directives']
    text = will_info['text']

    # perform validity checks on testator and witnesses
    validate(will_info, oracle_info)

    # Create the will using information from the input JSON, write it out to
    # persistent storage, and publish the mapping from the testator's ID to the
    # will's location
    w = Will(testator, witnesses, directives, text)
    loc = export_will(w, opts['input-json'])
    publish_loc(testator._id, loc)


if __name__ == '__main__':
    cmd_line_invocation()
