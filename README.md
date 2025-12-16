# Agentic RAG Excel Analyzer

An AI-powered Excel data analysis system using LangChain, Google Gemini 2.0 Flash, and RAG (Retrieval-Augmented Generation). The system combines semantic understanding through vector search with precise pandas calculations to answer natural language questions about Excel data.

## Features

- **Natural Language Queries**: Ask questions about your Excel data in plain English
- **ReAct Agent**: Intelligent agent that reasons about queries and breaks them into steps
- **RAG Integration**: Uses vector search to understand column meanings and data structure
- **Precise Calculations**: Pandas-based tools ensure numerical accuracy
- **Multi-Sheet Support**: Handle Excel files with multiple sheets
- **REST API**: Clean HTTP API for integration

## Capabilities

The agent can perform:
- **Data Queries**: Filter and search data based on conditions
- **Aggregations**: Sum, average, count, min, max, standard deviation
- **Group Analysis**: Group by columns and aggregate
- **Correlations**: Calculate relationships between numeric columns
- **Trend Analysis**: Analyze changes over time
- **Complex Analysis**: Multi-step reasoning for advanced questions

## Architecture

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  RAG (Chroma Vector Store)      │
│  - Column metadata              │
│  - Data relationships           │
│  - Schema understanding         │
└──────┬──────────────────────────┘
       │ Context
       ▼
┌─────────────────────────────────┐
│  ReAct Agent (Gemini 2.0)       │
│  - Understands query            │
│  - Plans execution steps        │
│  - Uses pandas tools            │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Pandas Tools                   │
│  - Filter data                  │
│  - Aggregate                    │
│  - Group by                     │
│  - Calculate stats              │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│   Result    │
└─────────────┘
```

## Setup

### Prerequisites

- Python 3.9+
- Google Gemini API key

### Installation

1. Clone the repository
```bash
cd agentic-rag
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.0-flash-exp
TEMPERATURE=0.1
MAX_ITERATIONS=10
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
```

### Get a Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Copy your API key and add it to `.env`

## Running the Application

### Start the server

```bash
python -m src.main
```

Or with uvicorn:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model": "gemini-2.0-flash-exp"
}
```

### 2. Upload Excel File
```http
POST /api/upload
Content-Type: multipart/form-data
```

Example with curl:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@sales_data.xlsx"
```

Response:
```json
{
  "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "sales_data.xlsx",
  "sheets": ["Sales"],
  "columns": {
    "Sales": ["date", "product", "region", "sales", "quantity"]
  },
  "rows_count": {
    "Sales": 1000
  },
  "message": "File uploaded and processed successfully"
}
```

### 3. Query Dataset
```http
POST /api/query
Content-Type: application/json
```

Request body:
```json
{
  "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
  "query": "What is the total sales in the North region?",
  "sheet_name": "Sales"
}
```

Example with curl:
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your-dataset-id",
    "query": "What is the total sales in the North region?"
  }'
```

Response:
```json
{
  "query": "What is the total sales in the North region?",
  "answer": "The total sales in the North region is $125,450.00. This is based on 250 transactions.",
  "execution_steps": [
    {
      "step": 1,
      "action": "query_data",
      "action_input": "region == 'North'",
      "observation": "Filtered to 250 rows"
    },
    {
      "step": 2,
      "action": "aggregate_data",
      "action_input": {"column": "sales", "operation": "sum"},
      "observation": "Sum: 125450.00"
    }
  ],
  "rag_context_used": "Column: sales\nType: numeric\nDescription: Sales revenue in USD...",
  "success": true
}
```

### 4. Get Dataset Info
```http
GET /api/dataset/{dataset_id}?include_sample=true
```

Response:
```json
{
  "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "sales_data.xlsx",
  "uploaded_at": "2025-12-16T10:30:00Z",
  "sheets": ["Sales"],
  "columns": {
    "Sales": ["date", "product", "region", "sales", "quantity"]
  },
  "rows_count": {
    "Sales": 1000
  },
  "sample_data": {
    "Sales": [
      {"date": "2025-01-01", "product": "Widget A", "region": "North", "sales": 100, "quantity": 5}
    ]
  }
}
```

### 5. List All Datasets
```http
GET /api/datasets
```

Response:
```json
{
  "datasets": [
    {
      "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "sales_data.xlsx",
      "uploaded_at": "2025-12-16T10:30:00Z",
      "sheets": ["Sales"]
    }
  ],
  "total": 1
}
```

### 6. Delete Dataset
```http
DELETE /api/dataset/{dataset_id}
```

Response:
```json
{
  "message": "Dataset deleted successfully",
  "dataset_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Example Queries

### Simple Aggregation
```json
{
  "query": "What is the total sales?"
}
```

### Filtering + Aggregation
```json
{
  "query": "What is the average sales in the North region?"
}
```

### Group Analysis
```json
{
  "query": "Compare total sales between all regions"
}
```

### Complex Multi-Step
```json
{
  "query": "Which product has the highest average sales, and what region contributes the most?"
}
```

### Correlation
```json
{
  "query": "Is there a correlation between quantity and sales?"
}
```

### Trend Analysis
```json
{
  "query": "How have sales changed over time?"
}
```

## Project Structure

```
agentic-rag/
├── src/
│   ├── main.py                  # FastAPI app entry point
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── api/
│   │   ├── routes.py            # API endpoints
│   │   └── schemas.py           # Pydantic models
│   ├── agent/
│   │   ├── executor.py          # ReAct agent orchestration
│   │   ├── tools.py             # 8 pandas-based tools
│   │   └── prompts.py           # System prompts
│   ├── rag/
│   │   ├── embeddings.py        # Google Generative AI embeddings
│   │   ├── vector_store.py      # Chroma vector store
│   │   └── metadata_builder.py # Metadata extraction
│   ├── data/
│   │   ├── excel_handler.py     # Excel file processing
│   │   └── storage.py           # In-memory data store
│   └── utils/
│       ├── logger.py            # Logging
│       └── validators.py        # Input validation
├── uploads/                     # Uploaded files
├── tests/                       # Tests
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

1. **Upload**: User uploads Excel file → System reads it → Extracts metadata → Embeds metadata into Chroma
2. **Query**: User asks question → RAG retrieves relevant column/schema info → Agent creates plan → Executes with pandas tools → Returns answer
3. **RAG Role**: Helps agent understand what columns mean, not for calculations
4. **Tools Role**: Perform precise calculations using pandas

## Key Design Decisions

- **RAG for Understanding**: Vector store holds metadata about columns, not data itself
- **Pandas for Calculations**: All numerical operations use pandas for accuracy
- **ReAct Agent**: Agent reasons about query and uses tools step by step
- **In-Memory Storage**: Fast access, simple setup (can be extended to persistent DB)

## Limitations

- Data is stored in memory (lost on restart)
- File size limit: 50 MB
- No formula execution (by design)
- Single-user (no authentication)

## Future Enhancements

- Persistent storage (PostgreSQL)
- Chart/visualization generation
- Multi-file joins
- Authentication and API keys
- Caching for repeated queries
- Export results to Excel/CSV

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root:
```bash
python -m src.main
```

### API Key Issues
Verify your `.env` file has the correct API key:
```bash
cat .env | grep GOOGLE_API_KEY
```

### Dependencies
If packages are missing:
```bash
pip install -r requirements.txt --upgrade
```

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
