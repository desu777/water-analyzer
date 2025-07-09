# Water Test Analyzer

AI-powered water quality test analysis system. Upload PDF test results and get comprehensive AI analysis.

## 🚀 Features

- **PDF Upload**: Drag & drop PDF files with water test results
- **AI Analysis**: Advanced analysis using OpenAI/Anthropic models
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
src/
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

### Workflow
1. **Upload**: User drops PDF file
2. **Processing**: AI analyzes test results
3. **Results**: Download PDF report or view preview

## 🔧 Configuration

### Environment Variables
```env
# API Configuration
VITE_API_URL=http://localhost:2104
VITE_TEST_ENV=true

# AI Models (sensitive - see doors.md)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Development Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📚 API Endpoints

- `POST /api/upload-pdf` - Upload PDF file
- `GET /api/status/:id` - Get analysis status
- `GET /api/result/:id` - Get analysis results
- `GET /api/preview/:id` - Get markdown preview
- `GET /api/download/:id` - Download analysis PDF
- `GET /api/stream/:id` - Stream workflow updates

## 🎯 Usage

1. Open application in browser
2. Drag & drop PDF file with water test results
3. Click "Analizuj Badania" to start analysis
4. Monitor progress in real-time
5. Download PDF report or view preview when complete

## 🛡️ Security

- File validation (PDF only, max 10MB)
- Server-side PDF parsing
- API key protection via environment variables
- CORS configuration for production

## 📱 Responsive Design

- Mobile-first approach
- Touch-friendly interface
- Optimized for tablets and phones
- Progressive Web App features

## 🔍 Debug Mode

Enable debug logging:
```env
VITE_TEST_ENV=true
```

Debug logs include:
- File upload details
- API request/response data
- Workflow progress updates
- Error diagnostics

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

- Lazy loading components
- Optimized bundle size
- Efficient re-renders
- Cached API responses

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