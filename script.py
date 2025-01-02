from pprint import pprint
import requests

url = 'http://localhost:11434/api/chat'
headers = {'Content-type': 'application/json'}

user_input = """\
Correct Answer:
A healthy diet should include a variety of fruits, vegetables, whole grains, lean protein, and healthy fats. Avoid processed foods, limit sugar, and control portion sizes to maintain a balanced and nutritious diet.

LLM Answer:
A healthy diet consists of eating fruits and vegetables. Avoid eating junk food and drink lots of water.
"""

user_input_2 = """\
Correct Answer:
The process of photosynthesis occurs in the chloroplasts of plant cells. It uses sunlight, carbon dioxide, and water to produce glucose and oxygen. The overall chemical equation for photosynthesis is:
6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.

LLM Answer:
The process of photosynthesis occurs in the chloroplasts of plant cells. It uses sunlight, carbon dioxide, and water to produce glucose and oxygen. The overall chemical equation for photosynthesis is:
6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.
"""

user_input_1 = """
Correct Answer:
Machine learning involves training algorithms on data to make predictions or decisions without being explicitly programmed. Supervised learning, unsupervised learning, and reinforcement learning are three primary types of machine learning.

LLM Answer:
Machine learning is the learning of robots. It is a type of learning that is done by robots.
"""

data = {
  "model": "JudgeModel",
  "messages": [
    {
      "role": "user",
      "content": user_input_1
    }
  ],
  "stream": False
}

print("\nSending request...", end='\n\n')
response = requests.post(url, headers=headers, json=data)

# print(response.json())
pprint(response.json())
