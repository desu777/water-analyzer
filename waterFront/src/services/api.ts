import { 
  PDFUploadRequest, 
  PDFUploadResponse, 
  AnalysisStatus, 
  AnalysisResult, 
  AnalysisPreview, 
  ApiError, 
  AnalysisWorkflow 
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:2104';

class WaterAnalysisApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
    };

    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log(`🔍 [Water API] Making request to: ${url}`, config);
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log(`✅ [Water API] Response received:`, data);
      }
      
      return data;
    } catch (error) {
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.error(`❌ [Water API] Request failed:`, error);
      }
      
      const apiError: ApiError = {
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        status: error instanceof Error && 'status' in error ? (error as any).status : undefined
      };
      
      throw apiError;
    }
  }

  async uploadPDF(file: File, userId?: string): Promise<PDFUploadResponse> {
    const formData = new FormData();
    formData.append('pdf', file);
    if (userId) {
      formData.append('userId', userId);
    }

    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log('📤 [Water API] Uploading PDF:', file.name, 'Size:', file.size);
    }

    return this.request<PDFUploadResponse>('/api/upload-pdf', {
      method: 'POST',
      body: formData,
    });
  }

  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
    return this.request<AnalysisStatus>(`/api/status/${analysisId}`, {
      method: 'GET',
    });
  }

  async getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
    return this.request<AnalysisResult>(`/api/result/${analysisId}`, {
      method: 'GET',
    });
  }

  async getAnalysisPreview(analysisId: string): Promise<AnalysisPreview> {
    return this.request<AnalysisPreview>(`/api/preview/${analysisId}`, {
      method: 'GET',
    });
  }

  async downloadAnalysisPDF(analysisId: string): Promise<Blob> {
    const url = `${API_BASE_URL}/api/download/${analysisId}`;
    
    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log(`📥 [Water API] Downloading PDF for analysis: ${analysisId}`);
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/pdf',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.log(`✅ [Water API] PDF downloaded, size: ${blob.size} bytes`);
      }
      
      return blob;
    } catch (error) {
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.error(`❌ [Water API] PDF download failed:`, error);
      }
      throw error;
    }
  }

  // Stream analysis workflow updates
  async streamAnalysisWorkflow(
    analysisId: string,
    onUpdate: (update: AnalysisWorkflow) => void
  ): Promise<void> {
    const url = `${API_BASE_URL}/api/stream/${analysisId}`;
    
    if (import.meta.env.VITE_TEST_ENV === 'true') {
      console.log('🌊 [Water API] Starting workflow stream for:', analysisId);
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6);
              if (jsonStr.trim()) {
                const update: AnalysisWorkflow = JSON.parse(jsonStr);
                onUpdate(update);
              }
            } catch (error) {
              if (import.meta.env.VITE_TEST_ENV === 'true') {
                console.error('❌ [Water API] Error parsing workflow update:', error);
              }
            }
          }
        }
      }
    } catch (error) {
      if (import.meta.env.VITE_TEST_ENV === 'true') {
        console.error(`❌ [Water API] Workflow stream failed:`, error);
      }
      throw error;
    }
  }

  async healthCheck(): Promise<{status: string; version: string; timestamp: number}> {
    return this.request<{status: string; version: string; timestamp: number}>('/api/health', {
      method: 'GET',
    });
  }
}

export const waterAnalysisApi = new WaterAnalysisApiService();
export default waterAnalysisApi; 