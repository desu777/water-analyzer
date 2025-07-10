# Water Test Analyzer Backend

AI-powered backend for water quality test analysis using FastAPI, LangChain, and OpenRouter.

## 🏗️ Architecture

### Tech Stack
- **Framework:** FastAPI (Python)
- **AI Integration:** LangChain + OpenRouter API
- **PDF Processing:** PyPDF2, pdfplumber
- **Report Generation:** ReportLab
- **Real-time Updates:** Server-Sent Events (SSE)

### Project Structure
```
waterBack/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── upload.py          # PDF upload
│   │   ├── analysis.py        # Analysis results
│   │   └── streaming.py       # SSE streaming
│   ├── models/                # Data models
│   │   ├── requests.py        # Request models
│   │   ├── responses.py       # Response models
│   │   └── water_data.py      # Water analysis models
│   ├── services/              # Business logic
│   │   ├── pdf_processor.py   # PDF text extraction
│   │   ├── ai_analyzer.py     # AI analysis
│   │   ├── report_generator.py # PDF report generation
│   │   └── workflow_manager.py # Progress tracking
│   ├── utils/                 # Utilities
│   │   ├── logger.py          # Logging system
│   │   ├── file_handler.py    # File operations
│   │   └── validation.py      # Input validation
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── prompts/                   # AI prompts
│   ├── water_analysis_main.txt
│   ├── water_parameters_eval.txt
│   ├── recommendations.txt
│   └── report_formatting.txt
├── requirements.txt           # Dependencies
├── doors.md                   # Environment gateway
└── README.md                  # Documentation
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Copy the `.env.example` file and configure:
```bash
# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Model Names (configurable)
OPENROUTER_MODEL_FAST=openai/gpt-3.5-turbo
OPENROUTER_MODEL_BALANCED=anthropic/claude-3-haiku
OPENROUTER_MODEL_ADVANCED=anthropic/claude-3-opus
OPENROUTER_MODEL_PREMIUM=openai/gpt-4-turbo

# Model Selection
OPENROUTER_DEFAULT_MODEL=BALANCED
OPENROUTER_FALLBACK_MODEL=FAST

# App Configuration
APP_HOST=localhost
APP_PORT=2104
DEBUG_MODE=true
```

### 3. Run the Server
```bash
# Development mode
python -m app.main

# Or with uvicorn
uvicorn app.main:app --host localhost --port 2104 --reload
```

### 4. Access API Documentation
- **Swagger UI:** http://localhost:2104/docs
- **ReDoc:** http://localhost:2104/redoc

## 📚 API Endpoints

### Upload
- `POST /api/upload-pdf` - Upload PDF file for analysis

### Analysis
- `GET /api/status/{analysis_id}` - Get analysis status
- `GET /api/result/{analysis_id}` - Get analysis results
- `GET /api/preview/{analysis_id}` - Get markdown preview
- `GET /api/download/{analysis_id}` - Download PDF report

### Streaming
- `GET /api/stream/{analysis_id}` - SSE progress stream

### Health
- `GET /api/health` - Health check

### Report Management
- `GET /api/report-status/{analysis_id}` - Check report availability status

## 🔄 Analysis Workflow

1. **Upload** (0-10%) - File validation and storage
2. **Parsing** (10-30%) - PDF text extraction and data parsing
3. **Analysis** (30-80%) - AI-powered water quality analysis
4. **Generation** (80-95%) - PDF report generation
5. **Complete** (95-100%) - Analysis ready for download

## 🤖 AI Integration

### OpenRouter Models
- **Fast:** `openai/gpt-3.5-turbo` (quick analysis)
- **Balanced:** `anthropic/claude-3-haiku` (default)
- **Advanced:** `anthropic/claude-3-opus` (detailed analysis)
- **Premium:** `openai/gpt-4-turbo` (highest quality)

### Prompt System
Modular prompt system with separate files:
- **Main Analysis:** Comprehensive water quality assessment
- **Parameter Evaluation:** Individual parameter analysis
- **Recommendations:** Practical action items
- **Report Formatting:** Professional report structure

## 📋 Features

### PDF Processing
- Multiple extraction methods (pdfplumber, PyPDF2)
- Table detection and parsing
- Polish water parameter recognition
- Metadata extraction

### AI Analysis
- Polish water quality standards compliance
- Health risk assessment
- Filtration system recommendations
- Educational explanations

### Report Generation
- Professional PDF reports
- Color-coded parameter status
- Actionable recommendations
- Compliance documentation

### Real-time Progress
- Server-Sent Events streaming
- Workflow step tracking
- Error handling and recovery
- Background task processing

### Report Management
- **10-minute report lifetime** - optimal storage management
- **Automatic cleanup** - reports deleted after download or expiration
- **Download tracking** - faster cleanup for downloaded reports
- **Status monitoring** - real-time report availability checking

## 🔧 Configuration

### Model Selection
All model names are configurable via environment variables:
```env
OPENROUTER_MODEL_FAST=openai/gpt-3.5-turbo
OPENROUTER_MODEL_BALANCED=anthropic/claude-3-haiku
```

### Debug Mode
Enable detailed logging:
```env
DEBUG_MODE=true
```

### File Limits
```env
MAX_PDF_SIZE_MB=10
```

### Report Cleanup
```env
REPORT_LIFETIME_MINUTES=10          # Report expiration time
CLEANUP_INTERVAL_MINUTES=5          # Cleanup check frequency
POST_DOWNLOAD_CLEANUP_MINUTES=1     # Time after download to delete
```

## 🛠️ Development

### Adding New Prompts
1. Create new `.txt` file in `prompts/` directory
2. Load in `ai_analyzer.py` using `_load_prompt()` method
3. Use in analysis workflow

### Custom Water Parameters
Extend parameter patterns in `pdf_processor.py`:
```python
parameter_patterns = {
    'new_param': r'new_param[:\s]+(\d+[,.]?\d*)\s*(\w+)',
    # ...
}
```

### Error Handling
- Global exception handler
- Validation errors
- AI fallback models
- Graceful degradation

## 📦 Dependencies

### Core
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File uploads

### AI & Processing
- `langchain` - AI orchestration
- `langchain-openai` - OpenRouter integration
- `PyPDF2` - PDF processing
- `pdfplumber` - Table extraction

### Reports & Utils
- `reportlab` - PDF generation
- `python-dotenv` - Environment management
- `pydantic` - Data validation

## 🔒 Security

- Input validation for all uploads
- File type verification
- Size limits enforcement
- Secure file handling
- Environment variable protection

## 📈 Monitoring

- Comprehensive logging system
- Session tracking
- Performance metrics
- Error reporting
- Debug mode support

## 🧪 Testing

```bash
# Run tests
pytest

# Test specific component
pytest app/tests/test_pdf_processor.py
```

## 🚀 Production Deployment

### Docker
```dockerfile
FROM python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "2104"]
```

### Environment Variables
Set production values for:
- `OPENROUTER_API_KEY`
- `DEBUG_MODE=false`
- `CORS_ORIGINS`
- File storage paths

---

## 📞 Support

For technical support or questions about the Water Test Analyzer backend, please check the documentation or create an issue in the project repository. 