# Representing and working with wills in software

## Desiderata

The following is a (non-exhaustive) list of desiderata for representing wills in a form suitable for working with them via software.  

1) **Interoperability.**  Ideally, we should not lock in the use of any one kind of software.  This argues for a flexible representation, such as JSON.
2) **Editability.** Wills can be modified.  Their digital versions should be correspondingly editable.  However, this raises a number of issues:

    * **Edit permissions.** Who is allowed to edit the a will?  Where is this checked?
3) **Provenance and auditability.** We should be able to check the provenance of the digital will:

    * At will execution time: what information came from where;
    * At any time: the edit history of a will: what was changed, by whom, and when?
    * What else?

4) ...

## Implementation logic
The code shown below sketches the logic of a possible implementation.  Python is chosen for convenience, with the understanding that interoperability considerations (above) are taken into account.

``` Python
##################################################################################
#                                                                                #
# A Will object has the following fields:                                        #
# -- _testator: the testator for the will;                                       #
# -- _directives: the testator's directives about asset handling;                #
# -- _creation_info: information about its creation (witnesses, dates, etc.)     #
# -- _edit_history: a list of edits to the will (ideally: append-only)           #
#                                                                                #
##################################################################################

class Will:
    def __init__(self, testator, directives, will_creation_info):
        """ Create a will object with the fields specified."""
        self._testator = testator
	self._directives = directives
	self._creation_info = will_creation_info
	self._edit_history: []

    def modify(...):
        """ Modify a will.'''
        pass


##################################################################################
#                                                                                #
# A Witness object records information about a witness to the creation of a will #
# -- _name: the name of the witness                                              #
# -- _id: since different people can share the same name                         #
#                                                                                #
##################################################################################

class Witness:
    def __init__(self, name, id):
        self._name = name
        self._id = id


##################################################################################
#                                                                                #
# A CreationInfo object contains information about the creation of a will.  This #
# includes information about the witnesses, the date, and anything else required #
# by law.                                                                        #
#                                                                                #
##################################################################################

class CreationInfo:
    def __init__(self, witnesses, date):
        self._witnesses = witnesses
        self._date = date
        # ... anything else?


##################################################################################
#                                                                                #
#                                 CREATING A WILL                                #
#                                                                                #
##################################################################################

# Q [LAW]: What other information should we record at will creation time?
def create_will(testator, directives, witness_list):
    c_info = creation_info(witness_list, MIN_NUM_WITNESSES)
    w = Will(testator, directives, c_info)
    export_will(w)    # write it out in appropriate format

# creation_info(witness_list, min_num) takes a list of witnesses and performs
# various checks on them, including that the no. of witnesses meets the minimum
# required.  If the checks pass, a CreationInfo object is returned.
def creation_info(witness_list, min_num):
    qualified_witnesses = {w for w in witness_list if chk_qualified(w)}
    assert len(qualified_witnesses) >= min_num, 'Not enough qualified witnesses'
    today = today_date()
    return CreationInfo(qualified_witnesses, today)
```
