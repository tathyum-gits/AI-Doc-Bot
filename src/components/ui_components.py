import streamlit as st
from typing import List, Dict, Optional
import pandas as pd
import time
from dataclasses import dataclass

class DocumentStats:
    """Component for displaying document statistics."""
    
    @staticmethod
    def render(uploaded_files: Dict[str, str], embedding_manager):
        """Render document statistics."""
        if not uploaded_files:
            return
            
        st.sidebar.subheader("Document Statistics")
        
        total_docs = len(uploaded_files)
        total_chunks = embedding_manager.get_total_documents()
        
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Documents", total_docs)
        col2.metric("Total Chunks", total_chunks)

class ChatMessage:
    """Enhanced chat message component."""
    
    @staticmethod
    def user_message(content: str):
        """Render user message."""
        with st.chat_message("user"):
            st.markdown(content)
            
    @staticmethod
    def assistant_message(content: str, 
                         sources: Optional[List[Dict]] = None,
                         confidence_score: Optional[float] = None,
                         model_used: Optional[str] = None):
        """Render assistant message with enhanced formatting."""
        with st.chat_message("assistant"):
            st.markdown(content)
            
            if sources or confidence_score or model_used:
                with st.expander("Response Details"):
                    if model_used:
                        st.markdown(f"**Model Used**: {model_used}")
                    if confidence_score is not None:
                        st.progress(confidence_score, text="Confidence Score")
                    
                    if sources:
                        st.markdown("**Sources**")
                        source_df = pd.DataFrame(sources)
                        source_df = source_df.rename(columns={
                            'document_id': 'Document',
                            'page_number': 'Page',
                            'similarity_score': 'Relevance'
                        })
                        source_df['Relevance'] = source_df['Relevance'].apply(
                            lambda x: f"{x:.2%}"
                        )
                        st.dataframe(source_df, hide_index=True)

class UploadProgress:
    """Component for displaying file upload and processing progress."""
    
    def __init__(self):
        self._progress_bar = None
        self._status_text = None
        
    def initialize(self):
        """Initialize progress components."""
        self._progress_bar = st.sidebar.progress(0)
        self._status_text = st.sidebar.empty()
        
    def update(self, progress: float, status: str):
        """Update progress bar and status."""
        if self._progress_bar is not None:
            self._progress_bar.progress(progress)
        if self._status_text is not None:
            self._status_text.text(status)
            
    def complete(self, success: bool = True):
        """Complete the progress indication."""
        if success:
            if self._status_text is not None:
                self._status_text.success("Processing complete!")
        else:
            if self._status_text is not None:
                self._status_text.error("Processing failed")
        # Clear progress bar
        if self._progress_bar is not None:
            self._progress_bar.empty()
        
    def clear(self):
        """Clear all progress components."""
        if self._progress_bar is not None:
            self._progress_bar.empty()
        if self._status_text is not None:
            self._status_text.empty()

class ErrorHandler:
    """Component for handling and displaying errors."""
    
    @staticmethod
    def show_error(title: str, error: Exception):
        """Display error message with details."""
        with st.sidebar.expander("Error Details", expanded=True):
            st.error(title)
            st.code(str(error))
            
    @staticmethod
    def show_warning(message: str):
        """Display warning message."""
        st.sidebar.warning(message)
        
    @staticmethod
    def show_info(message: str):
        """Display info message."""
        st.sidebar.info(message)

class ModelSelector:
    """Enhanced model selection component."""
    
    @staticmethod
    def render() -> str:
        """Render model selection interface."""
        st.sidebar.subheader("Model Settings")
        
        model_options = {
            "openai": {
                "name": "OpenAI GPT-4",
                "description": "Latest GPT-4 model with highest accuracy",
                "icon": "🤖"
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "description": "Claude model with strong reasoning capabilities",
                "icon": "🧠"
            },
            "gemini": {
                "name": "Google Gemini",
                "description": "Google's latest language model",
                "icon": "🌟"
            }
        }
        
        selected_model = st.sidebar.selectbox(
            "Select AI Model",
            options=list(model_options.keys()),
            format_func=lambda x: f"{model_options[x]['icon']} {model_options[x]['name']}"
        )
        
        # Show model description
        st.sidebar.caption(model_options[selected_model]['description'])
        
        return selected_model

