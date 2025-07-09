import { motion } from 'framer-motion';
import { Droplets } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-gradient-to-r from-water-blue-600 to-water-blue-700 shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-center"
        >
          <div className="flex items-center space-x-3">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 bg-white rounded-full flex items-center justify-center"
            >
              <Droplets className="w-6 h-6 text-water-blue-600" />
            </motion.div>
            
            <div>
              <h1 className="text-3xl font-bold text-white">
                Water Test Analyzer
              </h1>
              <p className="text-water-blue-100 text-sm">
                AI-powered water quality analysis
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </header>
  );
};

export default Header; 