## Pre-installation

You need to install some dependencies and en_core_web_sm (for spacy) by running these codes:

```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Requirements

To run this code, you'll need an input file (a will text in `.txt` format). There is a will text in this repository (`test_wills.txt`), so you can try running the code with the file if you want.

You'll also need the OpenAI API key to run this code. If you are a DASS team member, please contact Alice to get the key.

## Run the code

You can run the text extraction pipeline by running this code:

```
python main.py path/to/your/input_file classification path/to/your/output_file
```

The second argument is the text extraction model. You can choose between `classification` and `full_examples`.

## Contact

If you have any questions about the codes, please contact Alice (alicekwak@arizona.edu) or file a github issue.
