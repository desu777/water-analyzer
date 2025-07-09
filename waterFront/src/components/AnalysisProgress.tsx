import { motion } from 'framer-motion';
import { AnalysisWorkflow } from '../types';
import { 
  Upload, 
  FileText, 
  Brain, 
  FileOutput, 
  CheckCircle2, 
  AlertCircle,
  Clock
} from 'lucide-react';

interface AnalysisProgressProps {
  workflow: AnalysisWorkflow | null;
  filename: string;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({ workflow, filename }) => {
  const steps = [
    {
      key: 'upload',
      label: 'Przesyłanie pliku',
      icon: Upload,
      description: 'Wysyłanie pliku na serwer'
    },
    {
      key: 'parsing',
      label: 'Analiza treści',
      icon: FileText,
      description: 'Odczytywanie danych z PDF'
    },
    {
      key: 'analysis',
      label: 'Analiza AI',
      icon: Brain,
      description: 'Analiza wyników badań'
    },
    {
      key: 'generation',
      label: 'Generowanie raportu',
      icon: FileOutput,
      description: 'Tworzenie końcowego raportu'
    },
    {
      key: 'complete',
      label: 'Zakończone',
      icon: CheckCircle2,
      description: 'Analiza gotowa do pobrania'
    }
  ];

  const getStepStatus = (stepKey: string) => {
    if (!workflow) return 'pending';
    
    const stepIndex = steps.findIndex(s => s.key === stepKey);
    const currentStepIndex = steps.findIndex(s => s.key === workflow.step);
    
    if (stepIndex < currentStepIndex) return 'completed';
    if (stepIndex === currentStepIndex) {
      return workflow.status === 'error' ? 'error' : 'processing';
    }
    return 'pending';
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8">
      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto mb-4 water-droplet">
          <div className="water-wave" />
        </div>
        <h2 className="text-2xl font-bold text-water-blue-800 mb-2">
          Analizuję wyniki badań
        </h2>
        <p className="text-water-blue-600 mb-4">
          {filename}
        </p>
        
        {workflow && (
          <div className="flex items-center justify-center space-x-2 text-sm text-water-blue-500">
            <Clock className="w-4 h-4" />
            <span>Czas: {formatTime(workflow.elapsedTime)}</span>
          </div>
        )}
      </div>

      <div className="space-y-6">
        {steps.map((step, index) => {
          const status = getStepStatus(step.key);
          const isActive = workflow?.step === step.key;
          const Icon = step.icon;
          
          return (
            <motion.div
              key={step.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`
                flex items-center space-x-4 p-4 rounded-lg transition-all duration-300
                ${status === 'completed' ? 'bg-green-50 border-green-200' : 
                  status === 'processing' ? 'bg-water-blue-50 border-water-blue-200' : 
                  status === 'error' ? 'bg-red-50 border-red-200' : 
                  'bg-gray-50 border-gray-200'}
                border
              `}
            >
              <div className={`
                w-12 h-12 rounded-full flex items-center justify-center
                ${status === 'completed' ? 'bg-green-500' : 
                  status === 'processing' ? 'bg-water-blue-500' : 
                  status === 'error' ? 'bg-red-500' : 
                  'bg-gray-300'}
              `}>
                {status === 'processing' ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </motion.div>
                ) : status === 'error' ? (
                  <AlertCircle className="w-6 h-6 text-white" />
                ) : (
                  <Icon className="w-6 h-6 text-white" />
                )}
              </div>
              
              <div className="flex-1">
                <h3 className={`
                  font-semibold
                  ${status === 'completed' ? 'text-green-800' : 
                    status === 'processing' ? 'text-water-blue-800' : 
                    status === 'error' ? 'text-red-800' : 
                    'text-gray-600'}
                `}>
                  {step.label}
                </h3>
                <p className={`
                  text-sm
                  ${status === 'completed' ? 'text-green-600' : 
                    status === 'processing' ? 'text-water-blue-600' : 
                    status === 'error' ? 'text-red-600' : 
                    'text-gray-500'}
                `}>
                  {isActive && workflow?.message ? workflow.message : step.description}
                </p>
              </div>
              
              {status === 'completed' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
                >
                  <CheckCircle2 className="w-4 h-4 text-white" />
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>

      {workflow && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-8"
        >
          <div className="progress-container">
            <motion.div
              className="progress-bar"
              initial={{ width: 0 }}
              animate={{ width: `${workflow.progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-sm text-water-blue-600">
              Postęp: {Math.round(workflow.progress)}%
            </span>
            <span className="text-sm text-water-blue-500">
              {workflow.message}
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AnalysisProgress; 