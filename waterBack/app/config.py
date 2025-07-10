import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # App Configuration
    APP_HOST: str = os.getenv('APP_HOST', 'localhost')
    APP_PORT: int = int(os.getenv('APP_PORT', '2104'))
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    MAX_PDF_SIZE_MB: int = int(os.getenv('MAX_PDF_SIZE_MB', '10'))
    
    # Folders
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    TEMP_FOLDER: str = os.getenv('TEMP_FOLDER', 'temp')
    REPORTS_FOLDER: str = os.getenv('REPORTS_FOLDER', 'reports')
    
    # CORS
    CORS_ORIGINS: list = os.getenv('CORS_ORIGINS', 'http://localhost:3001,http://localhost:3000').split(',')
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    
    # Report Cleanup
    REPORT_LIFETIME_MINUTES: int = int(os.getenv('REPORT_LIFETIME_MINUTES', '10'))
    CLEANUP_INTERVAL_MINUTES: int = int(os.getenv('CLEANUP_INTERVAL_MINUTES', '5'))
    POST_DOWNLOAD_CLEANUP_MINUTES: int = int(os.getenv('POST_DOWNLOAD_CLEANUP_MINUTES', '1'))

class OpenRouterConfig:
    # API Configuration
    API_KEY: str = os.getenv('OPENROUTER_API_KEY', '')
    BASE_URL: str = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    
    # Model Names from .env
    MODEL_FAST: str = os.getenv('OPENROUTER_MODEL_FAST', 'openai/gpt-3.5-turbo')
    MODEL_BALANCED: str = os.getenv('OPENROUTER_MODEL_BALANCED', 'anthropic/claude-3-haiku')
    MODEL_ADVANCED: str = os.getenv('OPENROUTER_MODEL_ADVANCED', 'anthropic/claude-3-opus')
    MODEL_PREMIUM: str = os.getenv('OPENROUTER_MODEL_PREMIUM', 'openai/gpt-4-turbo')
    
    # Default Selection
    DEFAULT_MODEL: str = os.getenv('OPENROUTER_DEFAULT_MODEL', 'BALANCED')
    FALLBACK_MODEL: str = os.getenv('OPENROUTER_FALLBACK_MODEL', 'FAST')
    
    # Model Parameters
    TEMPERATURE: float = float(os.getenv('MODEL_TEMPERATURE', '0.1'))
    MAX_TOKENS: int = int(os.getenv('MODEL_MAX_TOKENS', '4000'))
    TOP_P: float = float(os.getenv('MODEL_TOP_P', '1.0'))
    
    @classmethod
    def get_model_name(cls, model_type: str) -> str:
        """Get model name by type"""
        model_map = {
            'FAST': cls.MODEL_FAST,
            'BALANCED': cls.MODEL_BALANCED,
            'ADVANCED': cls.MODEL_ADVANCED,
            'PREMIUM': cls.MODEL_PREMIUM
        }
        return model_map.get(model_type.upper(), cls.MODEL_BALANCED)
    
    @classmethod
    def get_model_config(cls, model_type: str = None) -> Dict[str, Any]:
        """Get complete model configuration"""
        if not model_type:
            model_type = cls.DEFAULT_MODEL
            
        return {
            'model_name': cls.get_model_name(model_type),
            'openai_api_key': cls.API_KEY,
            'openai_api_base': cls.BASE_URL,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'top_p': cls.TOP_P
        }

class LangChainConfig:
    TRACING_V2: bool = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    API_KEY: str = os.getenv('LANGCHAIN_API_KEY', '')
    PROJECT: str = os.getenv('LANGCHAIN_PROJECT', 'water-test-analyzer')

# Initialize settings
settings = Settings()
openrouter_config = OpenRouterConfig()
langchain_config = LangChainConfig()

# Debug logging
if settings.DEBUG_MODE:
    print("🔧 [Config] Settings loaded:")
    print(f"   🌐 Host: {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"   📁 Upload folder: {settings.UPLOAD_FOLDER}")
    print(f"   🤖 Default model: {openrouter_config.get_model_name(openrouter_config.DEFAULT_MODEL)}")
    print(f"   🔄 Fallback model: {openrouter_config.get_model_name(openrouter_config.FALLBACK_MODEL)}")
    print(f"   🗑️ Report cleanup: {settings.REPORT_LIFETIME_MINUTES}min lifetime, {settings.CLEANUP_INTERVAL_MINUTES}min interval") 