"""Code Generator for Self-Improving Trading Bot.

import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple
This module implements a code generator that can create new code based on
acquired knowledge from various sources.
"""

import os
import re
import json
import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

import openai
import aiohttp
from gpt4all import GPT4All

from ..knowledge_acquisition.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType
from enum import auto
import pathlib

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Type of AI model."""
    GPT4 = "gpt-4"
    GPT4ALL = "gpt4all"


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    name: str
    temperature: float
    max_tokens: int
    api_type: str  # "openai" or "azure"
    strengths: List[str]
    endpoint: Optional[str] = None


@dataclass
class CodeGenerationConfig:
    """Configuration for code generation."""
    max_tokens: int = 4000
    temperature: float = 0.2
    model: str = "gpt-4"
    safety_checks: bool = True
    validation_level: str = "strict"
    allow_imports: bool = True
    allowed_modules: List[str] = field(default_factory=lambda: [
        "numpy", "pandas", "scipy", "sklearn", "torch", "tensorflow",
        "matplotlib", "seaborn", "plotly", "statsmodels", "nltk",
        "datetime", "time", "os", "sys", "math", "random", "re", "json",
        "collections", "itertools", "functools", "operator", "typing",
        "dataclasses", "enum", "abc", "logging", "warnings", "traceback",
        "threading", "multiprocessing", "asyncio", "aiohttp", "requests"
    ])
    code_style: str = "pep8"
    docstring_style: str = "google"
    include_tests: bool = True
    include_type_hints: bool = True


@dataclass
class GeneratedCode:
    """Generated code with metadata."""
    code: str
    model: str
    prompt: str
    generation_time: float
    token_count: int
    target_file: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    validated: bool = False
    safety_checked: bool = False


class CodeGenerator:
    """Generator for code based on knowledge."""
    
    def __init__(self, knowledge_base: KnowledgeBase, api_keys: Optional[Dict[str, str]] = None, 
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the code generator.
        
        Args:
            knowledge_base: Knowledge base to use
            api_keys: Dictionary of API keys for different services
            config: Configuration dictionary
        """
        self.knowledge_base = knowledge_base
        self.api_keys = api_keys or {}
        self.config = config or {}
        
        # Set OpenAI API key if available
        if "openai" in self.api_keys:
            openai.api_key = self.api_keys["openai"]
        
        # Initialize model configurations
        self.models = self._initialize_models()
        
        # Set default model
        default_model = self.config.get("code_generation", {}).get("default_model", "gpt-4")
        self.default_model = self.models.get(default_model, self.models.get("gpt-4"))
        
        # Set model selection strategy
        self.model_selection = self.config.get("code_generation", {}).get("model_selection", "auto")
        
        logger.info("Code generator initialized")
    
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations.
        
        Returns:
            Dictionary of model configurations
        """
        models = {}
        model_configs = self.config.get("code_generation", {}).get("models", {})
        api_endpoints = self.config.get("api_endpoints", {})
        
        # Default GPT-4 configuration
        models["gpt-4"] = ModelConfig(
            name="gpt-4",
            temperature=0.2,
            max_tokens=4000,
            api_type="openai",
            strengths=["complex algorithms", "architecture design", "refactoring"]
        )
        
        # Default Phi-3-mini configuration
        models["phi-3-mini"] = ModelConfig(
            name="phi-3-mini",
            temperature=0.3,
            max_tokens=2048,
            api_type="azure",
            endpoint=api_endpoints.get("azure_phi3_mini"),
            strengths=["simple functions", "bug fixes", "documentation"]
        )
        
        # Override with configuration if available
        for model_name, model_config in model_configs.items():
            if model_name in models:
                # Update existing model configuration
                models[model_name].temperature = model_config.get("temperature", models[model_name].temperature)
                models[model_name].max_tokens = model_config.get("max_tokens", models[model_name].max_tokens)
                models[model_name].api_type = model_config.get("api_type", models[model_name].api_type)
                models[model_name].strengths = model_config.get("strengths", models[model_name].strengths)
                
                # Set endpoint if available
                if models[model_name].api_type == "azure":
                    endpoint_key = f"azure_{model_name.replace('-', '_')}"
                    models[model_name].endpoint = api_endpoints.get(endpoint_key, models[model_name].endpoint)
            else:
                # Create new model configuration
                models[model_name] = ModelConfig(
                    name=model_name,
                    temperature=model_config.get("temperature", 0.2),
                    max_tokens=model_config.get("max_tokens", 2000),
                    api_type=model_config.get("api_type", "openai"),
                    strengths=model_config.get("strengths", []),
                    endpoint=api_endpoints.get(f"azure_{model_name.replace('-', '_')}")
                )
        
        return models
    
    def _select_model(self, purpose: str, target_file: str, knowledge_items: List[KnowledgeItem]) -> ModelConfig:
        """Select the best model for the task.
        
        Args:
            purpose: Purpose of the code generation
            target_file: Target file to generate code for
            knowledge_items: Knowledge items to use
            
        Returns:
            Selected model configuration
        """
        # If manual selection, always use default model
        if self.model_selection == "manual":
            return self.default_model
        
        # If selection by strengths, match purpose with model strengths
        if self.model_selection == "strengths":
            purpose_lower = purpose.lower()
            best_match = None
            best_score = -1
            
            for model_name, model_config in self.models.items():
                score = sum(1 for strength in model_config.strengths if strength.lower() in purpose_lower)
                if score > best_score:
                    best_score = score
                    best_match = model_config
            
            if best_match and best_score > 0:
                return best_match
        
        # Auto selection based on task complexity
        file_extension = os.path.splitext(target_file)[1].lower()
        file_size = os.path.getsize(target_file) if os.path.exists(target_file) else 0
        knowledge_size = sum(len(item.content) for item in knowledge_items)
        
        # Use GPT-4 for complex tasks
        if any([
            "refactor" in purpose.lower(),
            "architecture" in purpose.lower(),
            "complex" in purpose.lower(),
            file_size > 10000,  # Large files
            knowledge_size > 20000,  # Lots of knowledge
            file_extension in [".py", ".js", ".ts", ".java"]  # Complex languages
        ]):
            return self.models.get("gpt-4", self.default_model)
        
        # Use GPT4All for simpler tasks or when offline generation is preferred
        if any([
            "fix bug" in purpose.lower(),
            "documentation" in purpose.lower(),
            "comment" in purpose.lower(),
            "simple" in purpose.lower(),
            file_size < 5000,  # Small files
            file_extension in [".md", ".txt", ".csv", ".json", ".yaml"],  # Simple formats
            "offline" in purpose.lower()  # Explicit offline request
        ]):
            return self.models.get("gpt4all", self.default_model)
        
        # Default to the default model
        return self.default_model
    
    async def _generate_with_openai(self, prompt: str, model_config: ModelConfig) -> Tuple[str, Dict[str, Any]]:
        """Generate code using OpenAI API.
        
        Args:
            prompt: Prompt to send to the API
            model_config: Model configuration
            
        Returns:
            Generated code and response metadata
        """
        response = await openai.ChatCompletion.acreate(
            model=model_config.name,
            messages=[
                {"role": "system", "content": "You are an expert software developer. Generate high-quality, well-documented code based on the provided knowledge and context."},
                {"role": "user", "content": prompt}
            ],
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens
        )
        
        code = response.choices[0].message.content
        metadata = {"token_count": response.usage.total_tokens}
        
        return code, metadata
    
    async def _generate_with_gpt4all(self, prompt: str, model_config: ModelConfig) -> Tuple[str, Dict[str, Any]]:
        """Generate code using GPT4All locally.
        
        Args:
            prompt: Prompt to send to GPT4All
            model_config: Model configuration
            
        Returns:
            Generated code and response metadata
        """
        model_path = self.config.get("local_models", {}).get("gpt4all_path")
        if not model_path or not os.path.exists(model_path):
            raise ValueError(f"GPT4All model not found at {model_path}")
        
        # Create system prompt
        system_prompt = "You are an expert software developer. Generate high-quality, well-documented code based on the provided knowledge and context."
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        # Run GPT4All in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            code = await loop.run_in_executor(
                None,
                self._run_gpt4all_generation,
                model_path,
                full_prompt,
                model_config
            )
            
            # Estimate token count
            token_count = len(prompt.split()) + len(code.split())
            metadata = {
                "token_count": token_count,
                "model_type": model_config.model_type,
                "offline": True
            }
            
            return code, metadata
            
        except Exception as e:
            raise Exception(f"GPT4All generation error: {str(e)}")
    
    def _run_gpt4all_generation(self, model_path: str, prompt: str, model_config: ModelConfig) -> str:
        """Run GPT4All generation in a separate thread.
        
        Args:
            model_path: Path to GPT4All model file
            prompt: Full prompt to send to model
            model_config: Model configuration
            
        Returns:
            Generated code
        """
        # Initialize GPT4All model
        model = GPT4All(model_path)
        try:
            model.model_type = model_config.model_type
            model.batch_size = model_config.batch_size
            model.threads = model_config.threads
            
            # Generate response
            response = model.generate(
                prompt,
                max_tokens=model_config.max_tokens,
                temp=model_config.temperature,
                top_k=50,
                top_p=0.95,
                repeat_penalty=1.3
            )
            
            return response.strip()
            
        finally:
            # Clean up
            model.reset()
            del model
    
    async def generate_code(self, purpose: str, target_file: str, knowledge_ids: List[str], 
                         additional_context: Optional[str] = None, model_name: Optional[str] = None) -> GeneratedCode:
        """Generate code based on knowledge.
        
        Args:
            purpose: Purpose of the code generation
            target_file: Target file to generate code for
            knowledge_ids: IDs of knowledge items to use
            additional_context: Additional context to include in the prompt
            model_name: Name of the model to use (optional)
            
        Returns:
            Generated code with metadata
        """
        logger.info(f"Generating code for {target_file} with purpose: {purpose}")
        
        # Get knowledge items
        knowledge_items = []
        for knowledge_id in knowledge_ids:
            item = self.knowledge_base.get_item(knowledge_id)
            if item:
                knowledge_items.append(item)
        
        # Select model
        if model_name and model_name in self.models:
            model_config = self.models[model_name]
        else:
            model_config = self._select_model(purpose, target_file, knowledge_items)
        
        logger.info(f"Selected model {model_config.name} for code generation")
        
        # Build prompt
        prompt = self._build_prompt(purpose, target_file, knowledge_items, additional_context)
        
        # Generate code
        start_time = asyncio.get_event_loop().time()
        
        try:
            if model_config.api_type == "openai":
                code, response_metadata = await self._generate_with_openai(prompt, model_config)
            elif model_config.api_type == "local":
                code, response_metadata = await self._generate_with_gpt4all(prompt, model_config)
            else:
                raise ValueError(f"Unknown API type: {model_config.api_type}")
        except Exception as e:
            logger.error(f"Error generating code with {model_config.name}: {e}")
            # Fall back to default model if available and different
            if model_config.name != self.default_model.name:
                logger.info(f"Falling back to {self.default_model.name}")
                model_config = self.default_model
                if model_config.api_type == "openai":
                    code, response_metadata = await self._generate_with_openai(prompt, model_config)
                elif model_config.api_type == "local":
                    code, response_metadata = await self._generate_with_gpt4all(prompt, model_config)
                else:
                    raise ValueError(f"Unknown API type: {model_config.api_type}")
            else:
                logger.error("Failed to generate code with all available models")
                raise
        
        end_time = asyncio.get_event_loop().time()
        
        # Clean up code
        code = self._clean_code(code)
        
        # Create metadata
        metadata = {
            "purpose": purpose,
            "target_file": target_file,
            "knowledge_ids": knowledge_ids,
            "token_count": response_metadata.get("token_count", 0),
            "api_type": model_config.api_type,
            "model_type": model_config.model_type if hasattr(model_config, "model_type") else None,
            "offline": response_metadata.get("offline", False)
        }
        
        # Record in history
        self.generation_history.append({
            "timestamp": datetime.now(),
            "purpose": purpose,
            "target_file": target_file,
            "knowledge_count": len(knowledge_items),
            "code_length": len(code),
            "model": model_config.name,
            "offline": response_metadata.get("offline", False)
        })
        
        # Return generated code
        return GeneratedCode(
            code=code,
            model=model_config.name,
            prompt=prompt,
            generation_time=end_time - start_time,
            token_count=response_metadata.get("token_count", 0),
            target_file=target_file,
            metadata=metadata
        )
    
    async def improve_existing_code(self, file_path: str, purpose: str,
                                 knowledge_ids: Optional[List[str]] = None,
                                 knowledge_query: Optional[str] = None,
                                 knowledge_tags: Optional[List[str]] = None,
                                 additional_context: Optional[str] = None) -> GeneratedCode:
        """Improve existing code based on knowledge.
        
        Args:
            file_path: Path to the existing code file
            purpose: Purpose of the improvement
            knowledge_ids: IDs of knowledge items to use
            knowledge_query: Query to search for knowledge items
            knowledge_tags: Tags to search for knowledge items
            additional_context: Additional context for code generation
            
        Returns:
            Generated improved code
        """
        logger.info(f"Improving existing code: {file_path}")
        
        # Read existing code
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_code = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return GeneratedCode(
                code=f"# Error reading file: {e}",
                purpose=purpose,
                source_knowledge=[],
                dependencies=[],
                target_file=file_path,
                validated=False,
                safety_checked=False,
                metadata={"error": f"Error reading file: {e}"}
            )
        
        # Generate improved code
        return await self.generate_code(
            purpose=purpose,
            target_file=file_path,
            knowledge_ids=knowledge_ids,
            knowledge_query=knowledge_query,
            knowledge_tags=knowledge_tags,
            existing_code=existing_code,
            additional_context=additional_context
        )
    
    async def generate_new_module(self, module_name: str, module_purpose: str,
                               knowledge_query: Optional[str] = None,
                               knowledge_tags: Optional[List[str]] = None) -> GeneratedCode:
        """Generate a new module based on knowledge.
        
        Args:
            module_name: Name of the module to generate
            module_purpose: Purpose of the module
            knowledge_query: Query to search for knowledge items
            knowledge_tags: Tags to search for knowledge items
            
        Returns:
            Generated module code
        """
        logger.info(f"Generating new module: {module_name}")
        
        # Determine target file path
        target_file = f"trading_bot/{module_name.replace('.', '/')}.py"
        
        # Generate module code
        return await self.generate_code(
            purpose=f"Create new module: {module_purpose}",
            target_file=target_file,
            knowledge_query=knowledge_query,
            knowledge_tags=knowledge_tags,
            additional_context=f"This is a new module named '{module_name}' with purpose: {module_purpose}"
        )
    
    async def _collect_knowledge(self, knowledge_ids: Optional[List[str]] = None,
                              knowledge_query: Optional[str] = None,
                              knowledge_tags: Optional[List[str]] = None) -> List[KnowledgeItem]:
        """Collect knowledge items for code generation.
        
        Args:
            knowledge_ids: IDs of knowledge items to use
            knowledge_query: Query to search for knowledge items
            knowledge_tags: Tags to search for knowledge items
            
        Returns:
            List of knowledge items
        """
        knowledge_items = []
        
        # Collect by IDs
        if knowledge_ids:
            for item_id in knowledge_ids:
                item = self.knowledge_base.get_item(item_id)
                if item:
                    knowledge_items.append(item)
        
        # Collect by query and tags
        if knowledge_query or knowledge_tags:
            search_results = self.knowledge_base.search(
                query=knowledge_query,
                tags=knowledge_tags,
                min_confidence=0.7,
                limit=20
            )
            
            # Add search results, avoiding duplicates
            existing_ids = {item.id for item in knowledge_items}
            for item in search_results:
                if item.id not in existing_ids:
                    knowledge_items.append(item)
                    existing_ids.add(item.id)
        
        return knowledge_items
    
    def _prepare_generation_prompt(self, purpose: str, knowledge_items: List[KnowledgeItem],
                                 existing_code: Optional[str] = None,
                                 additional_context: Optional[str] = None) -> str:
        """Prepare prompt for code generation.
        
        Args:
            purpose: Purpose of the code to generate
            knowledge_items: Knowledge items to use
            existing_code: Existing code to modify
            additional_context: Additional context for code generation
            
        Returns:
            Generation prompt
        """
        prompt = f"# Code Generation Task\n\n"
        prompt += f"## Purpose\n{purpose}\n\n"
        
        # Add configuration
        prompt += "## Configuration\n"
        prompt += f"- Code style: {self.config.code_style}\n"
        prompt += f"- Docstring style: {self.config.docstring_style}\n"
        prompt += f"- Include type hints: {self.config.include_type_hints}\n"
        prompt += f"- Include tests: {self.config.include_tests}\n\n"
        
        # Add existing code if provided
        if existing_code:
            prompt += "## Existing Code\n"
            prompt += "```python\n"
            prompt += existing_code
            prompt += "\n```\n\n"
        
        # Add additional context if provided
        if additional_context:
            prompt += "## Additional Context\n"
            prompt += additional_context
            prompt += "\n\n"
        
        # Add knowledge items
        prompt += "## Knowledge Items\n\n"
        for i, item in enumerate(knowledge_items):
            prompt += f"### Knowledge Item {i+1}: {item.title}\n"
            prompt += f"Source: {item.source}\n"
            prompt += f"Type: {item.knowledge_type.value}\n"
            prompt += f"Tags: {', '.join(item.tags)}\n"
            prompt += f"Content:\n{item.content}\n\n"
        
        # Add instructions
        prompt += "## Instructions\n"
        prompt += "1. Generate high-quality Python code based on the provided knowledge items.\n"
        prompt += "2. Follow the specified code style and docstring style.\n"
        prompt += "3. Include comprehensive docstrings and comments.\n"
        prompt += "4. Ensure the code is efficient, robust, and maintainable.\n"
        prompt += "5. Only use allowed imports and dependencies.\n"
        
        if existing_code:
            prompt += "6. Improve the existing code while maintaining its core functionality.\n"
            prompt += "7. Preserve any critical existing functionality and interfaces.\n"
        else:
            prompt += "6. Create a complete implementation that fulfills the stated purpose.\n"
            prompt += "7. Include necessary classes, functions, and utilities.\n"
        
        if self.config.include_tests:
            prompt += "8. Include unit tests for the generated code.\n"
        
        prompt += "\nGenerate only the Python code without any additional explanations or markdown formatting.\n"
        
        return prompt
    
    async def _call_code_generation_api(self, prompt: str) -> Optional[str]:
        """Call code generation API.
        
        Args:
            prompt: Generation prompt
            
        Returns:
            Generated code if successful, None otherwise
        """
        if "openai" not in self.api_keys:
            logger.error("OpenAI API key not provided")
            return None
        try:
        
            
            headers = {
                "Authorization": f"Bearer {self.api_keys['openai']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
            
            # Extract code from response
            content = result["choices"][0]["message"]["content"]
            
            # Extract code from markdown if needed
            code_pattern = r"```python\n(.*?)```"
            code_matches = re.findall(code_pattern, content, re.DOTALL)
            
            if code_matches:
                # Combine all code blocks
                return "\n\n".join(code_matches)
            else:
                # Return the whole content if no code blocks found
                return content
            
        except Exception as e:
            logger.error(f"Error calling code generation API: {e}")
            return None
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """Extract dependencies from generated code.
        
        Args:
            code: Generated code
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        # Extract import statements
        import_pattern = r"^\s*import\s+([a-zA-Z0-9_.,\s]+)$|^\s*from\s+([a-zA-Z0-9_.]+)\s+import"
        import_matches = re.finditer(import_pattern, code, re.MULTILINE)
        
        for match in import_matches:
            if match.group(1):  # import x, y, z
                modules = [m.strip() for m in match.group(1).split(",")]
                for module in modules:
                    # Extract base module (e.g., 'numpy' from 'numpy.random')
                    base_module = module.split(".")[0]
                    if base_module not in dependencies:
                        dependencies.append(base_module)
            elif match.group(2):  # from x import y
                module = match.group(2)
                base_module = module.split(".")[0]
                if base_module not in dependencies:
                    dependencies.append(base_module)
        
        return dependencies
    
    def get_generation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get code generation history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of generation history entries
        """
        return self.generation_history[-limit:]
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about code generation.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_generations": len(self.generation_history),
            "by_purpose": {},
            "by_target_file": {},
            "recent_generations": len([g for g in self.generation_history 
                                     if (datetime.now() - g["timestamp"]).days < 30])
        }
        
        # Count by purpose and target file
        for gen in self.generation_history:
            purpose = gen["purpose"]
            stats["by_purpose"][purpose] = stats["by_purpose"].get(purpose, 0) + 1
            
            target_file = gen["target_file"]
            stats["by_target_file"][target_file] = stats["by_target_file"].get(target_file, 0) + 1
        
        return stats
