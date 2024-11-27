import requests

def get_img_description(encoded_img, api_key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
    "model": "gpt-4o",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "다음 그림은 영유아의 증상 혹은 상태를 촬영한 사진이다. 다음 사진에서 관찰할 수 있는 아이의 상태를 묘사하라. 상태에 대해 진단해서는 안된다."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_img}"}}
        ]
    }],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()['choices'][0]['message']['content']

