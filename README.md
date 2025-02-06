# LLM-Judge App - Setup and API Usage

## Prerequisites
- Ensure that the `qwen2.5:14b` model is running.

## How to Pull the Ollama Model
To pull the Ollama model, run the following command:
```sh
ollama pull <model_name>
```
Replace `<model_name>` with the desired model (e.g., `qwen2.5:14b`).

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/QuestPK/LLM-Judge.git
    cd LLM-Judge
    ```
2. Create a virtual environment (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Starting the Application
To start the Flask server, run:
```sh
python run.py
```

## API Usage 

###  API Documentation
For complete API documentation and usage details, visit:
```http
GET /api-docs
```

### 1. Obtain a Token
To authenticate and interact with the API, retrieve a token by making a request to:
```http
POST /get-new-token
```

### 2. Create a Project
Create a project to add qna sets:
```http
POST /create-project
```
#### Request Body (JSON):
```json
{
  "project_name": "Example Project"
}
```
#### Response:
```json
{
  "project_id": "786",
  "message": "Project created successfully"
}
```

### 3. Add Question-Answer (QnA) Sets
To add QnA sets to a project, use:
```http
POST /add-qna
```
#### Sample QnA Set 1
```json
{
  "project_id": "786",
  "qa_data": {
    "qa_set": [
      {
        "id": 1,
        "question": "What are the symptoms and treatment options for an abscess in dogs?",
        "answer": "Symptoms of an abscess in dogs include painful skin swelling or a draining sore, fever, lethargy, loss of appetite, and reluctance to move the affected area. For treatment, a veterinarian typically needs to anesthetize the dog and then surgically lance and drain the abscess. The area is clipped of fur, disinfected, and flushed with a solution like hydrogen peroxide and water. Oral antibiotics are usually prescribed as well. At home, the incision should be rinsed daily with a solution of hydrogen peroxide and water to aid healing."
      },
      {
        "id": 2,
        "question": "How does acupuncture benefit dogs, and what conditions can it help treat?",
        "answer": "Acupuncture offers several benefits for dogs, primarily due to its lack of side effects. It can release neurochemicals or endorphins in the brain that cause pain relief. This therapy is used to help manage a variety of conditions in pets, including: - Arthritis - Reproductive disorders - Back and musculoskeletal problems - Skin conditions like allergies - Pain relief - Neurological issues. Acupuncture is considered an integral part of veterinary medicine, and its benefits are recognized in improving the overall well-being of pets."
      }
    ],
    "set_id": 78
  }
}
```

#### Sample QnA Set 2
```json
{
  "project_id": "786",
  "qa_data": {
    "qa_set": [
      {
        "id": 1,
        "question": "What are the symptoms and treatment options for an abscess in dogs?",
        "answer": "For an abscess in dogs, the symptoms often include: • A painful, swollen area on the skin that may drain pus or have an open, sore appearance. • Signs of discomfort such as reluctance to move the affected area. • Systemic symptoms like fever (commonly above 102.5°F), lethargy, and loss of appetite. Treatment options generally involve veterinary intervention and can include: • Anesthesia for the dog, as abscesses are very painful. • Clipping the fur around the swollen area and disinfecting it with a surgical scrub solution (like betadine). • Lancing the abscess to drain the infection and flushing it with a solution (often a mix of hydrogen peroxide and water). • Leaving the incision open to allow it to heal from the inside out, and in some cases, placing a drain or “wick” to assist with ongoing drainage. • Prescription of oral antibiotics to help fight the infection. In addition to these standard treatments, a warm, moist compress may be applied as first aid until veterinary care is available, and supportive nutrition and care can help the dog recover more comfortably."
      },
      {
        "id": 2,
        "question": "How does acupuncture benefit dogs, and what conditions can it help treat?",
        "answer": "Acupuncture benefits dogs by stimulating specific points that trigger the release of neurochemicals or endorphins in the brain, which in turn provide pain relief and help promote overall balance in the body. One of its major advantages is that it generally causes few or no side effects. This makes it a particularly appealing supportive treatment in veterinary medicine. Some of the conditions that acupuncture can help treat in dogs include: • Seizures – Acupuncture has been used historically to manage seizures when conventional treatments have not been effective. • Pain and arthritis – By releasing natural pain-relieving chemicals, acupuncture can alleviate chronic pain and improve joint function in conditions like arthritis. • Musculoskeletal problems – It can address issues with the back and other structures, helping to relieve discomfort and improve mobility. • Reproductive disorders – It may support treatment plans for certain reproductive challenges. • Skin conditions – Dogs suffering from allergies or other dermatological issues may also benefit. • Neurological problems – The overall balancing effects can help with various neurological conditions. Overall, the therapy is often integrated into broader treatment plans, especially when owners are looking for a complementary or supportive approach to their pet’s care. If acupuncture is recommended, a veterinarian trained or certified in veterinary acupuncture should perform the treatment, or they may refer you to a specialist with additional training in this technique."
      }
    ],
    "set_id": 79
  }
}
```

### 4. Compare QnA Sets
To compare QnA sets and get similarity scores:
```http
POST /compare-qna
```


## Troubleshooting
- Ensure that all dependencies are installed.
- If the Flask server does not start, check for port conflicts or missing environment configurations.
- Verify that the `qwen2.5:14b` model is running before making API calls.

## Contributing
Feel free to contribute by submitting pull requests or reporting issues.
