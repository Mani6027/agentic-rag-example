# Quick Start Guide

Get your Agentic RAG Excel Analyzer up and running in 5 minutes!

## Step 1: Setup Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Google API key
# Get one from: https://makersuite.google.com/app/apikey
nano .env  # or use your favorite editor
```

Your `.env` should look like:
```env
GOOGLE_API_KEY=your_actual_api_key_here
MODEL_NAME=gemini-2.0-flash-exp
TEMPERATURE=0.1
MAX_ITERATIONS=10
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
```

## Step 3: Run the Server

```bash
# Start the FastAPI server
python3 -m src.main
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test with Swagger UI

1. Open your browser: http://localhost:8000/docs
2. You'll see the interactive API documentation

## Step 5: Upload Your First Excel File

### Using Swagger UI:
1. Go to http://localhost:8000/docs
2. Click on `POST /api/upload`
3. Click "Try it out"
4. Choose your Excel file
5. Click "Execute"
6. Copy the `dataset_id` from the response

### Using curl:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@your_excel_file.xlsx"
```

## Step 6: Query Your Data

### Using Swagger UI:
1. Click on `POST /api/query`
2. Click "Try it out"
3. Enter:
   - `dataset_id`: (from upload response)
   - `query`: "What is the total sales?"
4. Click "Execute"

### Using curl:
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your-dataset-id-here",
    "query": "What is the total sales?"
  }'
```

## Example Queries to Try

Once you have data uploaded, try these queries:

1. **Simple Aggregation**
   ```
   "What is the total sales?"
   ```

2. **Filtering**
   ```
   "Show me all products with sales greater than 1000"
   ```

3. **Group Analysis**
   ```
   "Compare sales across all regions"
   ```

4. **Complex Questions**
   ```
   "Which product has the highest average sales per region?"
   ```

5. **Trends**
   ```
   "How have sales changed over time?"
   ```

## Troubleshooting

### Issue: Import errors when running
**Solution**: Make sure you're in the project root and use:
```bash
python3 -m src.main
```

### Issue: "API key not found"
**Solution**: Check your `.env` file exists and has `GOOGLE_API_KEY=...`

### Issue: Module not found
**Solution**: Reinstall dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Port 8000 already in use
**Solution**: Use a different port:
```bash
uvicorn src.main:app --port 8001
```

## Next Steps

- Check out the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Try different types of queries
- Upload multiple Excel files

## Need Help?

- Check the logs in `agentic_rag.log`
- API docs: http://localhost:8000/docs
- Set `LOG_LEVEL=DEBUG` in `.env` for more details
