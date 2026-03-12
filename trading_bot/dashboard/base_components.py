"""
Base components for the dashboard
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
try:
    from dash import html
except ImportError:
    dash = None


class ComponentType(Enum):
    """Types of dashboard components."""
    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    ALERT = "alert"
    CONTROL = "control"
    CUSTOM = "custom"


@dataclass
class ComponentConfig:
    """Configuration for a dashboard component."""
    id: str
    title: str
    type: ComponentType
    refresh_interval: int = 5000  # milliseconds
    width: int = 12  # Bootstrap column width (out of 12)
    height: Optional[int] = None  # Height in pixels
    data_source: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


class BaseComponent:
    """Base class for dashboard components."""
    
    def __init__(self, config: ComponentConfig):
        """
        Initialize the component.
        
        Args:
            config: Component configuration
        """
        self.config = config
        self.id = config.id
        self.title = config.title
        self.type = config.type
        self.data = {}
        
        logger.debug(f"Initialized component: {self.id}")
    
    def update(self, data: Dict[str, Any]):
        """
        Update component data.
        
        Args:
            data: New data for the component
        """
        self.data = data
    
    def render(self) -> html.Div:
        """
        Render the component.
        
        Returns:
            Dash component
        """
        return html.Div([
            html.H5(self.title),
            html.P("Component not implemented")
        ], id=f"{self.id}-container")


# Configure logging
logger = logging.getLogger(__name__)
