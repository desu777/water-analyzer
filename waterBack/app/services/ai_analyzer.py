import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

from app.config import OpenRouterConfig, settings
from app.models.water_data import WaterTestData, AnalysisContext
from app.utils.logger import log_debug, log_error, log_info, log_warning

class WaterAnalysisAI:
    """AI service for water quality analysis using LangChain + OpenRouter"""
    
    def __init__(self, model_type: str = None):
        self.config = OpenRouterConfig.get_model_config(model_type)
        self.llm = self._create_llm()
        self.prompts_dir = Path("prompts")
        self.master_prompt_template = self._load_master_prompt()
        
        # Ensure prompts directory exists
        if not self.prompts_dir.exists():
            log_warning("Prompts directory not found, creating it", "AI_ANALYZER")
            self.prompts_dir.mkdir(exist_ok=True)
    
    def _create_llm(self) -> ChatOpenAI:
        """Create LangChain ChatOpenAI instance with OpenRouter"""
        try:
            llm = ChatOpenAI(**self.config)
            if settings.DEBUG_MODE:
                log_debug(f"Created LLM with model: {self.config['model_name']}", "AI_ANALYZER")
            return llm
        except Exception as e:
            log_error(f"Failed to create LLM: {str(e)}", "AI_ANALYZER")
            raise
    
    def switch_model(self, model_type: str):
        """Switch to different model dynamically"""
        try:
            old_model = self.config['model_name']
            self.config = OpenRouterConfig.get_model_config(model_type)
            self.llm = self._create_llm()
            log_info(f"Switched model from {old_model} to {self.config['model_name']}", "AI_ANALYZER")
        except Exception as e:
            log_error(f"Failed to switch model: {str(e)}", "AI_ANALYZER")
            raise
    
    def _load_master_prompt(self) -> str:
        """Load the master analysis prompt from file"""
        try:
            prompt_path = self.prompts_dir / "water_analysis_master.txt"
            if not prompt_path.exists():
                log_error("CRITICAL: Master prompt 'water_analysis_master.txt' not found!", "AI_ANALYZER")
                return self._get_default_prompt()
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            log_debug("Loaded master analysis prompt", "AI_ANALYZER")
            return prompt
            
        except Exception as e:
            log_error(f"Failed to load master prompt: {str(e)}", "AI_ANALYZER")
            return self._get_default_prompt()

    async def analyze_water_data(self, context: AnalysisContext) -> str:
        """
        Analyze water test data using AI with the master prompt.
        This is the primary method for generating the personalized report part.
        """
        try:
            log_info(f"Starting AI analysis for {context.analysisId} using master prompt", "AI_ANALYZER")
            
            # Prepare data for analysis
            data_summary = self._prepare_data_summary(context)
            
            # Create messages from the master prompt
            system_message_content = self.master_prompt_template.format(data_summary=data_summary)
            
            # In new LangChain versions, it's better to use a single HumanMessage 
            # or a structured prompt rather than System + Human for this kind of task.
            # We'll put the whole template into a HumanMessage for the model to process.
            messages = [
                HumanMessage(content=system_message_content)
            ]
            
            # Call LLM
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            log_info(f"AI analysis completed for {context.analysisId}", "AI_ANALYZER")
            return result
            
        except Exception as e:
            log_error(f"AI analysis failed: {str(e)}", "AI_ANALYZER")
            
            # Try fallback model
            fallback_model = OpenRouterConfig.FALLBACK_MODEL
            if self.config.get('model_name') != OpenRouterConfig.get_model_name(fallback_model):
                try:
                    log_info(f"Trying fallback model: {fallback_model}", "AI_ANALYZER")
                    self.switch_model(fallback_model)
                    return await self.analyze_water_data(context)
                except Exception as fallback_error:
                    log_error(f"Fallback model also failed: {str(fallback_error)}", "AI_ANALYZER")
            
            return self._generate_error_response(str(e))
    
    def _prepare_data_summary(self, context: AnalysisContext) -> str:
        """Prepare data summary for AI analysis"""
        summary_parts = []
        
        summary_parts.append(f"**Plik Oryginalny:** `{context.originalFilename}`")
        summary_parts.append(f"**ID Analizy:** `{context.analysisId}`")
        
        if context.waterData:
            water_data = context.waterData
            if water_data.testDate:
                summary_parts.append(f"**Data Badania (z dokumentu):** {water_data.testDate}")
            if water_data.laboratory:
                summary_parts.append(f"**Laboratorium:** {water_data.laboratory}")
            if water_data.sampleLocation:
                summary_parts.append(f"**Miejsce Poboru Próbki:** {water_data.sampleLocation}")
            
            if water_data.parameters:
                summary_parts.append("\n**Wyniki Parametrów:**")
                # Create a formatted table for better readability by the AI
                param_table = "| Parametr | Wynik | Jednostka |\n|---|---|---|\n"
                for param in water_data.parameters:
                    value = str(param.value).replace('\n', ' ').strip()
                    unit = param.unit.replace('\n', ' ').strip() if param.unit else " "
                    name = param.name.replace('\n', ' ').strip()
                    param_table += f"| {name} | {value} | {unit} |\n"
                summary_parts.append(param_table)

        summary_parts.append(f"\n**Pełna Treść Wyodrębniona z Dokumentu PDF:**\n---\n{context.extractedText}\n---")
        
        return "\n".join(summary_parts)
    
    def _generate_error_response(self, error_message: str) -> str:
        """Generate a user-friendly error message in Markdown format."""
        log_error(f"Generating error response for user: {error_message}", "AI_ANALYZER")
        return f"""
# Błąd Analizy

## Niestety, napotkaliśmy problem

Podczas przetwarzania Twojej analizy wystąpił nieoczekiwany błąd. Nasz zespół techniczny został o tym automatycznie poinformowany.

**Szczegóły błędu:**
`{error_message}`

Prosimy spróbować ponownie za chwilę. Jeśli problem będzie się powtarzał, skontaktuj się z naszym wsparciem.

Przepraszamy za niedogodności.
"""

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the currently used model."""
        return {
            "model_name": self.config.get('model_name'),
            "temperature": self.config.get('temperature'),
            "max_tokens": self.config.get('max_tokens')
        }
    
    def _get_default_prompt(self) -> str:
        """Provides a fallback prompt if the main file is missing."""
        return """
Jako ekspert ds. analizy wody, przeanalizuj poniższe dane i stwórz zwięzły raport w formacie Markdown.

Dane do analizy:
{data_summary}
"""

# Global AI analyzer instance
ai_analyzer = WaterAnalysisAI() 