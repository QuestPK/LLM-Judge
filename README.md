

# LLM-Judge app setup and endpoints usage

## Prerequisites
- Ensure that `qwen2.5:14b` model is running.

## How to Pull the Ollama Model
1. To pull the Ollama model, run the following command:
    ```sh
    ollama pull <model_name>
    ```
    Replace `<model_name>` with the desired model (e.g., `qwen2.5:14b` or any specific Ollama model).


## Installation
1. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Start the app
1. Flask server:
    ```sh
    python run.py
    ```

## Usage `/get-score-for-queries` Endpoint
1. **Endpoint**: `base_url/get-score-for-queries`
2. **Request type**: POST
2. **Payload**:
    ```json
    {
        "queries_data": [
            {
                "12": {
                    "question": "What is a healthy diet?",
                    "baseline": "A healthy diet should include a variety of fruits, vegetables, whole grains, lean protein, and healthy fats. Avoid processed foods, limit sugar, and control portion sizes to maintain a balanced and nutritious diet.",
                    "current": "A healthy diet consists of eating fruits and vegetables. Avoid eating junk food and drink lots of water.",
                    "summary_accepted": true
                },
                "34": {
                    "question": "What is photosynthesis?",
                    "baseline": "The process of photosynthesis occurs in the chloroplasts of plant cells. It uses sunlight, carbon dioxide, and water to produce glucose and oxygen. The overall chemical equation for photosynthesis is: \n6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.",
                    "current": "The process of photosynthesis occurs in the chloroplasts of plant cells. It uses sunlight, carbon dioxide, and water to produce glucose and oxygen. The overall chemical equation for photosynthesis is: \n6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.",
                    "summary_accepted": true
                }
            }
        ],
        "email": "umertes@gmail.com"
    }
    ```

## Usage `/get-score` Endpoint
1. **Endpoint**: `base_url/get-score`
2. **Request type**: POST
2. **Payload**:
    ```json
    {
    "query_data" : {
        "question" : "sample question",
        "baseline" : "baseline answer",
        "current" : "current answer"
    },
    "email" : "test@gmail.com"
}
    ```

## Usage `/compare-qa-sets` Endpoint
1. **Endpoint**: `base_url/compare-qa-sets`
2. **Request type**: POST
2. **Payload**:
    ```json
    {
        "email" : "umertest123@gmail.com",
        "project_id" : 22,
        "current_set_id" : 78
        "baseline_set_id" : 456 // Optional
    }
    ```

