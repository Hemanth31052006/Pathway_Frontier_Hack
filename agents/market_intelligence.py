"""
Agent 2: Market Intelligence - FIXED PATHWAY SYNTAX
Manages knowledge base with Pathway for real-time document processing
"""

import os
import PyPDF2
import io
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from agents.base_agent import BaseAgent

try:
    import pathway as pw
    PATHWAY_AVAILABLE = True
except ImportError:
    PATHWAY_AVAILABLE = False
    print("⚠️ Pathway not installed. Run: pip install pathway")


class MarketIntelligenceAgent(BaseAgent):
    """Manages knowledge base with Pathway and vector search"""
    
    def __init__(self):
        super().__init__("🧠 Market Intelligence")
        
        # Initialize embedding model
        self.log("Loading Sentence Transformer model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.log("✅ Embedding model loaded (384 dimensions)")
        
        self.vector_store = []
        self.documents = []
        
        # Check Pathway availability
        if not PATHWAY_AVAILABLE:
            self.log("⚠️ Pathway not available, using manual indexing only")
    
    def create_embedding(self, text: str) -> np.ndarray:
        """Create embedding using Sentence Transformer"""
        return self.embedding_model.encode(text, show_progress_bar=False)
    
    def setup_pathway_pipeline(self):
        """
        Setup Pathway real-time document processing pipeline
        FIXED VERSION - Correct metadata access
        """
        
        if not PATHWAY_AVAILABLE:
            self.log("⚠️ Pathway not installed, skipping pipeline setup")
            return None
        
        self.log("Setting up Pathway real-time pipeline...")
        
        try:
            # Ensure knowledge_base folder exists
            os.makedirs("knowledge_base", exist_ok=True)
            
            # Monitor knowledge_base folder in STREAMING mode
            knowledge_docs = pw.io.fs.read(
                path="knowledge_base/",
                format="binary",
                mode="streaming",  # KEY: This enables real-time monitoring
                with_metadata=True
            )
            
            # Parse documents
            # FIXED: Correct way to access metadata
            parsed = knowledge_docs.select(
                text=pw.apply(lambda data: self._extract_text(data), pw.this.data),
                filepath=pw.this.path  # ← FIXED: Use pw.this.path instead of pw.this._metadata
            )
            
            # Split into chunks
            chunked = parsed.select(
                chunks=pw.apply(
                    lambda text: self._split_text(text, max_tokens=400),
                    pw.this.text
                ),
                filepath=pw.this.filepath
            )
            
            # Flatten chunks (each chunk becomes a row)
            flattened = chunked.flatten(pw.this.chunks).select(
                chunk_text=pw.this.chunks,
                filepath=pw.this.filepath
            )
            
            # Create embeddings
            embedded = flattened.select(
                chunk_text=pw.this.chunk_text,
                vector=pw.apply(self.create_embedding, pw.this.chunk_text),
                filepath=pw.this.filepath
            )
            
            self.log("✅ Pathway pipeline active - monitoring knowledge_base/")
            self.log("   Mode: STREAMING (real-time file monitoring)")
            self.log("   Watching: knowledge_base/*.txt, *.pdf")
            
            return embedded
            
        except Exception as e:
            self.log(f"⚠️ Pathway setup error: {e}")
            self.log(f"   Error details: {type(e).__name__}")
            return None
    
    def _extract_text(self, data: bytes) -> str:
        """
        Extract text from document bytes
        Handles both plain text and PDF files
        """
        try:
            # Try as plain text first
            return data.decode('utf-8', errors='ignore')
        except:
            # If it's a PDF, extract text
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(data))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e:
                self.log(f"⚠️ Text extraction failed: {e}")
                return ""
    
    def _split_text(self, text: str, max_tokens: int = 400) -> List[str]:
        """
        Split text into chunks for embedding
        Uses simple word-based splitting
        """
        if not text or not text.strip():
            return [""]
        
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Rough estimate: 4 characters per token
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > max_tokens * 4:
                if current_chunk:  # Only add non-empty chunks
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [""]
    
    def index_documents_manually(self):
        """
        Manually index documents from knowledge_base/ folder
        This is used as:
        1. Fallback when Pathway is not available
        2. Initial indexing of existing documents
        3. Complementary to Pathway streaming (for UI feedback)
        """
        self.log("Manually indexing documents from knowledge_base/...")
        
        if not os.path.exists("knowledge_base"):
            os.makedirs("knowledge_base")
            self.log("⚠️ Created knowledge_base/ folder (empty)")
            return
        
        files = [f for f in os.listdir("knowledge_base") 
                if f.endswith(('.txt', '.pdf'))]
        
        if not files:
            self.log("⚠️ No documents found in knowledge_base/")
            self.log("   Add .txt or .pdf files to enable market intelligence")
            return
        
        self.log(f"Found {len(files)} files to index")
        
        # Clear existing store (for refresh)
        self.vector_store = []
        
        indexed_count = 0
        chunk_count = 0
        
        for filename in files:
            filepath = os.path.join("knowledge_base", filename)
            try:
                # Read file
                if filename.endswith('.pdf'):
                    text = self.extract_text_from_pdf(filepath)
                else:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                
                if not text.strip():
                    continue
                
                # Split into chunks
                chunks = self._split_text(text)
                
                # Create embeddings
                for chunk in chunks:
                    if chunk.strip():
                        embedding = self.create_embedding(chunk)
                        self.vector_store.append({
                            'text': chunk,
                            'vector': embedding,
                            'source': filename
                        })
                        chunk_count += 1
                
                indexed_count += 1
                self.log(f"✅ Indexed {filename} ({len(chunks)} chunks)")
                
            except Exception as e:
                self.log(f"⚠️ Error indexing {filename}: {str(e)[:100]}")
        
        self.log(f"✅ Indexing complete!")
        self.log(f"   Files: {indexed_count}/{len(files)}")
        self.log(f"   Chunks: {chunk_count}")
        self.log(f"   Ready for semantic search")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            self.log(f"Error reading PDF {pdf_path}: {e}")
            return ""
    
    def query_insights(self, query: str, top_k: int = 5) -> List[str]:
        """
        Query vector store for relevant insights using semantic search
        
        Args:
            query: Search query (e.g., "latest banking sector news")
            top_k: Number of top results to return
        
        Returns:
            List of relevant text chunks
        """
        
        if not self.vector_store:
            self.log("⚠️ Vector store empty, returning fallback insights")
            return self._get_fallback_insights()
        
        self.log(f"Querying vector store: '{query[:60]}...'")
        
        # Create query embedding
        query_vector = self.create_embedding(query)
        
        # Calculate cosine similarity with all chunks
        similarities = []
        for doc in self.vector_store:
            similarity = np.dot(query_vector, doc['vector']) / (
                np.linalg.norm(query_vector) * np.linalg.norm(doc['vector'])
            )
            similarities.append({
                'text': doc['text'],
                'similarity': similarity,
                'source': doc['source']
            })
        
        # Sort by similarity and get top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = similarities[:top_k]
        
        self.log(f"✅ Found {len(top_results)} relevant insights")
        for i, result in enumerate(top_results[:3], 1):
            self.log(f"   {i}. {result['source']} (similarity: {result['similarity']:.3f})")
        
        return [result['text'] for result in top_results]
    
    def _get_fallback_insights(self) -> List[str]:
        """
        Return fallback insights when vector store is empty
        Provides generic but useful market context
        """
        return [
            "Indian IT sector showing strong growth momentum with major companies posting double-digit revenue growth driven by digital transformation deals.",
            "Banking sector demonstrating recovery with improved asset quality. Credit growth picking up across retail and corporate segments.",
            "Pharmaceutical sector facing margin pressures in domestic market but long-term outlook positive with export opportunities and new drug launches.",
            "Infrastructure and capital goods sector benefiting from government push on infrastructure spending and manufacturing initiatives.",
            "FMCG sector showing steady growth with premiumization trend. Rural demand gradually recovering after slowdown."
        ]
    
    def get_knowledge_base_stats(self) -> dict:
        """Get statistics about current knowledge base"""
        file_count = len([f for f in os.listdir("knowledge_base") 
                         if f.endswith(('.txt', '.pdf'))]) if os.path.exists("knowledge_base") else 0
        
        return {
            "total_files": file_count,
            "total_chunks": len(self.vector_store),
            "pathway_active": PATHWAY_AVAILABLE,
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384
        }