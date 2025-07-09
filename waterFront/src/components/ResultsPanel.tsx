import { useState } from 'react';
import { motion } from 'framer-motion';
import { AnalysisResult } from '../types';
import waterAnalysisApi from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Download, 
  Eye, 
  FileText, 
  RefreshCw, 
  Calendar, 
  Clock,
  AlertCircle
} from 'lucide-react';

interface ResultsPanelProps {
  result: AnalysisResult | null;
  analysisId: string;
  onReset: () => void;
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({ result, analysisId, onReset }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewContent, setPreviewContent] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleDownload = async () => {
    if (!analysisId) return;
    
    setIsDownloading(true);
    setError('');
    
    try {
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log('📥 [ResultsPanel] Starting PDF download...');
      }
      
      const blob = await waterAnalysisApi.downloadAnalysisPDF(analysisId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `analiza_badania_wody_${new Date().toISOString().split('T')[0]}.pdf`;
      
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log('✅ [ResultsPanel] PDF download completed');
      }
      
    } catch (error) {
      console.error('❌ [ResultsPanel] Download failed:', error);
      setError('Nie udało się pobrać pliku PDF');
    } finally {
      setIsDownloading(false);
    }
  };

  const handlePreview = async () => {
    if (!analysisId) return;
    
    setError('');
    
    try {
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log('👁️ [ResultsPanel] Loading preview...');
      }
      
      const preview = await waterAnalysisApi.getAnalysisPreview(analysisId);
      setPreviewContent(preview.markdown);
      setShowPreview(true);
      
    } catch (error) {
      console.error('❌ [ResultsPanel] Preview failed:', error);
      setError('Nie udało się załadować podglądu');
    }
  };

  const formatDate = (date: Date): string => {
    return new Date(date).toLocaleDateString('pl-PL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (!result) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 text-center">
        <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">
          Brak wyników
        </h3>
        <p className="text-gray-500 mb-6">
          Nie udało się pobrać wyników analizy
        </p>
        <button
          onClick={onReset}
          className="px-6 py-2 btn-secondary rounded-lg font-medium"
        >
          Wróć do początku
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Result Summary */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-water-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-water-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-water-blue-800">
                {result.originalFilename}
              </h3>
              <p className="text-sm text-water-blue-600">
                Analiza zakończona pomyślnie
              </p>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>Data analizy: {formatDate(result.analysisDate)}</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>Czas przetwarzania: {formatDuration(result.processingTime)}</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <motion.button
            onClick={handleDownload}
            disabled={isDownloading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 px-6 py-3 btn-primary rounded-lg font-semibold text-white transition-all duration-300 flex items-center justify-center space-x-2"
          >
            {isDownloading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              >
                <RefreshCw className="w-5 h-5" />
              </motion.div>
            ) : (
              <Download className="w-5 h-5" />
            )}
            <span>
              {isDownloading ? 'Pobieranie...' : 'Pobierz analizę PDF'}
            </span>
          </motion.button>
          
          <motion.button
            onClick={handlePreview}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 px-6 py-3 btn-secondary rounded-lg font-semibold transition-all duration-300 flex items-center justify-center space-x-2"
          >
            <Eye className="w-5 h-5" />
            <span>Podgląd analizy</span>
          </motion.button>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setShowPreview(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-xl max-w-4xl max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">
                Podgląd analizy
              </h3>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[70vh]">
              <div className="prose prose-water-blue max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h1 className="text-2xl font-bold text-water-blue-800 mb-4">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-xl font-semibold text-water-blue-700 mb-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-lg font-medium text-water-blue-600 mb-2">{children}</h3>,
                    p: ({ children }) => <p className="text-gray-700 mb-4 leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-6 mb-4 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="text-gray-700">{children}</li>,
                  }}
                >
                  {previewContent}
                </ReactMarkdown>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-2"
        >
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-700">{error}</p>
        </motion.div>
      )}

      {/* New Analysis Button */}
      <div className="text-center">
        <motion.button
          onClick={onReset}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="px-8 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-all duration-300 flex items-center space-x-2 mx-auto"
        >
          <RefreshCw className="w-5 h-5" />
          <span>Analizuj kolejny plik</span>
        </motion.button>
      </div>
    </div>
  );
};

export default ResultsPanel; 