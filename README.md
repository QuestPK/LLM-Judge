# LLM-Judge

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

## How to Request the Ollama Endpoint
1. Once the Ollama model is pulled, you can request the endpoint using HTTP requests. Here’s an example using `curl`:
    ```sh
   curl -X POST http://localhost:11434/api/chat -d "{\"model\": \"qwen2.5:14b\", \"messages\": [{\"role\": \"system\", \"content\": \"you are a personal assistant ....\"}, {\"role\": \"user\", \"content\": \"Your question...\"}], \"stream\": false}" -H "Content-Type: application/json"
    ```

## Start the app
1. Flask server:
    ```sh
    python run.py
    ```
