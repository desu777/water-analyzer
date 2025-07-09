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
    
    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt from file"""
        try:
            prompt_path = self.prompts_dir / prompt_file
            
            if not prompt_path.exists():
                log_warning(f"Prompt file not found: {prompt_file}", "AI_ANALYZER")
                return self._get_default_prompt()
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            
            log_debug(f"Loaded prompt from {prompt_file}", "AI_ANALYZER")
            return prompt
            
        except Exception as e:
            log_error(f"Failed to load prompt {prompt_file}: {str(e)}", "AI_ANALYZER")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default prompt if file is not available"""
        return """
        Jesteś ekspertem w analizie jakości wody. Przeanalizuj poniższe dane badania wody i oceń:
        
        1. Oceń każdy parametr względem polskich norm
        2. Zidentyfikuj potencjalne zagrożenia dla zdrowia
        3. Zaproponuj konkretne działania naprawcze
        4. Podaj zalecenia dotyczące użytkowania wody
        
        Odpowiedz w formacie Markdown z sekcjami:
        - Podsumowanie
        - Analiza parametrów
        - Zagrożenia
        - Rekomendacje
        
        Dane badania:
        """
    
    async def analyze_water_data(self, context: AnalysisContext) -> str:
        """Analyze water test data using AI"""
        try:
            log_info(f"Starting AI analysis for {context.analysisId}", "AI_ANALYZER")
            
            # Load main analysis prompt
            prompt_template = self._load_prompt('water_analysis_main.txt')
            
            # Prepare data for analysis
            data_summary = self._prepare_data_summary(context)
            
            # Create messages
            system_message = SystemMessage(content=prompt_template)
            human_message = HumanMessage(content=data_summary)
            
            # Call LLM
            response = await self.llm.agenerate([[system_message, human_message]])
            result = response.generations[0][0].text
            
            log_info(f"AI analysis completed for {context.analysisId}", "AI_ANALYZER")
            return result
            
        except Exception as e:
            log_error(f"AI analysis failed: {str(e)}", "AI_ANALYZER")
            
            # Try fallback model
            fallback_model = OpenRouterConfig.FALLBACK_MODEL
            if fallback_model != self.config.get('model_name'):
                try:
                    log_info(f"Trying fallback model: {fallback_model}", "AI_ANALYZER")
                    self.switch_model(fallback_model)
                    return await self.analyze_water_data(context)
                except Exception as fallback_error:
                    log_error(f"Fallback model also failed: {str(fallback_error)}", "AI_ANALYZER")
            
            # Return error message
            return self._generate_error_response(str(e))
    
    def _prepare_data_summary(self, context: AnalysisContext) -> str:
        """Prepare data summary for AI analysis"""
        summary_parts = []
        
        # Basic information
        summary_parts.append(f"**Plik:** {context.originalFilename}")
        summary_parts.append(f"**ID Analizy:** {context.analysisId}")
        
        # Water data if available
        if context.waterData:
            water_data = context.waterData
            
            if water_data.testDate:
                summary_parts.append(f"**Data badania:** {water_data.testDate}")
            
            if water_data.laboratory:
                summary_parts.append(f"**Laboratorium:** {water_data.laboratory}")
            
            if water_data.sampleLocation:
                summary_parts.append(f"**Lokalizacja próbki:** {water_data.sampleLocation}")
            
            # Parameters
            if water_data.parameters:
                summary_parts.append("\n**Parametry badania:**")
                for param in water_data.parameters:
                    param_line = f"- {param.name}: {param.value}"
                    if param.unit:
                        param_line += f" {param.unit}"
                    summary_parts.append(param_line)
        
        # Raw extracted text
        summary_parts.append(f"\n**Pełna treść dokumentu:**\n{context.extractedText}")
        
        return "\n".join(summary_parts)
    
    async def evaluate_parameters(self, water_data: WaterTestData) -> str:
        """Evaluate individual water parameters"""
        try:
            log_info("Evaluating water parameters", "AI_ANALYZER")
            
            prompt_template = self._load_prompt('water_parameters_eval.txt')
            
            # Prepare parameters data
            params_data = self._format_parameters_for_evaluation(water_data.parameters)
            
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=params_data)
            ]
            
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            log_info("Parameter evaluation completed", "AI_ANALYZER")
            return result
            
        except Exception as e:
            log_error(f"Parameter evaluation failed: {str(e)}", "AI_ANALYZER")
            return f"Błąd podczas oceny parametrów: {str(e)}"
    
    def _format_parameters_for_evaluation(self, parameters) -> str:
        """Format parameters for evaluation"""
        if not parameters:
            return "Brak danych o parametrach do oceny."
        
        formatted_params = []
        for param in parameters:
            param_str = f"**{param.name}:** {param.value}"
            if param.unit:
                param_str += f" {param.unit}"
            formatted_params.append(param_str)
        
        return "\n".join(formatted_params)
    
    async def generate_recommendations(self, analysis_result: str) -> str:
        """Generate practical recommendations"""
        try:
            log_info("Generating recommendations", "AI_ANALYZER")
            
            prompt_template = self._load_prompt('recommendations.txt')
            
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=f"Na podstawie analizy:\n{analysis_result}")
            ]
            
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            log_info("Recommendations generated", "AI_ANALYZER")
            return result
            
        except Exception as e:
            log_error(f"Recommendations generation failed: {str(e)}", "AI_ANALYZER")
            return f"Błąd podczas generowania rekomendacji: {str(e)}"
    
    async def format_final_report(self, analysis_parts: Dict[str, str]) -> str:
        """Format final report"""
        try:
            log_info("Formatting final report", "AI_ANALYZER")
            
            prompt_template = self._load_prompt('report_formatting.txt')
            
            # Combine all analysis parts
            combined_analysis = ""
            for section, content in analysis_parts.items():
                combined_analysis += f"\n## {section}\n{content}\n"
            
            messages = [
                SystemMessage(content=prompt_template),
                HumanMessage(content=combined_analysis)
            ]
            
            response = await self.llm.agenerate([messages])
            result = response.generations[0][0].text
            
            log_info("Final report formatted", "AI_ANALYZER")
            return result
            
        except Exception as e:
            log_error(f"Report formatting failed: {str(e)}", "AI_ANALYZER")
            return combined_analysis  # Return unformatted if formatting fails
    
    def _generate_error_response(self, error_message: str) -> str:
        """Generate error response in markdown format"""
        return f"""
# Błąd Analizy Wody

## ⚠️ Wystąpił Problem

Nie udało się przeprowadzić automatycznej analizy wyników badania wody.

**Błąd:** {error_message}

## 🔧 Zalecenia

1. **Sprawdź format pliku PDF** - upewnij się, że jest to standardowy raport laboratoryjny
2. **Skonsultuj się z ekspertem** - zalecamy konsultację z specjalistą ds. jakości wody
3. **Spróbuj ponownie** - możesz spróbować przesłać plik ponownie

## 📞 Pomoc

W przypadku ciągłych problemów, skontaktuj się z pomocą techniczną.
"""
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            'model_name': self.config.get('model_name'),
            'temperature': self.config.get('temperature'),
            'max_tokens': self.config.get('max_tokens'),
            'api_base': self.config.get('openai_api_base')
        }

# Global AI analyzer instance
ai_analyzer = WaterAnalysisAI() 