"""
Gemini API client implementation.
Demonstrates enterprise AI capabilities and advanced model features.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
import google.generativeai as genai
from config.auth import auth
from config.settings import settings
import os
from gemini.configure import configure_gemini
configure_gemini()

class GeminiClient:
    """
    Gemini API client for enterprise AI capabilities.
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.vertex_ai_model_name
        self.logger = logging.getLogger("gemini_client")
        # self.vertex_ai = auth.get_vertex_ai_client()  # Not needed for Gemini
        # Initialize the model using google-generativeai
        self.model = genai.GenerativeModel(self.model_name)
        
        # Model configuration
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        self.logger.info(f"Gemini client initialized with model: {self.model_name}")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini model."""
        try:
            # Update generation config with any provided parameters
            config = self.generation_config.copy()
            config.update(kwargs)
            
            response = self.model.generate_content(
                prompt,
                generation_config=config
            )
            
            self.logger.info(f"Generated text for prompt: {prompt[:50]}...")
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error generating text: {e}")
            raise
    
    async def generate_with_safety(self, prompt: str, safety_settings: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate text with safety filters."""
        try:
            # Default safety settings
            if safety_settings is None:
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=self.generation_config
            )
            
            result = {
                "text": response.text,
                "safety_ratings": getattr(response, 'safety_ratings', None),
                "prompt_feedback": getattr(response, 'prompt_feedback', None)
            }
            
            self.logger.info(f"Generated text with safety filters for prompt: {prompt[:50]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating text with safety: {e}")
            raise
    
    async def chat_conversation(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Have a conversation with the model."""
        try:
            # Create chat session
            chat = self.model.start_chat()
            
            # Send messages
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if role == "user":
                    response = chat.send_message(content)
                elif role == "assistant":
                    # For assistant messages, we might want to continue the conversation
                    # This is a simplified approach
                    pass
            
            # Get the final response
            final_response = chat.last.text
            
            self.logger.info(f"Chat conversation completed with {len(messages)} messages")
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error in chat conversation: {e}")
            raise
    
    async def analyze_content(self, content: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze content using Gemini."""
        try:
            analysis_prompts = {
                "sentiment": "Analyze the sentiment of this text and provide a score from -1 (very negative) to 1 (very positive):",
                "tone": "Analyze the tone of this text and describe it in detail:",
                "key_topics": "Extract the key topics and themes from this text:",
                "summary": "Provide a concise summary of this text:",
                "general": "Provide a general analysis of this text including key points, tone, and structure:"
            }
            
            prompt = f"{analysis_prompts.get(analysis_type, analysis_prompts['general'])}\n\n{content}"
            
            response = await self.generate_text(prompt)
            
            result = {
                "analysis_type": analysis_type,
                "content": content,
                "analysis": response,
                "model_used": self.model_name
            }
            
            self.logger.info(f"Content analysis completed for type: {analysis_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {e}")
            raise
    
    async def code_generation(self, description: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """Generate code based on description."""
        try:
            prompt = f"""
            Generate {language} code based on the following description:
            
            {description}
            
            Please provide:
            1. Complete, runnable code
            2. Comments explaining the logic
            3. Any necessary imports
            4. Example usage if applicable
            
            Code:
            """
            
            response = await self.generate_text(prompt, **kwargs)
            
            result = {
                "language": language,
                "description": description,
                "code": response,
                "model_used": self.model_name
            }
            
            self.logger.info(f"Code generation completed for {language}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating code: {e}")
            raise
    
    async def code_review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Review and improve code."""
        try:
            prompt = f"""
            Review this {language} code and provide:
            1. Code quality assessment
            2. Potential improvements
            3. Security considerations
            4. Performance optimizations
            5. Best practices suggestions
            
            Code to review:
            {code}
            """
            
            response = await self.generate_text(prompt)
            
            result = {
                "language": language,
                "original_code": code,
                "review": response,
                "model_used": self.model_name
            }
            
            self.logger.info(f"Code review completed for {language}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error reviewing code: {e}")
            raise
    
    async def document_analysis(self, document_content: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze documents using Gemini."""
        try:
            analysis_prompts = {
                "comprehensive": "Provide a comprehensive analysis of this document including structure, key points, and insights:",
                "summary": "Create a detailed summary of this document:",
                "qa": "Generate potential questions and answers based on this document:",
                "extraction": "Extract key information, facts, and data points from this document:"
            }
            
            prompt = f"{analysis_prompts.get(analysis_type, analysis_prompts['comprehensive'])}\n\n{document_content}"
            
            response = await self.generate_text(prompt)
            
            result = {
                "analysis_type": analysis_type,
                "document_length": len(document_content),
                "analysis": response,
                "model_used": self.model_name
            }
            
            self.logger.info(f"Document analysis completed for type: {analysis_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing document: {e}")
            raise
    
    async def creative_writing(self, prompt: str, style: str = "professional", **kwargs) -> Dict[str, Any]:
        """Generate creative content."""
        try:
            style_prompts = {
                "professional": "Write in a professional, business-like tone:",
                "creative": "Write in a creative, engaging style:",
                "technical": "Write in a technical, detailed manner:",
                "casual": "Write in a casual, conversational tone:",
                "formal": "Write in a formal, academic style:"
            }
            
            full_prompt = f"{style_prompts.get(style, style_prompts['professional'])}\n\n{prompt}"
            
            response = await self.generate_text(full_prompt, **kwargs)
            
            result = {
                "style": style,
                "original_prompt": prompt,
                "content": response,
                "model_used": self.model_name
            }
            
            self.logger.info(f"Creative writing completed in {style} style")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in creative writing: {e}")
            raise
    
    def update_generation_config(self, **kwargs) -> None:
        """Update the generation configuration."""
        self.generation_config.update(kwargs)
        self.logger.info(f"Generation config updated: {kwargs}")
    
    async def health_check(self) -> bool:
        """Perform a health check on the Gemini client."""
        try:
            test_response = await self.generate_text("Hello, this is a health check.")
            return "error" not in test_response.lower()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False


# Example usage
async def main():
    """Example usage of GeminiClient."""
    client = GeminiClient()
    
    # Test basic text generation
    response = await client.generate_text("Explain machine learning in simple terms.")
    print(f"Generated text: {response}")
    
    # Test content analysis
    analysis = await client.analyze_content(
        "I love this product! It's amazing and works perfectly.",
        analysis_type="sentiment"
    )
    print(f"Sentiment analysis: {analysis}")
    
    # Test code generation
    code_result = await client.code_generation(
        "Create a function to calculate fibonacci numbers",
        language="python"
    )
    print(f"Generated code: {code_result['code']}")
    
    # Test creative writing
    creative_result = await client.creative_writing(
        "Write a short story about a robot learning to paint",
        style="creative"
    )
    print(f"Creative content: {creative_result['content']}")


if __name__ == "__main__":
    asyncio.run(main()) 