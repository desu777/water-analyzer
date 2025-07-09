export interface PDFUploadRequest {
  file: File;
  userId?: string;
}

export interface PDFUploadResponse {
  success: boolean;
  analysisId: string;
  message: string;
  error?: string;
}

export interface AnalysisStatus {
  id: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  startTime: Date;
  completedTime?: Date;
  error?: string;
}

export interface AnalysisResult {
  id: string;
  originalFilename: string;
  analysisMarkdown: string;
  analysisDate: Date;
  processingTime: number;
  pdfUrl?: string;
  previewUrl?: string;
}

export interface AnalysisPreview {
  id: string;
  markdown: string;
  metadata: {
    originalFilename: string;
    analysisDate: string;
    processingTime: number;
  };
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export interface WaterTestData {
  testDate?: string;
  laboratory?: string;
  sampleLocation?: string;
  parameters: WaterParameter[];
  summary?: string;
  recommendations?: string[];
}

export interface WaterParameter {
  name: string;
  value: number | string;
  unit?: string;
  acceptable?: boolean;
  range?: {
    min?: number;
    max?: number;
  };
  description?: string;
}

export interface AnalysisWorkflow {
  step: 'upload' | 'parsing' | 'analysis' | 'generation' | 'complete';
  status: 'processing' | 'completed' | 'error';
  message: string;
  progress: number;
  elapsedTime: number;
} 