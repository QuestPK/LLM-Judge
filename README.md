# LLM-Judge

## Prerequisites
- Ensure that `ollama` is installed on your system.

## Installation
1. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Model Creation
1. Create the JudgeModel:
    ```sh
    ollama create JudgeModel -f "JudgeModel file path"
    ```

## Running the Model
1. Run the JudgeModel:
    ```sh
    ollama run JudgeModel
    ```

## Stopping the Model
1. To stop the JudgeModel:
    ```sh
    ollama stop JudgeModel
    ```

## Running the Script
1. Run the [script.py](https://github.com/QuestPK/LLM-Judge/blob/dev/script.py) file:
    ```sh
    python script.py
    ```