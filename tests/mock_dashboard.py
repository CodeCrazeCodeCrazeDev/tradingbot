"""
Mock implementations of dashboard components for testing and demonstration.
"""

import time
import threading
from typing import Any, Callable, Dict, List
import dash
import dash_bootstrap_components as dbc
from dash import html


class DashboardDataProvider:
    """Mock data provider for dashboard."""
    
    def __init__(self):
        """Initialize the data provider."""
        self.data_sources = {}
        self.callbacks = {}
        self._running = False
        self._thread = None
    
    def register_data_source(self, source_id: str, data_source: Callable,
                           update_interval: float) -> None:
        """Register a data source."""
        self.data_sources[source_id] = {
            'function': data_source,
            'interval': update_interval,
            'last_update': 0
        }
    
    def register_callback(self, source_id: str, callback: Callable) -> None:
        """Register a callback for data updates."""
        if source_id not in self.callbacks:
            self.callbacks[source_id] = []
        self.callbacks[source_id].append(callback)
    
    def start(self) -> None:
        """Start the data provider."""
        self._running = True
        self._thread = threading.Thread(target=self._update_loop)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the data provider."""
        self._running = False
        if self._thread:
            self._thread.join()
    
    def _update_loop(self) -> None:
        """Update loop for data sources."""
        while self._running:
            current_time = time.time()
            
            for source_id, source in self.data_sources.items():
                if current_time - source['last_update'] >= source['interval']:
                    try:
                        data = source['function']()
                        source['last_update'] = current_time
                        
                        # Notify callbacks
                        if source_id in self.callbacks:
                            for callback in self.callbacks[source_id]:
                                callback(source_id, data)
                    except Exception as e:
                        print(f"Error updating {source_id}: {e}")
            
            time.sleep(0.1)


class DashboardServer:
    """Mock dashboard server."""
    
    def __init__(self, title: str = "Dashboard", theme: str = "darkly",
                 refresh_interval: int = 1000, data_provider: DashboardDataProvider = None):
        """Initialize the dashboard server."""
        self.title = title
        self.theme = theme
        self.refresh_interval = refresh_interval
        self.data_provider = data_provider or DashboardDataProvider()
        self.panels = {}
        self.layout_config = []
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.DARKLY],
            suppress_callback_exceptions=True
        )
    
    def register_panel(self, panel_id: str, panel: 'DashboardPanel') -> None:
        """Register a dashboard panel."""
        self.panels[panel_id] = panel
    
    def configure_layout(self, layout_config: List[Dict[str, Any]]) -> None:
        """Configure the dashboard layout."""
        self.layout_config = layout_config
        
        # Create layout
        self.app.layout = self._create_layout()
        
        # Register panel callbacks
        for panel_id, panel in self.panels.items():
            panel.register_callbacks(self.app, self.data_provider)
    
    def _create_layout(self) -> html.Div:
        """Create the dashboard layout."""
        tabs = []
        
        for section in self.layout_config:
            panels = []
            for panel_id in section['panels']:
                if panel_id in self.panels:
                    panels.append(self.panels[panel_id].get_layout())
            
            tab = dbc.Tab(
                dbc.Row(panels),
                label=section['name']
            )
            tabs.append(tab)
        
        return html.Div([
            dbc.NavbarSimple(
                brand=self.title,
                color="primary",
                dark=True
            ),
            dbc.Container([
                dbc.Tabs(tabs)
            ], fluid=True)
        ])
    
    def run(self, host: str = "localhost", port: int = 8050,
            debug: bool = False, **kwargs) -> None:
        """Run the dashboard server."""
        # Start data provider
        if self.data_provider:
            self.data_provider.start()
        
        try:
            print(f"Starting dashboard server at http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug, **kwargs)
        finally:
            if self.data_provider:
                self.data_provider.stop()


class DashboardPanel:
    """Base class for dashboard panels."""
    
    def __init__(self, id_prefix: str):
        """Initialize the panel."""
        self.id_prefix = id_prefix
    
    def id(self, component_id: str) -> str:
        """Generate a unique ID for a component."""
        return f"{self.id_prefix}-{component_id}"
    
    def get_layout(self) -> dbc.Card:
        """Get the panel layout."""
        raise NotImplementedError("Subclasses must implement get_layout")
    
    def register_callbacks(self, app: dash.Dash,
                         data_provider: DashboardDataProvider) -> None:
        """Register callbacks for this panel."""
        pass
