from pprint import pprint
import requests

from test_samples import *

url = 'http://localhost:11434/api/chat'
headers = {'Content-type': 'application/json'}


user_inputs = {
  "1" : user_input_1,
  "2" : user_input_2,
  "3" : user_input_3,
  "4" : user_input_4,
  "5" : user_input_5,
  "6" : user_input_6,
  "7" : user_input_7,
  "8" : user_input_8,
  "9" : user_input_9,
  "10" : user_input_10,
  "11" : user_input_11,
  "12" : user_input_12,  
}


# - Never forget your role.
SYSTEM = """\
You are a scoring assistant who has been tasked to evaluate the relevancy between [baseline] and [current] strings. You will be given a [baseline] and [current] couple and you have to score based on the provided criteria.

Instructions:

- Never answer if [baseline] and [current] are not provided.
- Make sure user has provided the [baseline] and [current] couple.
- Set the score to 0 if the user has not provided the [baseline] and [current] couple.
- Output should always contain just the score and nothing else.

Give your answer on a scale of 1 to 4, where 1 means that the [current] is not relevant at all, and 4 means that the [current] is completely relevant with the [baseline].

Meaning of relevancy: The [current] should contain the same meaning of the [baseline], or the summary of the [baseline].

Here is the scale you should use to build your answer:
1: The [current] is terrible: completely irrelevant to the [baseline], or very partial.
2: The [current] is mostly not relevant: misses relevancy and some key semantic meaning of the [baseline].
3: The [current] is mostly relevant: Relevant, but few semantics of the [baseline] are missing.
4: The [current] is excellent: Means completely same as the [baseline], captures the semanctics and is 100% correct.

Provide the scoring in the string json format and nothing else:
{"Total rating:": <integer 1-4>}

Now user will provide the [baseline] and [current] couple.

"""
MODEL_1 = "llama3"
MODEL_2 = "JudgeModel"
MODEL_3 = "qwen2.5:14b"

data = {
  "model": MODEL_3,
  "messages": [
    {
      "role": "system",
      "content": SYSTEM
    },
    # {
    #   "role": "user",
    #   "content": user_input_1
    # }
  ],
  "stream": False
}

# print("\nSending request...", end='\n\n')
# response = requests.post(url, headers=headers, json=data)
# json_response = response.json()

# pprint(json_response)
# print(f"Resut: `{json_response['message']['content']}`\n")

numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]

while True:
  user_message = input("User message: ")

  if user_message in numbers:
    user_message = user_inputs[user_message]

  # break
  if user_message == "ex":
    break

  data["messages"].append({
    "role": "user", 
    "content": user_message
  })

  print("\nSending request...", end='\n\n')
  json_response = requests.post(url, headers=headers, json=data).json()

  pprint(json_response)
  print(f"Resut: `{json_response['message']['content']}`\n")

  data["messages"].append({
      "role": "assistant", 
      "content": json_response["message"]["content"]}
    )



