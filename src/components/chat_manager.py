from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
import openai
from anthropic import Anthropic
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import logging
from src.components.embedding_manager import SearchResult

logger = logging.getLogger(__name__)

LLMProvider = Literal["openai", "anthropic", "gemini"]

@dataclass
class ChatResponse:
    answer: str
    sources: List[Dict[str, str]]
    confidence_score: float
    model_used: str

class ChatManager:
    def __init__(self, config):
        """Initialize chat manager with API configurations."""
        self.config = config
        self._setup_clients()
        
    def _setup_clients(self):
        """Set up API clients for different providers."""
        # OpenAI setup
        if hasattr(self.config, 'api') and self.config.api.openai_api_key:
            openai.api_key = self.config.api.openai_api_key
        else:
            logger.error("OpenAI API key not found in configuration")
            raise ValueError("OpenAI API key is required")
        
        # Anthropic setup
        if hasattr(self.config, 'api') and self.config.api.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=self.config.api.anthropic_api_key)
        else:
            logger.warning("Anthropic API key not found in configuration")
        
        # Google setup
        if hasattr(self.config, 'api') and self.config.api.google_api_key:
            genai.configure(api_key=self.config.api.google_api_key)
        else:
            logger.warning("Google API key not found in configuration")
        
    def _format_context(self, relevant_chunks: List[SearchResult]) -> str:
        """Format retrieved context for the LLM prompt."""
        context_parts = []
        for chunk in relevant_chunks:
            context_parts.append(
                f"[Document: {chunk.chunk.document_id}, "
                f"Page: {chunk.chunk.page_number}]\n{chunk.chunk.text}"
            )
        return "\n\n".join(context_parts)
        
    def _create_prompt(self, query: str, context: str) -> str:
        """Create a prompt for the LLM."""
        return f"""You are a professional AI assistant helping with document-based questions. 
        Your task is to answer the question based on the provided context.

        Context:
        {context}

        Question: {query}

        Please provide a clear, accurate answer based solely on the provided context. 
        Provide the answer in bullet points instead of paragraph(s)
        If the context doesn't contain enough information to answer the question fully, 
        please state that explicitly.

        Answer:"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_openai_response(self, prompt: str) -> str:
        """Get response from OpenAI's GPT model."""
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional AI assistant helping with document-based questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_anthropic_response(self, prompt: str) -> str:
        """Get response from Anthropic's Claude model."""
        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"Anthropic API error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_gemini_response(self, prompt: str) -> str:
        """Get response from Google's Gemini model."""
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")

    async def get_chat_response(
    self,
    query: str,
    relevant_chunks: List[SearchResult],
    provider: LLMProvider = "openai"
) -> ChatResponse:
        """Get response from specified LLM provider."""
        logger.info(f"Getting response using provider: {provider}")
        
        # Format context and create prompt
        context = self._format_context(relevant_chunks)
        logger.info(f"Context length: {len(context)} characters")
        
        prompt = self._create_prompt(query, context)
        logger.info("Created prompt")
        
        try:
            # Get response from specified provider
            if provider == "openai":
                logger.info("Requesting response from OpenAI")
                response_text = self.get_openai_response(prompt)
                logger.info("Got response from OpenAI")
            elif provider == "anthropic":
                response_text = self.get_anthropic_response(prompt)
            elif provider == "gemini":
                response_text = self.get_gemini_response(prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
            # Calculate confidence score based on chunk relevance
            confidence_score = max((chunk.similarity_score for chunk in relevant_chunks), default=0.0)
            
            # Format sources
            sources = [
                {
                    "document_id": chunk.chunk.document_id,
                    "page_number": chunk.chunk.page_number,
                    "similarity_score": chunk.similarity_score
                }
                for chunk in relevant_chunks
            ]
            
            return ChatResponse(
                answer=response_text,
                sources=sources,
                confidence_score=confidence_score,
                model_used=provider
            )
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}", exc_info=True)
            raise
