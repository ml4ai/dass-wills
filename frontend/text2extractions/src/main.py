# main.py
# Need to install en_core_web_sm before running this code:
# python -m spacy download en_core_web_sm

import os
import nltk
import classify_and_extract
import sentence_to_full_doc
import json
from nltk.tokenize import sent_tokenize
from openai import OpenAI

nltk.download('punkt')


def read_and_tokenize(file_path):
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


def process_files(input_dir, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # prompt the user for their api key
    # key = input("Please enter your openai api key: ")
    env_var_key = 'OPENAI_API_KEY'

    # Fetch the API key from the environment variable
    api_key = os.getenv(env_var_key)
    client = OpenAI(api_key=api_key)

    # Process each .txt file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(output_dir, output_filename)

            # Read and tokenize input file
            sentences = read_and_tokenize(input_path)

            # Text extraction
            extracted_info = classify_and_extract.main(sentences, client)

            # Assemble from each sentence into full extractions for the entire document
            full_doc = sentence_to_full_doc.process_json(extracted_info, input_path, client)
            final_doc = sentence_to_full_doc.condition_pronoun_replacement(full_doc)

            # Export the results to a JSON file
            export_to_json(final_doc, output_path)
            print(f"Extraction completed for {filename}")


def main():
    # Set input and output directories
    input_dir = "../input"
    output_dir = "../output"

    # Process all files in the input directory
    process_files(input_dir, output_dir)


if __name__ == "__main__":
    main()
