# Water Test Analyzer

AI-powered water quality test analysis system. Upload PDF test results and get comprehensive AI analysis.

## 🚀 Features

- **PDF Upload**: Drag & drop PDF files with water test results
- **AI Analysis**: Advanced analysis using LangChain with multiple AI models (OpenRouter)
- **Real-time Progress**: Live workflow updates during analysis
- **PDF Report**: Download comprehensive analysis as PDF
- **Preview**: View analysis results in browser
- **Responsive Design**: Works on desktop and mobile devices

## 🎨 Design

- **Blue Water Theme**: Beautiful blue gradient color scheme
- **Modern UI**: Clean, intuitive interface with smooth animations
- **Accessibility**: WCAG compliant design
- **Mobile First**: Responsive layout optimized for all devices

## 🏗️ Architecture

### Frontend (React + TypeScript)
```
waterFront/src/
├── components/
│   ├── WaterAnalyzer.tsx      # Main application component
│   ├── Header.tsx             # Application header
│   ├── PDFDropzone.tsx        # File upload component
│   ├── AnalysisProgress.tsx   # Progress tracking
│   └── ResultsPanel.tsx       # Results display & download
├── services/
│   └── api.ts                 # API communication
├── types/
│   └── index.ts               # TypeScript definitions
└── App.tsx                    # App entry point
```

### Backend (Python + FastAPI + LangChain)
```
waterBack/
├── app/
│   ├── api/                   # API endpoints
│   │   ├── upload.py          # PDF upload handling
│   │   ├── analysis.py        # Analysis endpoints
│   │   └── streaming.py       # SSE streaming
│   ├── services/
│   │   ├── ai_analyzer.py     # LangChain AI integration
│   │   ├── pdf_processor.py   # PDF parsing
│   │   ├── report_generator.py # PDF report creation
│   │   └── workflow_manager.py # Process orchestration
│   ├── models/                # Pydantic models
│   ├── utils/                 # Utilities & validation
│   └── config.py              # Configuration
├── prompts/                   # AI prompts
└── requirements.txt           # Dependencies
```

### Workflow
1. **Upload**: User drops PDF file → FastAPI validates and stores
2. **Processing**: LangChain orchestrates AI analysis using OpenRouter models
3. **Analysis**: Multi-stage AI evaluation with specialized prompts
4. **Results**: Generate PDF report and provide preview/download

## 🔧 Configuration

### Environment Variables

#### Frontend (.env)
```env
# API Configuration
VITE_API_URL=http://localhost:2104
VITE_TEST_ENV=true
```

#### Backend (.env)
```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# AI Models Configuration
FAST_MODEL=google/gemini-2.5-flash-preview-05-20
BALANCED_MODEL=anthropic/claude-3-haiku-20240307
ADVANCED_MODEL=anthropic/claude-3-sonnet-20240229
PREMIUM_MODEL=anthropic/claude-3-opus-20240229

# App Configuration
HOST=localhost
PORT=2104
UPLOAD_FOLDER=uploads
DEBUG=true
TEST_ENV=true

# CORS Settings
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Development Setup

#### Frontend Setup
```bash
cd waterFront
npm install
npm run dev
```

#### Backend Setup
```bash
cd waterBack
pip install -r requirements.txt
python -m app.main
```

#### Production Build
```bash
# Frontend
cd waterFront
npm run build

# Backend
cd waterBack
uvicorn app.main:app --host 0.0.0.0 --port 2104
```

## 📚 API Endpoints

- `POST /api/upload-pdf` - Upload PDF file for analysis
- `GET /api/status/{analysis_id}` - Get analysis workflow status
- `GET /api/result/{analysis_id}` - Get complete analysis results
- `GET /api/preview/{analysis_id}` - Get markdown preview
- `GET /api/download/{analysis_id}` - Download analysis PDF report
- `GET /api/stream/{analysis_id}` - Server-Sent Events for real-time updates

## 🤖 AI Models & LangChain Integration

### OpenRouter Models
- **FAST**: `google/gemini-2.5-flash-preview-05-20` - Quick analysis
- **BALANCED**: `` - Standard analysis
- **ADVANCED**: `` - Detailed analysis
- **PREMIUM**: ` - Comprehensive analysis

### LangChain Features
- **Multi-model support** with automatic fallback
- **Structured prompts** for consistent analysis
- **Chain orchestration** for complex workflows
- **Error handling** and retry mechanisms
- **Token optimization** for cost efficiency

### Analysis Stages
1. **PDF Parsing**: Extract text from water test results
2. **Parameter Evaluation**: Analyze individual water parameters
3. **Health Assessment**: Evaluate health implications
4. **Recommendations**: Generate actionable advice
5. **Report Generation**: Create comprehensive PDF report

## 🎯 Usage

1. Open application in browser
2. Drag & drop PDF file with water test results
3. Click "Analizuj Badania" to start analysis
4. Monitor progress in real-time
5. Download PDF report or view preview when complete

## 🛡️ Security

- **File validation**: PDF only, max 10MB, magic number verification
- **Server-side processing**: All PDF parsing done on backend
- **API key protection**: OpenRouter keys secured via environment variables
- **CORS configuration**: Configurable origins for production
- **Input sanitization**: Validation of all user inputs
- **Rate limiting**: Protection against abuse (planned)
- **Secure uploads**: Temporary file handling with cleanup

## 📱 Responsive Design

- Mobile-first approach
- Touch-friendly interface
- Optimized for tablets and phones
- Progressive Web App features

## 🔍 Debug Mode

Enable debug logging:
```env
# Frontend
VITE_TEST_ENV=true

# Backend
TEST_ENV=true
DEBUG=true
```

Debug logs include:
- **File upload details**: Size, type, validation
- **API request/response**: Full HTTP traces
- **LangChain operations**: Model calls, token usage
- **Workflow progress**: Real-time step updates
- **Error diagnostics**: Stack traces and context
- **AI model performance**: Response times, fallbacks

## 🎨 Color Theme

Blue water theme with custom Tailwind colors:
- `water-blue-50` to `water-blue-900`
- Gradient backgrounds
- Smooth transitions
- Consistent visual hierarchy

## 🔄 State Management

Simple React state management:
- Upload state tracking
- Progress monitoring
- Error handling
- Results caching

## 🚀 Performance

### Frontend Optimizations
- **Lazy loading**: Components loaded on demand
- **Bundle optimization**: Tree shaking and code splitting
- **Efficient re-renders**: React.memo and useMemo
- **API caching**: Response caching for better UX

### Backend Optimizations
- **Async processing**: Non-blocking I/O operations
- **LangChain caching**: Model response caching
- **Streaming responses**: Server-Sent Events for real-time updates
- **Memory management**: Efficient PDF processing
- **Connection pooling**: Optimized HTTP client usage

## 📄 File Support

- **Input**: PDF files only
- **Max size**: 10MB
- **Output**: PDF analysis report
- **Preview**: Markdown format

## 🎪 Animations

- Framer Motion animations
- Smooth transitions
- Loading states
- Progress indicators
- Interactive feedback 