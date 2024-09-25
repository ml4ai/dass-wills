from openai import OpenAI


def query_llm(prompt, model="chatgpt-4o-latest"):
    client = OpenAI()
    
    response = client.chat.completions.with_raw_response.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model=model,
    )
    
    request_id = response.headers.get('x-request-id')
    completion = response.parse()
    message_content = completion.choices[0].message.content
    
    return message_content
