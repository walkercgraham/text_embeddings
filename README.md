# Azure Search Vector Embedding Pipeline

A clean, reusable template for creating Azure AI Search indices with vector embeddings from CSV data. Supports text search, vector search, and hybrid search.

## 🎯 What This Does

This template helps you:
- Create Azure AI Search indices with vector search capabilities
- Generate embeddings from text data using Azure OpenAI
- Upload large datasets with automatic checkpointing
- Search using three modes: text (BM25), vector (semantic), or hybrid (best of both)

## 📋 Prerequisites

- Python 3.8+
- Azure AI Search account
- Azure OpenAI account with text-embedding-ada-002 deployment (or similar)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the example environment file and fill in your Azure credentials:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Required credentials in `.env`:
- `AZURE_SEARCH_SERVICE` - Your Azure Search service name
- `AZURE_SEARCH_ADMIN_KEY` - Admin API key
- `AZURE_SEARCH_INDEX_NAME` - Name for your index
- `AZURE_OPENAI_EMBEDDING_ENDPOINT` - Azure OpenAI endpoint (can be IP address)
- `AZURE_OPENAI_EMBEDDING_KEY` - API key for embeddings
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` - Deployment name (e.g., "text-embedding-ada-002")

### 3. Create the Index

```bash
python scripts/create_index.py
```

Or to delete and recreate:
```bash
python scripts/create_index.py --delete-existing
```

### 4. Upload Your Data

```bash
python scripts/embed_and_upload.py
```

This will:
- Load your CSV data
- Generate embeddings for each row
- Upload to Azure Search
- Save checkpoints every 250 rows

Resume if interrupted:
```bash
python scripts/embed_and_upload.py --resume
```

### 5. Test Search

```bash
# Text search (keyword matching)
python scripts/search_index.py --query "office chair" --mode text

# Vector search (semantic similarity)
python scripts/search_index.py --query "office chair" --mode vector

# Hybrid search (recommended - combines both)
python scripts/search_index.py --query "office chair" --mode hybrid --top 5
```

## 📓 Using Jupyter Notebooks

For interactive development, use the notebooks:

1. **`notebooks/01_create_index.ipynb`** - Create the index
2. **`notebooks/02_embed_and_upload.ipynb`** - Embed and upload data (CSV or Celonis)
3. **`notebooks/03_celonis_direct_connection.ipynb`** - Step-by-step Celonis extraction guide

Start Jupyter:
```bash
jupyter notebook
```

## 🔧 Adapting for Your Project

### 1. Update Index Schema

Edit `scripts/create_index.py` (or the notebook) to modify fields:

```python
INDEX_SCHEMA = {
    "name": config.azure_search_index_name,
    "fields": [
        {
            "name": "my_id_field",
            "type": "Edm.String",
            "key": True,
            "filterable": True
        },
        {
            "name": "my_text_field",
            "type": "Edm.String",
            "searchable": True
        },
        # ... add your fields here
        {
            "name": "embedding",
            "type": "Collection(Edm.Single)",
            "dimensions": 1536,  # Change if using different model
            "searchable": True,
            "retrievable": True,
            "vectorSearchProfile": "myHnswProfile"
        }
    ],
    # ... vector search configuration
}
```

### 2. Update Field Mapping

Edit `scripts/embed_and_upload.py` to map your CSV columns:

```python
FIELD_MAPPING = {
    # CSV Column Name : Index Field Name
    "your_csv_id_column": "my_id_field",
    "your_csv_text_column": "my_text_field",
    # ... map all your columns
}

# Which column to embed?
TEXT_COLUMN_TO_EMBED = "your_csv_text_column"

# Which columns are dates?
DATETIME_COLUMNS = ["date_column_1", "date_column_2"]
```

### 3. Replace Your Data

Put your CSV file in the `data/` folder and update `.env`:

```bash
CSV_FILE_PATH=data/your_data.csv
```

### 4. Update Search Fields

For hybrid search, specify which fields to search in `scripts/search_index.py`:

```python
search_fields = ["my_text_field", "another_searchable_field"]
```

## 📡 Celonis Integration (Optional)

You can load data directly from Celonis EMS instead of CSV files.

### 1. Install pycelonis

```bash
pip install --extra-index-url=https://pypi.celonis.cloud/ pycelonis
```

### 2. Configure Celonis Credentials

Add to your `.env` file:

```bash
DATA_SOURCE=celonis

CELONIS_BASE_URL=https://your-team.eu-1.celonis.cloud/
CELONIS_API_TOKEN=your_api_token_here
CELONIS_KEY_TYPE=APP_KEY
CELONIS_DATA_POOL_NAME=your_data_pool_name
CELONIS_DATA_MODEL_NAME=your_data_model_name
```

### 3. Run with Celonis

**Script:**
```bash
# Use Celonis as data source
python scripts/embed_and_upload.py --source celonis --max-rows 10

