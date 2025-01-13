import streamlit as st
import time
import os
import logging
from pathlib import Path
import asyncio
from typing import Dict, List
from src.config import config
from src.components.pdf_processor import PDFProcessor
from src.components.embedding_manager import EmbeddingManager
from src.components.chat_manager import ChatManager
from src.utils.security import SecurityManager, SessionManager, SecureFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="AI DocBot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DocumentChatApplication:
    """Main Streamlit application class for document chat interface."""
    
    def __init__(self):
        """Initialize the application and its components."""
        # Initialize session state first
        self._initialize_session_state()
        
        # Initialize managers and handlers
        self.security_manager = SecurityManager(config.security.encryption_key)
        self.session_manager = SessionManager(
            expiry_time=config.security.session_expiry,
            temp_dir="temp"
        )
        self.session_manager.create_session(st.session_state.session_id)
        self.file_handler = SecureFileHandler(
            security_manager=self.security_manager,
            allowed_extensions=['.pdf'],
            max_file_size=100 * 1024 * 1024  # 100MB
        )
        
        # Initialize processing components
        self.pdf_processor = PDFProcessor()
        self.embedding_manager = EmbeddingManager()
        self.chat_manager = ChatManager(config)
        
    def _initialize_session_state(self):
        """Initialize or restore session state."""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.chat_history = []
            st.session_state.uploaded_files = {}  # filename -> document_id mapping
            st.session_state.session_id = str(int(time.time()))  # Simple timestamp-based session ID
            st.session_state.selected_model = "openai"
            st.session_state.processing_question = False
            st.session_state.current_question = None
        
    def render_sidebar(self):
        """Render sidebar with file upload and settings."""
        with st.sidebar:
            # Model selection
            st.subheader("Model Settings")
            model_options = {
                "openai": "OpenAI GPT-4",
                "anthropic": "Anthropic Claude",
                "gemini": "Google Gemini"
            }
            
            selected_model = st.selectbox(
                "Select AI Model",
                options=list(model_options.keys()),
                format_func=lambda x: model_options[x],
                key="model_selector"
            )
            st.session_state.selected_model = selected_model
            
            # File upload section
            st.subheader("Upload Documents")
            uploaded_files = st.file_uploader(
                "Upload PDF Documents",
                type=['pdf'],
                accept_multiple_files=True,
                key="pdf_uploader",
                help="Upload one or more PDF documents to chat with"
            )
            
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    self._handle_file_upload(uploaded_file)
            
            # Display uploaded files
            if st.session_state.uploaded_files:
                st.subheader("Uploaded Documents")
                for filename, doc_id in st.session_state.uploaded_files.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(self._truncate_filename(filename))
                    with col2:
                        if st.button("🗑️", key=f"remove_{doc_id}"):
                            self._remove_document(filename)
                            st.rerun()
            if st.session_state.uploaded_files:
                # Document Statistics
                st.subheader("Document Statistics")
                self._update_document_stats()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Documents", st.session_state.document_stats['total_documents'])
                with col2:
                    st.metric("Total Chunks", st.session_state.document_stats['total_chunks'])
                            
    def _truncate_filename(self, filename: str, max_length: int = 25) -> str:
        """Truncate filename if it's too long."""
        if len(filename) <= max_length:
            return filename
        return filename[:max_length-3] + "..."
        
    def render_chat_interface(self):
        """Render main chat interface."""
        st.title("Document Chat")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        if "sources" in message:
                            with st.expander("View Sources"):
                                for source in message["sources"]:
                                    st.write(f"📄 Document: {source['document_id']}, "
                                        f"Page: {source['page_number']}, "
                                        f"Confidence: {source['similarity_score']:.2f}")
        
        # Chat input
        if st.session_state.uploaded_files:
            user_question = st.chat_input("Ask a question about your documents")
            if user_question:
                if not st.session_state.processing_question:
                    # Add user message to chat history immediately
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_question
                    })
                    st.session_state.processing_question = True
                    st.session_state.current_question = user_question
                    st.rerun()
                
            # Process the question if we have one pending
            if st.session_state.processing_question and st.session_state.current_question:
                try:
                    with st.spinner("Generating response..."):
                        # Get relevant document chunks
                        relevant_chunks = asyncio.run(self.embedding_manager.search(st.session_state.current_question))
                        
                        # Get AI response
                        response = asyncio.run(self.chat_manager.get_chat_response(
                            query=st.session_state.current_question,
                            relevant_chunks=relevant_chunks,
                            provider=st.session_state.selected_model
                        ))
                        
                        # Add response to chat history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response.answer,
                            "sources": response.sources
                        })
                        
                        # Reset processing state
                        st.session_state.processing_question = False
                        st.session_state.current_question = None
                        st.rerun()
                        
                except Exception as e:
                    error_message = f"Error processing question: {str(e)}"
                    logger.error(error_message, exc_info=True)
                    st.error(error_message)
                    st.session_state.processing_question = False
                    st.session_state.current_question = None
        else:
            st.info("Please upload some documents to start chatting!")

    async def _process_user_question(self, question: str):
        """Process user question and generate response."""
        logger.info("=== Starting to handle user question ===")
        logger.info(f"Question: {question}")
        
        try:
            # Add user message to chat history immediately
            st.session_state.chat_history.append({
                "role": "user",
                "content": question
            })
            # Force a rerun to show the user message immediately
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            st.error(error_message)
            return

        try:
            # Get relevant document chunks
            logger.info("Searching for chunks relevant to: " + question)
            relevant_chunks = await self.embedding_manager.search(question)
            logger.info(f"Found {len(relevant_chunks)} relevant chunks")
            
            # Get AI response
            logger.info("Getting AI response...")
            with st.spinner("Generating response..."):
                response = await self.chat_manager.get_response(
                    query=question,
                    relevant_chunks=relevant_chunks,
                    provider=st.session_state.selected_model
                )
                
                # Add response to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.answer,
                    "sources": response.sources
                })
                
        except Exception as e:
            error_message = f"Error processing question: {str(e)}"
            logger.error(error_message, exc_info=True)
            st.error(error_message)
            
    def _handle_file_upload(self, uploaded_file):
        """Process uploaded file and update embeddings."""
        if uploaded_file.name not in st.session_state.uploaded_files:
            try:
                # Read file content
                file_content = uploaded_file.read()
                
                # Process PDF
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    # Process the PDF first
                    processed_doc = self.pdf_processor.process_pdf(
                        file_content,
                        uploaded_file.name
                    )
                    
                    # Add to embeddings
                    asyncio.run(self.embedding_manager.add_documents(processed_doc.chunks))
                    
                    # Update UI state
                    st.session_state.uploaded_files[uploaded_file.name] = {
                        'document_id': processed_doc.document_id,
                        'total_chunks': len(processed_doc.chunks)
                    }
                    
                    st.success(f"Successfully processed {uploaded_file.name}")
                    
            except Exception as e:
                error_message = f"Error processing {uploaded_file.name}: {str(e)}"
                logger.error(error_message, exc_info=True)
                st.error(error_message)
                
    def _remove_document(self, filename: str):
        """Remove document from session and clean up resources."""
        if filename in st.session_state.uploaded_files:
            doc_id = st.session_state.uploaded_files[filename]
            
            # Remove from document chunks
            if filename in st.session_state.document_chunks:
                del st.session_state.document_chunks[filename]
                
            # Remove from uploaded files
            del st.session_state.uploaded_files[filename]
            
            # Remove from embeddings
            self.embedding_manager.remove_document(doc_id)
    def _update_document_stats(self):
        """Update document statistics."""
        if 'document_stats' not in st.session_state:
            st.session_state.document_stats = {
                'total_documents': 0,
                'total_chunks': 0
            }
        
        st.session_state.document_stats = {
            'total_documents': len(st.session_state.uploaded_files),
            'total_chunks': self.embedding_manager.get_total_documents()
        }
    def run(self):
        """Run the Streamlit application."""
        try:
            # Render components
            self.render_sidebar()
            self.render_chat_interface()
            
            # Cleanup expired sessions periodically
            if time.time() % 300 < 1:  # Run every 5 minutes
                self.session_manager.cleanup_expired_sessions()
                
        except Exception as e:
            logger.error("Application error", exc_info=True)
            st.error(f"Application error: {str(e)}")

# Run the application
if __name__ == "__main__":
    app = DocumentChatApplication()
    app.run()