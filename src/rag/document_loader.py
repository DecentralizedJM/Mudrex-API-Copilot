"""
Document ingestion pipeline for loading API documentation
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import re

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads and preprocesses documentation files"""
    
    @staticmethod
    def load_from_directory(directory: str, extensions: List[str] = None) -> List[Dict[str, Any]]:
        """
        Load all documents from a directory
        
        Args:
            directory: Path to documentation directory
            extensions: List of file extensions to load (default: .md, .txt)
            
        Returns:
            List of dicts with 'content', 'metadata', and 'id'
        """
        if extensions is None:
            extensions = ['.md', '.txt', '.rst']
        
        docs_path = Path(directory)
        if not docs_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        documents = []
        
        for file_path in docs_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Create metadata
                    metadata = {
                        'filename': file_path.name,
                        'filepath': str(file_path),
                        'type': file_path.suffix.lstrip('.'),
                        'size': len(content)
                    }
                    
                    # Generate unique ID
                    doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
                    
                    documents.append({
                        'content': content,
                        'metadata': metadata,
                        'id': doc_id
                    })
                    
                    logger.info(f"Loaded: {file_path.name}")
                    
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents
    
    @staticmethod
    def _chunk_large_text(content: str, chunk_size: int, overlap: int) -> List[str]:
        """Split long text into overlapping chunks with sentence-aware boundaries."""
        if len(content) <= chunk_size:
            return [content.strip()]

        chunks = []
        start = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))

            # Try to break at sentence end for readability
            if end < len(content):
                sentence_end = content.rfind('.', start, end)
                if sentence_end != -1 and sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= len(content):
                break

            # Ensure forward progress even when overlap is large
            next_start = max(end - overlap, start + 1)
            start = next_start

        return chunks

    @staticmethod
    def _split_markdown_sections(content: str) -> List[str]:
        """
        Split markdown by headings while preserving section context.

        Example chunk prefix:
        # Title > ## Request
        <section content...>
        """
        text = content.strip()
        if not text:
            return []

        lines = text.splitlines()
        sections: List[str] = []
        heading_stack: Dict[int, str] = {}
        current_lines: List[str] = []
        current_context = ""

        header_pattern = re.compile(r'^(#{1,6})\s+(.+?)\s*$')

        def flush_current() -> None:
            nonlocal current_lines
            body = "\n".join(current_lines).strip()
            if not body:
                current_lines = []
                return
            if current_context:
                sections.append(f"{current_context}\n\n{body}")
            else:
                sections.append(body)
            current_lines = []

        for line in lines:
            header_match = header_pattern.match(line)
            if header_match:
                flush_current()
                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                # Drop deeper/equal levels and keep parent path
                to_delete = [lvl for lvl in heading_stack if lvl >= level]
                for lvl in to_delete:
                    del heading_stack[lvl]
                heading_stack[level] = title

                ordered = [heading_stack[lvl] for lvl in sorted(heading_stack.keys())]
                current_context = " > ".join(ordered)
                current_lines = [line]
            else:
                current_lines.append(line)

        flush_current()

        # Fallback to whole text if no headings were found
        return sections or [text]

    @staticmethod
    def chunk_document(
        content: str,
        chunk_size: int = 1500,
        overlap: int = 200,
        section_max_size: int = 2000,
    ) -> List[str]:
        """
        Split document into retrieval-friendly chunks.

        Strategy:
        1. Split markdown into heading-based sections
        2. Keep each section as one chunk when possible
        3. If section is too large, split it with sentence-aware overlap
        
        Args:
            content: Document content
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks
            section_max_size: Maximum size of a section before sub-splitting
            
        Returns:
            List of text chunks
        """
        if len(content) <= chunk_size:
            return [content.strip()]

        sections = DocumentLoader._split_markdown_sections(content)
        chunks: List[str] = []
        for section in sections:
            if len(section) <= section_max_size:
                chunks.append(section.strip())
                continue
            chunks.extend(DocumentLoader._chunk_large_text(section, chunk_size=chunk_size, overlap=overlap))

        # Remove accidental empties
        chunks = [c for c in chunks if c]
        return chunks
    
    @staticmethod
    def process_documents(
        documents: List[Dict[str, Any]],
        chunk_size: int = 1500,
        overlap: int = 200,
        section_max_size: int = 2000,
    ) -> tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Process documents into chunks with metadata
        
        Args:
            documents: List of document dicts
            chunk_size: Maximum characters per chunk
                overlap: Overlap between chunks
                section_max_size: Maximum size of a section before sub-splitting
            
        Returns:
            Tuple of (texts, metadatas, ids)
        """
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            chunks = DocumentLoader.chunk_document(
                doc['content'],
                chunk_size=chunk_size,
                overlap=overlap,
                section_max_size=section_max_size,
            )
            
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                
                # Add chunk info to metadata
                chunk_metadata = doc['metadata'].copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['total_chunks'] = len(chunks)
                metadatas.append(chunk_metadata)
                
                # Create unique ID for chunk
                chunk_id = f"{doc['id']}_chunk_{i}"
                ids.append(chunk_id)
        
        logger.info(f"Created {len(texts)} chunks from {len(documents)} documents")
        return texts, metadatas, ids
