import PyPDF2
from typing import Dict, List, Tuple
import hashlib
from dataclasses import dataclass
import tempfile
import os
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    text: str
    page_number: int
    chunk_number: int
    document_id: str

@dataclass
class ProcessedDocument:
    document_id: str
    filename: str
    chunks: List[DocumentChunk]
    total_pages: int
    
class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the PDF processor with chunk size and overlap configurations.
        
        Args:
            chunk_size (int): The target size of each text chunk in characters
            chunk_overlap (int): The number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def generate_document_id(self, file_content: bytes, filename: str) -> str:
        """Generate a unique document ID based on file content and name."""
        content_hash = hashlib.sha256(file_content).hexdigest()
        name_hash = hashlib.sha256(filename.encode()).hexdigest()[:8]
        return f"{name_hash}-{content_hash[:16]}"
        
    def process_pdf(self, file_content: bytes, filename: str) -> ProcessedDocument:
        """Process a PDF file and extract text in chunks."""
        try:
            document_id = self.generate_document_id(file_content, filename)
            chunks: List[DocumentChunk] = []
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Open and process PDF
                with open(tmp_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    
                    # Combine text from all pages first
                    full_text = ""
                    for page_num in range(total_pages):
                        page_text = pdf_reader.pages[page_num].extract_text()
                        if page_text.strip():
                            full_text += page_text + "\n\n"
                
                # Split the combined text into chunks
                chunks = self._split_text_into_chunks(
                    full_text, 
                    1,  # Page number not as relevant when chunking full text
                    document_id
                )
                
                logger.info(f"Created {len(chunks)} chunks from PDF")
                
                return ProcessedDocument(
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks,
                    total_pages=total_pages
                )
                
            finally:
                # Ensure the file handle is closed before trying to remove
                try:
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {tmp_file_path}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {str(e)}")
            raise
                
    def _split_text_into_chunks(self, text: str, page_number: int, document_id: str) -> List[DocumentChunk]:
        """Split text into chunks of approximately equal size."""
        chunk_size = 2000  # Increased chunk size
        overlap = 200
        
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        chunk_number = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        page_number=page_number,
                        chunk_number=chunk_number,
                        document_id=document_id
                    ))
                    chunk_number += 1
                    # Keep some overlap
                    current_chunk = paragraph + "\n\n"
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                page_number=page_number,
                chunk_number=chunk_number,
                document_id=document_id
            ))
        
        return chunks