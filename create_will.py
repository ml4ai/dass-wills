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
    print(f"... exporting the will object with Testator:{will_object._data._testator}")
    with open(file_name+".pickle", 'wb') as handle:
        pickle.dump(will_object, handle, protocol=pickle.HIGHEST_PROTOCOL)
def publish_loc(testor_id, loc):
    """Publishing the will object"""
    #To do......
    print(f"... publishing the the location of will object with Testator id:{testor_id}")

def read_will_info(infilename):
    with open(infilename) as json_file:
        json_info = json.load(json_file)

    will_info = {}
    # Extract the relevant data about the will from the input JSON
    t = json_info['testator']
    will_info['testator'] = Person(t['name'], t['id'], t['info'])

    w = json_info['witnesses']
    will_info['witnesses'] = {Person(v['name'], v['id'], t['info'])
                              for v in w.values()}

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

##################################################################################
#                                                                                #
#                               VALIDATION CHECKS                                #
#                                                                                #
# Right now the validation checks don't do much.  Eventually they should make    #
# appropriate calls to an oracle.                                                #
#                                                                                #
##################################################################################

def validate_testator(testator):
    print(f'... validating testator: {testator}')

def validate_witness(witness):
    print(f'... validating witness: {witness}')

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
def create_will():
    opts = parse_cmd_line()
    if opts['input-json'] is None:
        sys.stderr.write('Input JSON file not specified... aborting\n')
        sys.exit(1)
    else:
        will_info_file = opts['input-json']

    # Read information about the will from the JSON file specified
    will_info = read_will_info(will_info_file)

    # Check legality conditions on testator
    validate_testator(will_info['testator'])
    
    # Check legality conditions on witnesses
    for w in will_info['witnesses']:
        validate_witness(w)

    # Create the will using information from the input JSON, write it out to
    # persistent storage, and publish the mapping from the testator's ID to the
    # will's location
    w = Will(will_info['testator'],
             will_info['witnesses'],
             will_info['directives'],
             will_info['text'])

    # write out the digital will to persistent storage 
    loc = export_will(w,opts['input-json'])

    # publish the association between the testator's ID and the location of
    # the will, for future retrieval and use
    publish_loc(will_info['testator']._id, loc)


if __name__ == '__main__':
    create_will()
