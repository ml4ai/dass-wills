#!/usr/bin/env python3

""" create_will.py -- create a will """

import json
import sys
import pickle
from wills import Person, Will

##################################################################################
#                                                                                #
#                                   UTILITIES                                    #
#                                                                                #
##################################################################################
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

    return will_info


# parse_cmd_line(): parse command line options and return a dictionary with
# command-line information.
def parse_cmd_line():
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: create_will [OPTIONS]\n')
        sys.exit(1)

    opts = {'input-json' : None}
    i, n = 1, len(sys.argv)
    
    # process command line arguments
    while i < n:
        arg = sys.argv[i]
        if arg == '-j':    # input JSON file
            if i < n-1:
                i += 1
                opts['input-json'] = sys.argv[i]
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
    else:
        will_info_file = opts['input-json']

    # Read information about the will from the JSON file specified
    will_info = read_will_info(will_info_file)
    create_will(will_info, opts)


##################################################################################
#                                                                                #
#                               VALIDATION CHECKS                                #
#                                                                                #
# Right now the validation checks don't do much.  Eventually they should make    #
# appropriate calls to an oracle.                                                #
#                                                                                #
##################################################################################

def validate(testator, witnesses):
    validate_testator(testator)
    for w in witnesses:
        validate_witness(w)

def validate_testator(testator):
    print(f'... [STUB] validating testator: {testator}')

def validate_witness(witness):
    print(f'... [STUB] validating witness: {witness}')

##################################################################################
#                                                                                #
#                                 WILL CREATION                                  #
#                                                                                #
##################################################################################


# create_will(): create a will and publish information about it to persistent
# storage.
#
# Eventually we will get information about the will, e.g., the testator,
# witnesses, directives, etc., from the NLP front end. The details of the
# interface for that remain to be worked out, so for now we assume that
# that information is provided in a JSON file specified via the command-line:
#
#     create_will -j <json-file>

def create_will(will_info, opts):
    testator = will_info['testator']
    witnesses = will_info['witnesses']
    directives = will_info['directives']
    text = will_info['text']

    # perform validity checks on testator and witnesses
    validate(testator, witnesses)

    # Create the will using information from the input JSON, write it out to
    # persistent storage, and publish the mapping from the testator's ID to the
    # will's location
    w = Will(testator, witnesses, directives, text)
    loc = export_will(w, opts['input-json'])
    publish_loc(testator._id, loc)


if __name__ == '__main__':
    cmd_line_invocation()
