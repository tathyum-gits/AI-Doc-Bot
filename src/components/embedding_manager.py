import faiss
import numpy as np
from typing import List, Dict, Optional, Tuple
import openai
from dataclasses import dataclass
import pickle
import os
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from src.components.pdf_processor import DocumentChunk
import streamlit as st

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    chunk: DocumentChunk
    similarity_score: float

class EmbeddingManager:
    def __init__(self, dimension: int = 3072):
        """Initialize the embedding manager with FAISS index."""
        self.dimension = dimension
        
        # Initialize or get from session state
        if 'faiss_index' not in st.session_state:
            st.session_state.faiss_index = faiss.IndexFlatL2(dimension)
            st.session_state.document_chunks = []  # Initialize as list
            st.session_state.embeddings = []
        elif isinstance(st.session_state.document_chunks, dict):  # Convert dict to list if needed
            st.session_state.document_chunks = []
            st.session_state.embeddings = []
            st.session_state.faiss_index = faiss.IndexFlatL2(dimension)
        
        self.index = st.session_state.faiss_index
        self.document_chunks = st.session_state.document_chunks
        self._embeddings = st.session_state.embeddings
        
        # Initialize OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        openai.api_key = openai_api_key
        
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using OpenAI's API."""
        try:
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-3-large"
            )
            embedding_data = response.data[0].embedding
            # Ensure the embedding is the correct shape
            embedding = np.array(embedding_data, dtype=np.float32)
            if embedding.shape[0] != self.dimension:
                raise ValueError(f"Embedding dimension mismatch. Expected {self.dimension}, got {embedding.shape[0]}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            # Return zero vector instead of random for consistency
            return np.zeros(self.dimension, dtype=np.float32)

    async def add_documents(self, documents: List[DocumentChunk]) -> None:
        """Add documents to the vector store."""
        if not documents:
            return

        try:
            # Ensure document_chunks is a list
            if not isinstance(self.document_chunks, list):
                self.document_chunks = []
                st.session_state.document_chunks = []

            # Generate embeddings for all chunks
            embeddings = []
            for chunk in documents:
                embedding = self.generate_embedding(chunk.text)
                embeddings.append(embedding)
                self._embeddings.append(embedding)
                self.document_chunks.append(chunk)

            # Convert to numpy array with correct shape and type
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Add to FAISS index
            self.index.add(embeddings_array)
            
            # Update session state
            st.session_state.document_chunks = self.document_chunks
            st.session_state.embeddings = self._embeddings
            st.session_state.faiss_index = self.index
            
            logger.info(f"Successfully added {len(documents)} chunks to index")
            logger.info(f"Total chunks in index: {len(self.document_chunks)}")
            logger.info(f"FAISS index size: {self.index.ntotal}")
            
        except Exception as e:
            logger.error(f"Error adding documents to index: {str(e)}")
            raise

    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search for relevant document chunks based on query."""
        logger.info(f"Searching for query: {query}")
        logger.info(f"Number of chunks in index: {len(self.document_chunks)}")
        logger.info(f"FAISS index size: {self.index.ntotal}")

        # Check if we have any chunks
        if not self.document_chunks:
            logger.warning("No documents in index")
            return []

        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            query_embedding = np.array([query_embedding], dtype=np.float32)

            # Perform search
            k = min(top_k, len(self.document_chunks))
            if k == 0:
                return []
                
            distances, indices = self.index.search(query_embedding, k)
            
            # Convert to SearchResult objects
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx != -1 and idx < len(self.document_chunks):  # Added bounds check
                    results.append(SearchResult(
                        chunk=self.document_chunks[idx],
                        similarity_score=1.0 / (1.0 + distance)
                    ))
            
            logger.info(f"Found {len(results)} relevant chunks")
            for result in results:
                logger.info(f"Chunk text: {result.chunk.text[:100]}...")  # Log first 100 chars
                logger.info(f"Similarity score: {result.similarity_score}")
                
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            return []

    def remove_document(self, document_id: str) -> None:
        """Remove a document and its embeddings."""
        if not self.document_chunks:
            return

        try:
            # Find indices of chunks to remove
            indices_to_remove = [
                i for i, chunk in enumerate(self.document_chunks)
                if chunk.document_id == document_id
            ]

            if not indices_to_remove:
                return

            # Create new index without removed documents
            new_index = faiss.IndexFlatL2(self.dimension)
            keep_indices = [i for i in range(len(self.document_chunks)) if i not in indices_to_remove]
            
            if keep_indices:
                # Get embeddings for documents to keep
                kept_embeddings = []
                for i in keep_indices:
                    embedding = self.index.reconstruct(i)
                    kept_embeddings.append(embedding)
                
                # Add kept embeddings to new index
                if kept_embeddings:
                    embeddings_array = np.array(kept_embeddings, dtype=np.float32)
                    new_index.add(embeddings_array)

            # Update index and chunks
            self.index = new_index
            self.document_chunks = [
                chunk for i, chunk in enumerate(self.document_chunks)
                if i not in indices_to_remove
            ]
            
            logger.info(f"Successfully removed document {document_id}")
            
        except Exception as e:
            logger.error(f"Error removing document: {str(e)}")
            raise

    def get_total_documents(self) -> int:
        """Get the total number of document chunks in the index."""
        return len(self.document_chunks)  # Return actual length of stored chunks