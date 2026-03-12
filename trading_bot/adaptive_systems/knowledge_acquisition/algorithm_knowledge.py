"""Algorithm Knowledge Acquisition for Self-Improving Trading Bot.

from pathlib import Path
This module implements the acquisition of knowledge from trading algorithms,
research papers, code repositories, and algorithmic strategies.
"""

import uuid
import json
import logging
import os
import re
try:
    import requests
except ImportError:
    requests = None
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
# Try to import git, but make it optional
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Git module not available. Repository extraction will be limited.")

from .knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, KnowledgeStatus
import pathlib
import numpy

logger = logging.getLogger(__name__)


class AlgorithmSource(Enum):
    """Types of algorithm sources."""
    RESEARCH_PAPER = "research_paper"
    CODE_REPOSITORY = "code_repository"
    TRADING_STRATEGY = "trading_strategy"
    INDICATOR = "indicator"
    OPTIMIZATION_ALGORITHM = "optimization_algorithm"
    RISK_MODEL = "risk_model"


@dataclass
class AlgorithmKnowledge:
    """Knowledge extracted from algorithms and code."""
    title: str
    content: str
    source: AlgorithmSource
    author: str
    implementation: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[datetime] = None
    complexity: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.85
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlgorithmKnowledgeAcquisition:
    """System for acquiring knowledge from algorithms and code."""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """Initialize the algorithm knowledge acquisition system.
        
        Args:
            knowledge_base: Knowledge base to store acquired knowledge
        """
        self.knowledge_base = knowledge_base
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.acquisition_history = []
        
        logger.info("Algorithm knowledge acquisition system initialized")
    
    def extract_from_code(self, code: str, title: str, source_type: AlgorithmSource,
                        author: str, metadata: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        """Extract knowledge from code.
        
        Args:
            code: Code content to extract knowledge from
            title: Title of the source
            source_type: Type of source
            author: Author of the code
            metadata: Additional metadata
            
        Returns:
            List of extracted knowledge items
        """
        logger.info(f"Extracting knowledge from code: {title}")
        
        # Extract functions, classes, and docstrings
        functions = self._extract_functions(code)
        classes = self._extract_classes(code)
        docstrings = self._extract_docstrings(code)
        
        # Create knowledge items
        knowledge_items = []
        
        # Process each function
        for func_name, func_code in functions.items():
            # Extract docstring and signature
            docstring = self._extract_function_docstring(func_code)
            signature = self._extract_function_signature(func_code)
            
            # Generate content
            content = f"Function: {func_name}\n\nSignature: {signature}\n\n"
            if docstring:
                content += f"Documentation:\n{docstring}\n\n"
            content += f"Implementation:\n```python\n{func_code}\n```"
            
            # Extract tags
            tags = self._extract_tags(func_code)
            tags.append(f"function:{func_name}")
            
            # Create knowledge item
            item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=f"Function: {func_name}",
                content=content,
                knowledge_type=KnowledgeType.ALGORITHM,
                source=f"{source_type.value}:{title}",
                tags=tags,
                confidence=0.9,  # High confidence for code
                acquisition_date=datetime.now(),
                status=KnowledgeStatus.UNVERIFIED,
                metadata={
                    "author": author,
                    "function_name": func_name,
                    "source_title": title,
                    "source_type": source_type.value,
                    **(metadata or {})
                }
            )
            
            knowledge_items.append(item)
        
        # Process each class
        for class_name, class_code in classes.items():
            # Extract docstring
            docstring = self._extract_class_docstring(class_code)
            
            # Generate content
            content = f"Class: {class_name}\n\n"
            if docstring:
                content += f"Documentation:\n{docstring}\n\n"
            content += f"Implementation:\n```python\n{class_code}\n```"
            
            # Extract tags
            tags = self._extract_tags(class_code)
            tags.append(f"class:{class_name}")
            
            # Create knowledge item
            item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=f"Class: {class_name}",
                content=content,
                knowledge_type=KnowledgeType.ALGORITHM,
                source=f"{source_type.value}:{title}",
                tags=tags,
                confidence=0.9,  # High confidence for code
                acquisition_date=datetime.now(),
                status=KnowledgeStatus.UNVERIFIED,
                metadata={
                    "author": author,
                    "class_name": class_name,
                    "source_title": title,
                    "source_type": source_type.value,
                    **(metadata or {})
                }
            )
            
            knowledge_items.append(item)
        
        # Create overall algorithm knowledge item
        if docstrings:
            overall_content = f"Algorithm: {title}\n\nOverview:\n{docstrings.get('module', '')}\n\n"
            overall_content += "Key Components:\n"
            for name, doc in docstrings.items():
                if name != "module":
                    overall_content += f"- {name}: {doc.split('.')[0]}.\n"
            
            # Extract tags
            tags = self._extract_tags(code)
            tags.append(f"algorithm:{title}")
            
            # Create knowledge item
            item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=f"Algorithm: {title}",
                content=overall_content,
                knowledge_type=KnowledgeType.ALGORITHM,
                source=f"{source_type.value}:{title}",
                tags=tags,
                confidence=0.85,
                acquisition_date=datetime.now(),
                status=KnowledgeStatus.UNVERIFIED,
                metadata={
                    "author": author,
                    "source_title": title,
                    "source_type": source_type.value,
                    **(metadata or {})
                }
            )
            
            knowledge_items.append(item)
        
        logger.info(f"Extracted {len(knowledge_items)} knowledge items from code: {title}")
        return knowledge_items
    
    def extract_from_file(self, file_path: str, source_type: AlgorithmSource,
                        author: str, metadata: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        """Extract knowledge from a code file.
        
        Args:
            file_path: Path to the file
            source_type: Type of source
            author: Author of the code
            metadata: Additional metadata
            
        Returns:
            List of extracted knowledge items
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        title = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return self.extract_from_code(code, title, source_type, author, metadata)
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from file {file_path}: {e}")
            return []
    
    def extract_from_repository(self, repo_url: str, local_path: Optional[str] = None,
                              source_type: AlgorithmSource = AlgorithmSource.CODE_REPOSITORY,
                              author: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract knowledge from a Git repository.
        
        Args:
            repo_url: URL of the repository
            local_path: Local path to clone the repository to
            source_type: Type of source
            author: Author of the code
            metadata: Additional metadata
            
        Returns:
            List of stored knowledge item IDs
        """
        if not GIT_AVAILABLE:
            logger.warning(f"Git module not available. Cannot extract from repository {repo_url}")
            return []
            
        if not local_path:
            local_path = os.path.join(os.getcwd(), "temp_repos", repo_url.split("/")[-1])
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        try:
            # Clone repository
            if not os.path.exists(local_path):
                git.Repo.clone_from(repo_url, local_path)
                logger.info(f"Cloned repository {repo_url} to {local_path}")
            else:
                logger.info(f"Repository already exists at {local_path}")
            
            # Extract repository info
            repo = git.Repo(local_path)
            
            # Get author if not provided
            if not author:
                try:
                    author = repo.git.log("-1", "--pretty=%an")
                except Exception:
                    author = "Unknown"
            
            # Find Python files
            python_files = []
            for root, _, files in os.walk(local_path):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
            
            # Extract knowledge from each file
            all_items = []
            for file_path in python_files:
                relative_path = os.path.relpath(file_path, local_path)
                file_metadata = {
                    "repo_url": repo_url,
                    "relative_path": relative_path,
                    **(metadata or {})
                }
                
                items = self.extract_from_file(
                    file_path, source_type, author, file_metadata
                )
                all_items.extend(items)
            
            # Store items
            stored_ids = self.store_knowledge_items(all_items)
            
            # Record in acquisition history
            self.acquisition_history.append({
                "timestamp": datetime.now(),
                "source": source_type.value,
                "repo_url": repo_url,
                "file_count": len(python_files),
                "item_count": len(stored_ids)
            })
            
            return stored_ids
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from repository {repo_url}: {e}")
            return []
    
    def extract_from_research_paper(self, paper_url: str, source_type: AlgorithmSource = AlgorithmSource.RESEARCH_PAPER,
                                  author: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract algorithm knowledge from a research paper.
        
        Args:
            paper_url: URL of the research paper
            source_type: Type of source
            author: Author of the paper
            metadata: Additional metadata
            
        Returns:
            List of stored knowledge item IDs
        """
        try:
            # Download paper content
            response = requests.get(paper_url, timeout=10)
            response.raise_for_status()
            
            # Extract text (this is a simplified approach)
            # In a real implementation, you would use a PDF parser or specific API
            text = response.text
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', text)
            title = title_match.group(1) if title_match else paper_url
            
            # Extract author if not provided
            if not author:
                author_match = re.search(r'<meta name="author" content="(.*?)"', text)
                author = author_match.group(1) if author_match else "Unknown"
            
            # Create algorithm knowledge
            algorithm = AlgorithmKnowledge(
                title=title,
                content=text,
                source=source_type,
                author=author,
                url=paper_url,
                tags=self._extract_tags(text),
                metadata=metadata or {}
            )
            
            # Convert to knowledge item
            item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=f"Research Paper: {title}",
                content=text,
                knowledge_type=KnowledgeType.ALGORITHM,
                source=f"{source_type.value}:{title}",
                tags=algorithm.tags,
                confidence=0.8,
                acquisition_date=datetime.now(),
                status=KnowledgeStatus.UNVERIFIED,
                metadata={
                    "author": author,
                    "url": paper_url,
                    "source_type": source_type.value,
                    **(metadata or {})
                }
            )
            
            # Store item
            item_id = self.knowledge_base.add_item(item)
            
            # Record in acquisition history
            self.acquisition_history.append({
                "timestamp": datetime.now(),
                "source": source_type.value,
                "url": paper_url,
                "item_id": item_id
            })
            
            return [item_id]
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from paper {paper_url}: {e}")
            return []
    
    def store_knowledge_items(self, items: List[KnowledgeItem]) -> List[str]:
        """Store knowledge items in the knowledge base.
        
        Args:
            items: Knowledge items to store
            
        Returns:
            List of stored item IDs
        """
        stored_ids = []
        
        for item in items:
            # Check for duplicates
            similar_items = self._find_similar_items(item)
            
            if similar_items:
                # Update existing item instead of creating a duplicate
                existing_item = similar_items[0]
                logger.info(f"Found similar item: {existing_item.title} (ID: {existing_item.id})")
                
                # Merge tags
                existing_item.tags = list(set(existing_item.tags + item.tags))
                
                # Update confidence if new item has higher confidence
                if item.confidence > existing_item.confidence:
                    existing_item.confidence = item.confidence
                
                # Update metadata
                existing_item.metadata.update(item.metadata)
                
                # Store updated item
                self.knowledge_base.update_item(existing_item)
                stored_ids.append(existing_item.id)
                
            else:
                # Store new item
                item_id = self.knowledge_base.add_item(item)
                stored_ids.append(item_id)
        
        return stored_ids
    
    def _extract_functions(self, code: str) -> Dict[str, str]:
        """Extract functions from code.
        
        Args:
            code: Code to extract functions from
            
        Returns:
            Dictionary mapping function names to function code
        """
        functions = {}
        
        # Simple regex pattern to find Python functions
        pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*?\).*?:'
        matches = re.finditer(pattern, code, re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            start_pos = match.start()
            
            # Find the end of the function
            lines = code[start_pos:].split('\n')
            func_lines = [lines[0]]
            indent = len(lines[1]) - len(lines[1].lstrip())
            
            for line in lines[1:]:
                if line.strip() and not line.startswith(' ' * indent) and not line.startswith('\t'):
                    break
                func_lines.append(line)
            
            functions[func_name] = '\n'.join(func_lines)
        
        return functions
    
    def _extract_classes(self, code: str) -> Dict[str, str]:
        """Extract classes from code.
        
        Args:
            code: Code to extract classes from
            
        Returns:
            Dictionary mapping class names to class code
        """
        classes = {}
        
        # Simple regex pattern to find Python classes
        pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(.*?\))?\s*:'
        matches = re.finditer(pattern, code, re.DOTALL)
        
        for match in matches:
            class_name = match.group(1)
            start_pos = match.start()
            
            # Find the end of the class
            lines = code[start_pos:].split('\n')
            class_lines = [lines[0]]
            indent = len(lines[1]) - len(lines[1].lstrip()) if len(lines) > 1 else 0
            
            for line in lines[1:]:
                if line.strip() and not line.startswith(' ' * indent) and not line.startswith('\t'):
                    break
                class_lines.append(line)
            
            classes[class_name] = '\n'.join(class_lines)
        
        return classes
    
    def _extract_docstrings(self, code: str) -> Dict[str, str]:
        """Extract docstrings from code.
        
        Args:
            code: Code to extract docstrings from
            
        Returns:
            Dictionary mapping names to docstrings
        """
        docstrings = {}
        
        # Module docstring
        module_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        if module_match:
            docstrings["module"] = module_match.group(1).strip()
        
        # Function docstrings
        func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*?\).*?:(?:\s*"""(.*?)""")?'
        func_matches = re.finditer(func_pattern, code, re.DOTALL)
        
        for match in func_matches:
            func_name = match.group(1)
            if match.group(2):
                docstrings[func_name] = match.group(2).strip()
        
        # Class docstrings
        class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(.*?\))?\s*:(?:\s*"""(.*?)""")?'
        class_matches = re.finditer(class_pattern, code, re.DOTALL)
        
        for match in class_matches:
            class_name = match.group(1)
            if match.group(2):
                docstrings[class_name] = match.group(2).strip()
        
        return docstrings
    
    def _extract_function_docstring(self, func_code: str) -> Optional[str]:
        """Extract docstring from function code.
        
        Args:
            func_code: Function code
            
        Returns:
            Docstring if found, None otherwise
        """
        docstring_match = re.search(r'"""(.*?)"""', func_code, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()
        return None
    
    def _extract_class_docstring(self, class_code: str) -> Optional[str]:
        """Extract docstring from class code.
        
        Args:
            class_code: Class code
            
        Returns:
            Docstring if found, None otherwise
        """
        docstring_match = re.search(r'"""(.*?)"""', class_code, re.DOTALL)
        if docstring_match:
            return docstring_match.group(1).strip()
        return None
    
    def _extract_function_signature(self, func_code: str) -> str:
        """Extract function signature.
        
        Args:
            func_code: Function code
            
        Returns:
            Function signature
        """
        signature_match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*\s*\(.*?\))', func_code)
        if signature_match:
            return signature_match.group(1)
        return ""
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content.
        
        Args:
            content: Content to extract tags from
            
        Returns:
            List of tags
        """
        # Use TF-IDF to find important terms
        tfidf_matrix = self.vectorizer.fit_transform([content])
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Get top TF-IDF scores
        scores = zip(feature_names, tfidf_matrix.toarray()[0])
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Extract top terms as tags
        tags = [word for word, score in sorted_scores[:10] if len(word) > 3]
        
        # Add algorithm-specific tags if they appear in the content
        algorithm_terms = [
            "algorithm", "function", "class", "method", "optimization",
            "trading", "strategy", "indicator", "backtest", "risk",
            "model", "prediction", "analysis", "pattern", "signal"
        ]
        
        for term in algorithm_terms:
            if term in content.lower() and term not in tags:
                tags.append(term)
        
        return tags[:15]  # Limit to 15 tags
    
    def _find_similar_items(self, item: KnowledgeItem) -> List[KnowledgeItem]:
        """Find similar items in the knowledge base.
        
        Args:
            item: Knowledge item to find similar items for
            
        Returns:
            List of similar knowledge items
        """
        # First check for items with the same title
        title_matches = self.knowledge_base.search(
            knowledge_type=KnowledgeType.ALGORITHM,
            query=item.title,
            limit=5
        )
        
        # If we have title matches, check content similarity
        if title_matches:
            similar_items = []
            for match in title_matches:
                similarity = self._calculate_text_similarity(item.content, match.content)
                if similarity > 0.7:  # High similarity threshold
                    similar_items.append(match)
            
            if similar_items:
                return similar_items
        
        # If no title matches or no similar content, check by tags
        if item.tags:
            tag_matches = self.knowledge_base.search(
                knowledge_type=KnowledgeType.ALGORITHM,
                tags=item.tags[:3],
                limit=5
            )
            
            similar_items = []
            for match in tag_matches:
                similarity = self._calculate_text_similarity(item.content, match.content)
                if similarity > 0.6:  # Slightly lower threshold for tag matches
                    similar_items.append(match)
            
            if similar_items:
                return similar_items
        
        return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF cosine similarity between texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
        return (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