# Override .env setting from CLI
python scripts/embed_and_upload.py --source csv
```

**Notebook 02:** Set `DATA_SOURCE = "celonis"` in the configuration cell.

**Notebook 03:** Follow the dedicated step-by-step Celonis guide.

### 4. Customize PQL Columns

Edit the `CELONIS_PQL_COLUMNS` list in the script or notebook to match your data model:

```python
CELONIS_PQL_COLUMNS = [
    {"name": "Id",        "query": '"YourTable"."ID"'},
    {"name": "ShortText", "query": '"YourTable"."Description"'},
    # ... add columns matching your FIELD_MAPPING keys
]
```

> **Note:** If pycelonis is not installed, CSV-only workflows continue to work without errors.

## 🔍 Search Modes Explained

### Text Search (BM25)
- Traditional keyword matching
- Fast and efficient
- Best for exact term matches
- Use when you know specific keywords

### Vector Search (Semantic)
- Understands meaning and context
- Finds conceptually similar items
- Language-agnostic
- Best for natural language queries

### Hybrid Search (Recommended)
- Combines text + vector search using Reciprocal Rank Fusion (RRF)
- Gets best of both worlds
- Balances precision and recall
- **Use this for most applications**

## 📁 Project Structure

```
text_embeddings_vector_db/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env                              # Your credentials (gitignored)
├── .env.example                       # Template for credentials
├── .gitignore                        # Ignore .env and checkpoints
├── data/
│   └── contract_items_reduced.csv    # Your CSV data
├── notebooks/
│   ├── 01_create_index.ipynb         # Interactive index creation
│   ├── 02_embed_and_upload.ipynb     # Interactive embedding pipeline (CSV or Celonis)
│   └── 03_celonis_direct_connection.ipynb  # Step-by-step Celonis guide
├── scripts/
│   ├── create_index.py               # Create index (CLI)
│   ├── embed_and_upload.py           # Embed and upload (CLI, --source csv|celonis)
│   └── search_index.py               # Search testing (CLI)
└── utils/
    ├── __init__.py
    ├── config.py                     # Load .env configuration
    ├── celonis_connection.py         # Celonis EMS integration (optional)
    ├── azure_search.py               # Index and search operations
    ├── embeddings.py                 # Embedding generation
    └── data_processing.py            # CSV handling and checkpoints
```

## ⚙️ Configuration Options

Edit `.env` to customize:

```bash
# Processing batch size
BATCH_SIZE=5000

# Delay between batches (seconds)
SLEEP_BETWEEN_BATCHES=5.0

# Delay between individual requests (seconds)
SLEEP_BETWEEN_REQUESTS=0.25

# Checkpoint file location
CHECKPOINT_FILE_PATH=data/checkpoint.parquet
```

## 🔐 Security Notes

- **Never commit `.env` file** - it contains your API keys
- The `.gitignore` file already excludes `.env` and checkpoints
- Use `.env.example` as a template for sharing configuration structure
- For production, consider using Azure Key Vault or similar

## 🐛 Troubleshooting

### SSL Certificate Errors

If using an IP-based endpoint, SSL warnings are expected. The code disables SSL verification for IP addresses. To suppress warnings:

```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### Checkpoint Issues

If your checkpoint gets corrupted:

```bash
rm data/checkpoint.parquet
python scripts/embed_and_upload.py
```

### Rate Limiting

If you hit rate limits, adjust in `.env`:

```bash
SLEEP_BETWEEN_REQUESTS=0.5  # Increase delay between requests
```

## 📊 Checkpointing & Resume

The pipeline automatically saves progress every 250 rows. If interrupted:

1. **Notebooks:** Just run the cells again - they'll resume automatically
2. **Scripts:** Use `--resume` flag: `python scripts/embed_and_upload.py --resume`

Checkpoint files are stored as Parquet format in `data/checkpoint.parquet`.

## 🧪 Testing

Test on a small batch first:

```bash
# Process only 10 rows
python scripts/embed_and_upload.py --max-rows 10
```

Or in the notebook, use:
```python
process_rows(df, max_rows=10)
```

## 💡 Tips

1. **Start Small:** Test with 10-100 rows before processing large datasets
2. **Use Hybrid Search:** It provides the best results in most cases
3. **Monitor Costs:** Embedding generation incurs OpenAI API costs
4. **Tune HNSW:** Adjust `m`, `efConstruction`, and `efSearch` for performance vs accuracy
5. **Check Index Stats:** Use `get_index_stats()` to verify uploads

## 📚 Additional Resources

- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Azure OpenAI Embeddings](https://learn.microsoft.com/azure/ai-services/openai/concepts/understand-embeddings)
- [Vector Search in Azure AI Search](https://learn.microsoft.com/azure/search/vector-search-overview)

## 🤝 Contributing

This is a template project. Feel free to:
- Customize for your use case
- Add features you need
- Share improvements with your team

## 📝 License

This template is provided as-is for internal use. Customize as needed for your organization.

---

**Need Help?** Check the inline comments in the code or refer to the Azure documentation linked above.