class FileManager:
    """Enhanced file management component."""
    
    @staticmethod
    def render_file_list(uploaded_files: Dict[str, str], 
                        on_remove_callback) -> Optional[str]:
        """Render list of uploaded files with management options."""
        if not uploaded_files:
            return None
            
        st.sidebar.subheader("Uploaded Documents")
        
        selected_file = None
        for filename, doc_id in uploaded_files.items():
            col1, col2, col3 = st.sidebar.columns([3, 1, 1])
            
            with col1:
                st.text(filename[:20] + "..." if len(filename) > 20 else filename)
            
            with col2:
                if st.button("👁️", key=f"view_{doc_id}", help="View document details"):
                    selected_file = filename
                    
            with col3:
                if st.button("🗑️", key=f"remove_{doc_id}", help="Remove document"):
                    on_remove_callback(filename)
                    st.rerun()
                    
        return selected_file
        
    @staticmethod
    def render_file_details(filename: str, doc_id: str, stats: Dict):
        """Render detailed view of a document."""
        with st.sidebar.expander("Document Details", expanded=True):
            st.text(f"Filename: {filename}")
            st.text(f"Document ID: {doc_id}")
            
            metrics = {
                "Pages": stats.get("pages", 0),
                "Chunks": stats.get("chunks", 0),
                "Size": f"{stats.get('size', 0) / 1024:.1f} KB"
            }
            
            cols = st.columns(len(metrics))
            for col, (label, value) in zip(cols, metrics.items()):
                col.metric(label, value)

class SessionInfo:
    """Component for displaying session information."""
    
    @staticmethod
    def render(session_id: str, start_time: float):
        """Render session information."""
        with st.sidebar.expander("Session Info", expanded=False):
            st.text(f"Session ID: {session_id[:8]}...")
            
            # Calculate session duration
            duration = time.time() - start_time
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            
            if hours > 0:
                st.text(f"Duration: {hours}h {minutes}m")
            else:
                st.text(f"Duration: {minutes}m")

class ChatInterface:
    """Enhanced chat interface component."""
    
    def __init__(self):
        self.message_container = st.container()
        
    def render_messages(self, chat_history: List[Dict]):
        """Render chat messages with enhanced formatting."""
        with self.message_container:
            for message in chat_history:
                if message["role"] == "user":
                    ChatMessage.user_message(message["content"])
                else:
                    ChatMessage.assistant_message(
                        content=message["content"],
                        sources=message.get("sources"),
                        confidence_score=message.get("confidence_score"),
                        model_used=message.get("model_used")
                    )
                    
    def render_input(self, callback, disabled: bool = False) -> None:
        """Render chat input with enhanced features."""
        input_placeholder = (
            "Please upload documents to start chatting"
            if disabled else
            "Ask a question about your documents..."
        )
        
        user_input = st.chat_input(
            input_placeholder,
            disabled=disabled,
            key="chat_input"
        )
        
        if user_input:
            callback(user_input)

class SystemMetrics:
    """Component for displaying system metrics."""
    
    @staticmethod
    def render(metrics: Dict):
        """Render system performance metrics."""
        with st.sidebar.expander("System Metrics", expanded=False):
            cols = st.columns(3)
            
            with cols[0]:
                st.metric(
                    "Memory Usage",
                    f"{metrics['memory_usage']:.1f}MB"
                )
                
            with cols[1]:
                st.metric(
                    "Response Time",
                    f"{metrics['avg_response_time']:.2f}s"
                )
                
            with cols[2]:
                st.metric(
                    "Requests/min",
                    metrics['requests_per_minute']
                )

class Settings:
    """Component for application settings."""
    
    @staticmethod
    def render() -> Dict:
        """Render settings interface and return configured values."""
        with st.sidebar.expander("Advanced Settings", expanded=False):
            settings = {
                "chunk_size": st.slider(
                    "Chunk Size",
                    min_value=100,
                    max_value=2000,
                    value=1000,
                    help="Size of text chunks for processing"
                ),
                
                "chunk_overlap": st.slider(
                    "Chunk Overlap",
                    min_value=0,
                    max_value=500,
                    value=200,
                    help="Overlap between consecutive chunks"
                ),
                
                "max_context_chunks": st.slider(
                    "Max Context Chunks",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="Maximum number of chunks to include in context"
                ),
                
                "temperature": st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="Controls randomness in responses"
                )
            }
            
            return settings