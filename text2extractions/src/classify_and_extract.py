import create_full_prompt
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff
import concurrent.futures


# Use GPT-4o (much cheaper than GPT-4, but still considerably expensive than GPT-3.5)
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def extract_information(prompt, target_text, client):
    response = client.chat.completions.create(
      model='gpt-4o',
      response_format={
        'type': 'json_object',
      },
      messages=[
        {
          "role": "system",
          "content": prompt
        },
        {
          "role": "user",
          "content": target_text
        }
      ],
      temperature=0,
      max_tokens=4096,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    return response


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def classification(prompt, target_text, client):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
              "role": "system",
              "content": prompt
            },
            {
              "role": "user",
              "content": target_text
            }
          ],
        temperature=0,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
    return response


def classify_text_list(text_list, client):
    print("Begin text classification!")
    with open("../doc/classification_prompt.txt", 'r') as file:
        prompt = file.read()
    total_classifications = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_text = {executor.submit(classification, prompt, text, client): text for text in text_list}
        for future in concurrent.futures.as_completed(future_to_text):
            classification_result = future.result()
            total_classifications.append(eval(classification_result.choices[0].message.content))
    assert len(text_list) == len(total_classifications)
    return total_classifications


def extract_for_text(index, text, client, directory, preds, num_of_examples):
    print(f"extracting from {index + 1}th sentence!")
    try:
        full_prompt = create_full_prompt.main(directory, preds[index], num_of_examples)
        response = extract_information(full_prompt, text, client)
        return response.choices[0].message.content
    except Exception as e:
        print(f"something went wrong while processing {index + 1}th text: {e}")
        return None


def main(text_list, client):
    directory = "../doc/example_pool"
    num_of_examples = 5

    # make predictions using pretrained models
    preds = classify_text_list(text_list, client)

    # check if the length of preds_list and text_list are equal
    assert len(preds) == len(text_list)

    # using predictions, create prompts and extract information
    extracted_info = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(extract_for_text, i, text_list[i], client, directory, preds, num_of_examples) for i in range(len(text_list))]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                extracted_info.append(result)

    return extracted_info
