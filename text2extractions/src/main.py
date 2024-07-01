# main.py
# need to install en_core_web_sm before running this code: 
# python -m spacy download en_core_web_sm

import nltk
import classify_and_extract
import sentence_to_full_doc
import json
from nltk.tokenize import sent_tokenize


def read_and_tokenize(file_path):
    nltk.download('punkt')
    try:
        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)
        return sentences
    except FileNotFoundError:
        print(f"The file '{file_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def export_to_json(dictionary, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(dictionary, json_file, indent=4)


def main():
    # set input and output paths
    input_path = "../input/input.txt"
    output_path = "../output/output.json"

    # read and tokenize input file
    sentences = read_and_tokenize(input_path)

    # text extraction
    extracted_info = classify_and_extract.main(sentences)

    # assemble from each sentence into full extractions for the entire document
    full_doc = sentence_to_full_doc.process_json(extracted_info, input_path)
    export_to_json(full_doc, output_path)
    print("Extraction completed!")


if __name__ == "__main__":
    main()