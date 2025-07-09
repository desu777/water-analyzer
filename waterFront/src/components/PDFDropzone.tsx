import { useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';

interface PDFDropzoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
}

const PDFDropzone: React.FC<PDFDropzoneProps> = ({ onFileSelect, selectedFile }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.type !== 'application/pdf') {
      return 'Tylko pliki PDF są dozwolone';
    }
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return 'Plik jest zbyt duży. Maksymalny rozmiar: 10MB';
    }
    
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const validationError = validateFile(file);
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setError('');
    onFileSelect(file);
    
    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log('📄 [PDFDropzone] File validated and selected:', file.name);
    }
  }, [onFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleRemoveFile = useCallback(() => {
    setError('');
    onFileSelect(null as any);
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onFileSelect]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileInputChange}
        className="hidden"
      />
      
      {!selectedFile ? (
        <motion.div
          onClick={handleClick}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            pdf-drop-zone w-full h-64 rounded-xl cursor-pointer
            flex flex-col items-center justify-center
            ${isDragOver ? 'drag-over' : ''}
          `}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <motion.div
            animate={{ y: isDragOver ? -5 : 0 }}
            transition={{ duration: 0.2 }}
            className="text-center"
          >
            <Upload className="w-16 h-16 text-water-blue-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-water-blue-700 mb-2">
              {isDragOver ? 'Upuść plik tutaj' : 'Wrzuć plik PDF'}
            </h3>
            <p className="text-water-blue-500 mb-4">
              lub kliknij aby wybrać plik
            </p>
            <p className="text-sm text-water-blue-400">
              Maksymalny rozmiar: 10MB
            </p>
          </motion.div>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border-2 border-water-blue-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-water-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-water-blue-600" />
              </div>
              <div>
                <h4 className="font-semibold text-water-blue-800">
                  {selectedFile.name}
                </h4>
                <p className="text-sm text-water-blue-500">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            
            <button
              onClick={handleRemoveFile}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </motion.div>
      )}
      
      {error && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2"
        >
          <AlertCircle className="w-5 h-5 text-red-500" />
          <p className="text-red-700 text-sm">{error}</p>
        </motion.div>
      )}
    </div>
  );
};

export default PDFDropzone; 