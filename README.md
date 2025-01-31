

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
2. Api usage 
    ```
    -> call /get-new-token to get a token.
    -> create a project using /create-project in order to get started.
    -> add 2 qna sets using /add-qna.
    -> start comparing to get scores using /compare-qna.
    ```
3. Visit /api-docs for complete details and usage of api's.

