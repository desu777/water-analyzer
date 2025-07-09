import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AnalysisStatus, AnalysisResult, AnalysisWorkflow } from '../types';
import waterAnalysisApi from '../services/api';
import Header from './Header';
import PDFDropzone from './PDFDropzone';
import AnalysisProgress from './AnalysisProgress';
import ResultsPanel from './ResultsPanel';
import { FileText, AlertCircle, CheckCircle2 } from 'lucide-react';

type AppState = 'upload' | 'processing' | 'completed' | 'error';

const WaterAnalyzer: React.FC = () => {
  const [appState, setAppState] = useState<AppState>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysisId, setAnalysisId] = useState<string>('');
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [currentWorkflow, setCurrentWorkflow] = useState<AnalysisWorkflow | null>(null);
  const [error, setError] = useState<string>('');

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
    setError('');
    
    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log('📄 [WaterAnalyzer] File selected:', file.name, 'Size:', file.size);
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setAppState('processing');
    setError('');

    try {
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log('🚀 [WaterAnalyzer] Starting upload process...');
      }

      // Upload PDF
      const uploadResponse = await waterAnalysisApi.uploadPDF(selectedFile);
      
      if (!uploadResponse.success) {
        throw new Error(uploadResponse.error || 'Upload failed');
      }

      setAnalysisId(uploadResponse.analysisId);

      // Start streaming workflow updates
      waterAnalysisApi.streamAnalysisWorkflow(
        uploadResponse.analysisId,
        (update: AnalysisWorkflow) => {
          setCurrentWorkflow(update);
          
          if (import.meta.env.VITE_TEST_ENV === 'true') {
            console.log('🔄 [WaterAnalyzer] Workflow update:', update);
          }

          // Check if analysis is complete
          if (update.step === 'complete' && update.status === 'completed') {
            handleAnalysisComplete(uploadResponse.analysisId);
          } else if (update.status === 'error') {
            setError(update.message || 'Analysis failed');
            setAppState('error');
          }
        }
      );

    } catch (error) {
      console.error('❌ [WaterAnalyzer] Upload failed:', error);
      setError(error instanceof Error ? error.message : 'Upload failed');
      setAppState('error');
    }
  }, [selectedFile]);

  const handleAnalysisComplete = useCallback(async (id: string) => {
    try {
      const result = await waterAnalysisApi.getAnalysisResult(id);
      setAnalysisResult(result);
      setAppState('completed');
      
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log('✅ [WaterAnalyzer] Analysis completed:', result);
      }
    } catch (error) {
      console.error('❌ [WaterAnalyzer] Failed to get analysis result:', error);
      setError('Failed to retrieve analysis result');
      setAppState('error');
    }
  }, []);

  const handleReset = useCallback(() => {
    setAppState('upload');
    setSelectedFile(null);
    setAnalysisId('');
    setAnalysisStatus(null);
    setAnalysisResult(null);
    setCurrentWorkflow(null);
    setError('');
    
    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log('🔄 [WaterAnalyzer] Reset to initial state');
    }
  }, []);

  const renderContent = () => {
    switch (appState) {
      case 'upload':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-2xl mx-auto"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 mx-auto mb-4 water-droplet">
                <div className="water-wave">
                  <FileText className="w-8 h-8 text-white absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-water-blue-800 mb-2">
                Analiza Badań Wody
              </h2>
              <p className="text-water-blue-600">
                Wrzuć plik PDF z wynikami badań wody, aby otrzymać kompleksową analizę
              </p>
            </div>

            <PDFDropzone 
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
            />

            {selectedFile && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-6 text-center"
              >
                <button
                  onClick={handleUpload}
                  className="px-8 py-3 btn-primary rounded-lg font-semibold text-white transition-all duration-300 hover:shadow-lg"
                >
                  Analizuj Badania
                </button>
              </motion.div>
            )}
          </motion.div>
        );

      case 'processing':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-2xl mx-auto"
          >
            <AnalysisProgress
              workflow={currentWorkflow}
              filename={selectedFile?.name || 'Unknown file'}
            />
          </motion.div>
        );

      case 'completed':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-4xl mx-auto"
          >
            <div className="text-center mb-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-water-blue-800 mb-2">
                Analiza Zakończona
              </h2>
              <p className="text-water-blue-600">
                Twoja analiza badań wody jest gotowa
              </p>
            </div>

            <ResultsPanel
              result={analysisResult}
              analysisId={analysisId}
              onReset={handleReset}
            />
          </motion.div>
        );

      case 'error':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-2xl mx-auto text-center"
          >
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-red-800 mb-2">
              Wystąpił błąd
            </h2>
            <p className="text-red-600 mb-6">
              {error || 'Nieznany błąd podczas analizy'}
            </p>
            <button
              onClick={handleReset}
              className="px-8 py-3 btn-secondary rounded-lg font-semibold transition-all duration-300"
            >
              Spróbuj ponownie
            </button>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-water-blue-50 to-water-blue-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {renderContent()}
        </AnimatePresence>
      </main>
    </div>
  );
};

export default WaterAnalyzer; 