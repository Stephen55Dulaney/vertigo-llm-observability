"""
Base Vertex AI Agent implementation.
Demonstrates core agent capabilities and patterns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from config.auth import auth
from config.settings import settings
import os
from gemini.configure import configure_gemini
configure_gemini()

class BaseAgent:
    """
    Base class for Vertex AI agents.
    Provides common functionality for all agent types.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
        # Use Gemini GenerativeModel
        self.model = genai.GenerativeModel(settings.vertex_ai_model_name)
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Agent capabilities
        self.capabilities = self._define_capabilities()
        
        self.logger.info(f"Agent '{name}' initialized with model: {settings.vertex_ai_model_name}")
    
    def _define_capabilities(self) -> Dict[str, Any]:
        """Define agent capabilities and tools."""
        return {
            "text_generation": True,
            "conversation_memory": True,
            "tool_calling": False,  # Override in subclasses
            "file_processing": False,  # Override in subclasses
            "api_integration": False,  # Override in subclasses
        }
    
    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Main chat method for interacting with the agent.
        
        Args:
            message: User input message
            context: Additional context for the conversation
            
        Returns:
            Agent response
        """
        try:
            # Add message to history
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            
            # Prepare conversation context
            conversation_context = self._prepare_context(context)
            
            # Generate response
            response = await self._generate_response(message, conversation_context)
            
            # Add response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            self.logger.info(f"Generated response for user message: {message[:50]}...")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return f"I encountered an error: {str(e)}"
    
    def _prepare_context(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare conversation context for the model."""
        context_parts = []
        
        # Add agent description
        if self.description:
            context_parts.append(f"Agent Description: {self.description}")
        
        # Add capabilities
        context_parts.append(f"Capabilities: {', '.join(self.capabilities.keys())}")
        
        # Add conversation history (last 5 exchanges)
        if self.conversation_history:
            recent_history = self.conversation_history[-10:]  # Last 5 exchanges
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent_history
            ])
            context_parts.append(f"Recent Conversation:\n{history_text}")
        
        # Add additional context
        if context:
            context_parts.append(f"Additional Context: {context}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_response(self, message: str, context: str) -> str:
        """Generate response using Gemini model."""
        try:
            # Create prompt with context
            prompt = f"""
{context}

Current Message: {message}

Please respond as {self.name}, considering the conversation context and your capabilities.
"""
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        return {
            "agent_name": self.name,
            "total_exchanges": len(self.conversation_history) // 2,
            "capabilities": self.capabilities,
            "model_used": settings.vertex_ai_model_name,
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")
    
    async def health_check(self) -> bool:
        """Perform a health check on the agent."""
        try:
            # Test basic response generation
            test_response = await self.chat("Hello, this is a health check.")
            return "error" not in test_response.lower()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False


# Example usage
async def main():
    """Example usage of the BaseAgent."""
    # Create a simple agent
    agent = BaseAgent(
        name="Assistant",
        description="A helpful AI assistant that can engage in conversation and provide information."
    )
    
    # Test the agent
    response = await agent.chat("Hello! What can you help me with?")
    print(f"Agent: {response}")
    
    # Get conversation summary
    summary = agent.get_conversation_summary()
    print(f"Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(main()) 