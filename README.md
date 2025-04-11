# LitLinker
[Paper](https://arxiv.org/pdf/2502.16097)

# Backend
## Requirements

- Python 3.7+
- FastAPI for the web framework
- MongoDB for data storage
- External models for case and text analysis (e.g., embeddings, cosine similarity)

## Installation

1. Clone this repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your MongoDB database and configure the connection details in the code.

## Running the Application

To run the FastAPI server, use the following command:
```
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:5000`.

# Frontend
Please check README.md in frontend folder.
