from openai import OpenAI


def query_llm(prompt, model="chatgpt-4o-latest"):
    client = OpenAI()
    
    # Send the prompt to the model
    response = client.chat.completions.with_raw_response.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model=model,
    )
    
    # Get and print the request ID from the headers
    request_id = response.headers.get('x-request-id')
    
    # Parse the completion response to get the message content
    completion = response.parse()
    message_content = completion.choices[0].message.content
    
    # Print and return the message content
    # print(f"Response: {message_content}")
    return message_content
