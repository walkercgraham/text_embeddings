# Getting Started Checklist

## ✅ For New Team Members

Follow this checklist to get started with the Azure Search Vector Embedding Pipeline:

### 1. Prerequisites Check
- [ ] Python 3.8 or higher installed
- [ ] Access to Azure AI Search service
- [ ] Access to Azure OpenAI service with embedding deployment
- [ ] Admin API keys for both services

### 2. Initial Setup (5 minutes)

```bash
# Clone or copy this template
cd text_embeddings_vector_db

# Install dependencies
pip install -r requirements.txt

# Create your .env file from template
cp .env.example .env
```

### 3. Configure Credentials (5 minutes)

Edit `.env` file and fill in these required values:

```bash
# Azure AI Search
AZURE_SEARCH_SERVICE=your_service_name        # Just the name, not full URL
AZURE_SEARCH_ADMIN_KEY=your_admin_key
AZURE_SEARCH_INDEX_NAME=your_index_name       # Choose a name for your index

# Azure OpenAI - Embeddings
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-endpoint
AZURE_OPENAI_EMBEDDING_KEY=your_key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

**Where to find these:**
- Azure Search: Portal → Your Search Service → Keys
- Azure OpenAI: Portal → Your OpenAI Service → Keys and Endpoint

### 4. Prepare Your Data (2 minutes)

- [ ] Place your CSV file in the `data/` folder
- [ ] Update `CSV_FILE_PATH` in `.env` to point to your file
- [ ] Note which column contains the text you want to embed
- [ ] Note which columns are datetime fields

### 5. Customize for Your Project (15 minutes)

#### A. Update Index Schema

Edit `scripts/create_index.py` (or `notebooks/01_create_index.ipynb`):

```python
INDEX_SCHEMA = {
    "name": config.azure_search_index_name,
    "fields": [
        {
            "name": "your_id_field",      # ← Change this
            "type": "Edm.String",
            "key": True,
            "filterable": True
        },
        {
            "name": "your_text_field",    # ← Change this
            "type": "Edm.String",
            "searchable": True
        },
        # Add more fields as needed
        {
            "name": "embedding",          # ← Keep this for vectors
            "type": "Collection(Edm.Single)",
            "dimensions": 1536,
            "searchable": True,
            "retrievable": True,
            "vectorSearchProfile": "myHnswProfile"
        }
    ],
    # ... vector search config (can leave as-is)
}
```

#### B. Update Field Mapping

Edit `scripts/embed_and_upload.py` (or `notebooks/02_embed_and_upload.ipynb`):

```python
FIELD_MAPPING = {
    # CSV Column Name : Index Field Name
    "your_csv_id_col": "your_id_field",
    "your_csv_text_col": "your_text_field",
    # Map all your CSV columns here
}

TEXT_COLUMN_TO_EMBED = "your_csv_text_col"  # Which column to embed

DATETIME_COLUMNS = ["date_col_1", "date_col_2"]  # Which are dates
```

### 6. Test with Small Dataset (5 minutes)

Always test first with a small batch:

```bash
# Create the index
python scripts/create_index.py

# Test with 10 rows
python scripts/embed_and_upload.py --max-rows 10

# Verify it worked
python scripts/search_index.py --query "test" --mode hybrid
```

### 7. Run Full Pipeline (depends on data size)

Once testing succeeds:

```bash
# Process all data
python scripts/embed_and_upload.py

# If interrupted, resume:
python scripts/embed_and_upload.py --resume
```

### 8. Verify Results

```bash
# Test different search modes
python scripts/search_index.py --query "your search" --mode text
python scripts/search_index.py --query "your search" --mode vector
python scripts/search_index.py --query "your search" --mode hybrid
```

## 🎯 Common Use Cases

### Use Case 1: Using Jupyter Notebooks

Prefer interactive development? Use the notebooks:

```bash
jupyter notebook
# Open notebooks/01_create_index.ipynb
# Then open notebooks/02_embed_and_upload.ipynb
```

### Use Case 2: Integrating into Your Application

```python
from utils import config, hybrid_search

# Search your index
results = hybrid_search(
    query="office furniture",
    top_k=10,
    search_fields=["item_text", "vendor_name"]
)

for doc in results["value"]:
    print(f"Score: {doc['@search.score']}")
    print(f"Text: {doc['item_text']}")
```

### Use Case 3: Automating with Cron/Scheduler

```bash
# Add to cron for daily updates
0 2 * * * cd /path/to/project && python scripts/embed_and_upload.py --resume
```

## 🐛 Troubleshooting

### "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "Missing required environment variables"
- Check your `.env` file exists
- Verify all required fields are filled in
- No quotes around values in `.env`

### "SSL Certificate Error"
- Expected when using IP-based endpoints
- The code handles this automatically
- Warnings can be ignored (or suppressed in the code)

### "Failed to generate embedding"
- Check your Azure OpenAI endpoint and key
- Verify the deployment name matches
- Check if you have quota/rate limits

### Checkpoint is corrupted
```bash
rm data/checkpoint.parquet
python scripts/embed_and_upload.py
```

## 📚 Next Steps

Once your pipeline is running:

1. **Optimize Search:** Tune HNSW parameters in index schema
2. **Monitor Costs:** Track embedding API usage
3. **Add Features:** Extend the utility modules as needed
4. **Share Template:** Help other team members get started

## 💡 Pro Tips

1. **Start small:** Always test with 10-100 rows first
2. **Use hybrid search:** Best results in most cases
3. **Monitor checkpoints:** Watch `data/checkpoint.parquet` grow
4. **Backup .env:** Keep credentials in a secure password manager
5. **Version control:** Commit everything except `.env` and checkpoints

## 🤝 Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review inline comments in the code
- Check Azure documentation for specific API questions
- Ask team members who have used the template

## ✨ You're Ready!

Once you complete this checklist, you'll have a working vector search pipeline. The template is designed to be:

- **Fast to set up:** 30 minutes from zero to working pipeline
- **Easy to customize:** Clear patterns and documentation
- **Production-ready:** Checkpointing, error handling, and logging
- **Reusable:** Use for multiple projects with minimal changes

Happy searching! 🚀
