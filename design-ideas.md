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

When a will is first created, its digital representation has to be written into some sort of persistent storage.  Subsequent accesses to the will, e.g., for modifications while the testator is alive or devolution after the testator's death, have to be able to locate this representation.  This means that the creation of the will needs to return some sort of locator for its digital representation, which is used for subsequent accesses.   For this, we need a way to map the testator's ID to the locator for that person's will.

**TBD:** The details of how the ID-to-locator mapping is implemented.

**Security requirements (TBD):**
We have to ensure that neither the ID-to-locator mapping nor the actual digital representation of the will can be hacked.  TBD.

**Privacy considerations (TBD):**
What kinds of privacy/confidentiality guarantees do we need?  E.g.:

- Is it important to allow the testator to keep the contents of the will confidential?
- Is it important to allow the testator to keep the fact of the existence of a will, and/or whether or not it has been edited, confidential?


### Representation of a Will
At the top level, the digital representation of a will contains the following information:

- `_data`: information about what the will specifies, e.g., the testator and the directives of the will;
- `_metadata`: information about the creation and edit history of the will;
- `_hash`: a cryptographic hash of the `_data` and `_metadata` fields, to allow auditing and checking for unauthorized alterations.

#### Will Data
The data for a will consists of the following:
- `_testator`: the testator for the will;
- `_directives`: the testator's directives about asset handling;
- `_text`: the original text of the will (to help resolve questions later).

#### Will Metadata
Metadata recorded for a will consists of the following:
- `_creation_info`: information about its creation (witnesses, dates, etc.)
- `_edit_history`: a list of edits to the will.

#### Edit information
Information about each edit contains the following information:
- `_type`: the nature of the edit ('create', 'modify', 'delete', ...)
- `_old`: some representation of the will prior to this edit
- `_change`: some representation of the change(s) being made
- `_who`: who performed the edit 
- `_timestamp`: a timestamp of when the edit was performed            

### Will creation
Given a will whose natural-language text is `w_txt`, we can create the will as follows:

``` Python
def create_will(w_txt):
    testator, directives, witnesses = nlp(w_txt)  # <-- NLP magic happens here
    w = Will(testator, witnesses, directives, w_txt)
    export_will(w)    # write it out in appropriate format
```
