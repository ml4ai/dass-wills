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
# A Will object contains information about the will, organized into three parts: #
# its data, a WillData object consisting of the testator, the directives of the  #
# will, and the original text of the will; and its metadata, consisting of       #
# information about its creation and edit history; and a cryptographic hash of   #
# the data and metadata, to check against tampering.                             #
#                                                                                #
#    -- _data : a WillData object, containing information about the testator     #
#               and the directives of the will; and                              #
#    -- _metadata : a WillMetadata object, containing metadata about the will.   #
#    -- _hash: a cryptographic hash of the _data and _metadata fields, to ensure #
#              that they have not been tampered with.                            #
#                                                                                #
#                                                                                #
# A WillData object contains the following fields:                               #
#                                                                                #
#     -- _testator: the testator for the will;                                   #
#     -- _directives: the testator's directives about asset handling;            #
#     -- _text: the original text of the will                                    #
#                                                                                #
#                                                                                #
# A WillMetadata object contains the following fields:                           #
#                                                                                #
# -- _creation_info: information about its creation (witnesses, dates, etc.)     #
# -- _edit_history: a list of edits to the will                                  #
#                                                                                #
##################################################################################

class WillData:
    """ Data about the testator and directives of the will. """
    def __init__(self, testator, directives, text):
        self._testator = testator
	self._directives = directives
	self._text = text

    def __str__(self):
        return('WillData: __str__() Not yet implemented')
	

class WillMetadata:
    """ Will metadata: information about its creation and edit history. """
    def __init__(self, creat_info, edit_history):
        self._creation_info = creat_info
	self._edit_history = edit_history

    def __str__(self):
        return('WillMetadata: __str__() Not yet implemented')


class Will:
    def __init__(self, testator, witnesses, directives, text):
        """ Create a will object with the fields specified."""
        w_data = WillData(testator, directives, text)

        timestamp = curr_time()

	edit_info = Edit('create', None, w_data, testator, timestamp)
	self._edit_history: [edit_info]

	creat_info = self.creation_info(witnesses, timestamp)

        w_meta = WillMetadata(creat_info, edit_info)

	self._data = data
	self._metadata = w_meta

        w_hash = compute_hash(f'{str(w_data)}; {str(w_meta)}')

        self._data = w_data
	self._metadata = w_meta
	self._hash = w_hash

    def creation_info(self, witness_list, timestamp):
        # creation_info(witness_list, min_num) takes a list of witnesses, 
        # performs various checks on them (including that the no. of witnesses 
        # meets the minimum required), and returns a CreationInfo object if the
	# checks pass.
        qualified_witnesses = {w for w in witness_list if chk_qualified(w)}
        assert len(qualified_witnesses) >= MIN_NUM_WITNESSES, \
	       'Not enough qualified witnesses'
        return CreationInfo(qualified_witnesses, timestamp)


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
# An Edit object contains information about an edit to the will.  It contains    #
# following information:                                                         #
# -- _type: the nature of the edit ('create', 'modify', 'delete', ...)           #
# -- _old: some representation of the will prior to this edit                    #
# -- _change: some representation of the change(s) being made                    #
# -- _who: who performed the edit                                                #
# -- _timestamp: a timestamp of when the edit was performed                      #
#                                                                                #
##################################################################################

class Edit:
    def __init__(self, edit_type, old_will, change, who, timestamp):
        self._type = edit_type
	self._old = old_will
	self._change = change
	self._who = who
	self._timestamp = timestamp

    def __str__(self):
        return('Edit: __str__() Not yet implemented')

```

Given a will whose natural-language text is `w_txt`, we can now create the will as follows:

```
def create_will(w_txt):
    testator, directives, witnesses = nlp(w_txt)  # <-- NLP magic happens here
    w = Will(testator, witnesses, directives, w_txt)
    export_will(w)    # write it out in appropriate format
```

**NOTE**: The cryptographic hash for a will should be stored separately in some trusted location so that it can be used to check the integrity of a will during auditing.
