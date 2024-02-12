# main.py
# need to install en_core_web_sm before running this code: 
# python -m spacy download en_core_web_sm

import nltk
import argparse
import re
import classification, full_examples, ceiling
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
    # get the path to the input file as an argument
    parser = argparse.ArgumentParser(description='Provide input file, text extraction model, and output file')
    parser.add_argument('input_file', type=str, help='Path to the input file')
    parser.add_argument('te_model', type=str, help='Select text extraction model: classification, full_examples, ceiling', default = 'classification')
    parser.add_argument('output_path', type=str, help='Path to the output file', default="output.json")
    args = parser.parse_args()
    file_path = args.input_file
    te_model = args.te_model
    output_path = args.output_path
    sentences = read_and_tokenize(file_path)

    if te_model == "classification":
        extracted_info = classification.main(sentences)
        full_doc = sentence_to_full_doc.process_json(extracted_info, file_path)
        export_to_json(full_doc, output_path)

    elif te_model == "full_examples":
        extracted_info = full_examples.main(sentences)
        full_doc = sentence_to_full_doc.process_json(extracted_info, file_path)
        export_to_json(full_doc, output_path)
    
    elif te_model == "ceiling":
        input_file = input("Enter the path to your input file ()")
        extracted_info = ceiling.main(input_file)
        full_doc = sentence_to_full_doc.process_json(extracted_info, file_path)
        export_to_json(full_doc, output_path)

    else:
        print("please choose text extraction model between 'classification' and 'full_examples'")

if __name__ == "__main__":
    main()