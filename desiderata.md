# Representing and working with wills in software

The following is a (non-exhaustive) list of desiderata for representing wills in a form suitable for working with them via software.  

1) **Interoperability.**  Ideally, we should not lock in the use of any one kind of software.  This argues for a flexible representation, such as JSON.
2) **Editability.** Wills can be modified.  Their digital versions should be correspondingly editable.  However, this raises a number of issues:
    a) **Edit permissions.** Who is allowed to edit the a will?  Where is this checked?
3) **Provenance and auditability.** We should be able to check the provenance of the digital will:
    a) At will execution time: what information came from where;
    b) At any time: the edit history of a will: who changed what when?


