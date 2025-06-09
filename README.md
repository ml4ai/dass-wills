# DASS WILLS

This driver code performs the following actions:

    - Processes the will text to get the text extractions json.
    - Processes the text extractions json to get the Will Model object.
    - Processes the Will Model to get the Devolution output.

All of outputs are stored in the given output folder.

## Requirements Installation:

```
pip3 install -r requirements.txt
python3 -m spacy download en_core_web_sm
python3 -m spacy download en_core_web_trf
```

## Arguments

The script requires the following arguments:

1. **Input File**: The path to the input will text file (required).
2. **Output Path**: The directory where the output files should be saved (required).
3. **OPENAI API KEY**: OPENAI API KEY for the modules usage (required).
4. **ORACLE FILE**: Add PATH of ORACLE database containing testator and beneficiaries information.


### Example Usage:

```bash
python3 src/driver.py -i input.txt -o outputp_path -k OPENAI_KEY -d ORACLE_PATH
```

