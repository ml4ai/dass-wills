## Pre-installation

You need to install some dependencies and en_core_web_sm (for spacy) by running these codes:

```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Requirements

To run this code, you'll need an input file (a will text in `.txt` format). There is a will text in this repository (`./text2extractions/input/input.txt`), so you can try running the code with the file. You also need the OpenAI API key to run this code.

## Run the code

You can run the text extraction pipeline by running this code:

```
python main.py
```

If you run the code, you'll be prompted to provide the OpenAI API key. If you are a DASS team member, please contact Alice to get the key for this project.

## Contact

If you have any questions about the codes, please contact Alice (alicekwak@arizona.edu) or file a GitHub issue.