"""
Test Report Generator
Generates comprehensive test reports with visualizations
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
import jinja2
import markdown
import traceback
import uuid

from trading_bot.schemas.validation import TestResult, TestReport
import numpy
import pandas

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive test reports with visualizations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Output directory
        self.output_dir = self.config.get('output_dir', 'test_reports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Templates directory
        self.template_dir = self.config.get('template_dir', 'templates')
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir)
            if os.path.exists(self.template_dir)
            else jinja2.DictLoader({'report.html': self._get_default_template()})
        )
        
        logger.info("Report generator initialized")
    
    def generate_report(self, test_report: TestReport) -> str:
        """
        Generate a comprehensive HTML report
        
        Args:
            test_report: Test report data
            
        Returns:
            Path to the generated report
        """
        # Create report directory
        report_id = test_report.suite_id
        report_dir = os.path.join(self.output_dir, report_id)
        Path(report_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate plots
        plots = self._generate_plots(test_report)
        
        # Save plots
        for plot_name, fig in plots.items():
            plot_path = os.path.join(report_dir, f"{plot_name}.png")
            fig.savefig(plot_path)
            plt.close(fig)
        
        # Prepare template data
        template_data = {
            'report': test_report.dict(),
            'plots': {name: f"{name}.png" for name in plots.keys()},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': self._generate_summary(test_report)
        }
        
        try:
            # Render template
            template = self.jinja_env.get_template('report.html')
            html = template.render(**template_data)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            # Use default template
            template = jinja2.Template(self._get_default_template())
            html = template.render(**template_data)
        
        # Save HTML report
        report_path = os.path.join(report_dir, 'report.html')
        with open(report_path, 'w') as f:
            f.write(html)
        
        # Save JSON data
        json_path = os.path.join(report_dir, 'report.json')
        with open(json_path, 'w') as f:
            json.dump(test_report.dict(), f, default=str, indent=2)
        
        logger.info(f"Report generated at {report_path}")
        
        return report_path
    
    def _generate_plots(self, test_report: TestReport) -> Dict[str, plt.Figure]:
        """Generate plots for the report"""
        plots = {}
        
        # Test results summary
        fig, ax = plt.subplots(figsize=(8, 6))
        labels = ['Passed', 'Failed', 'Skipped']
        values = [
            test_report.passed_tests,
            test_report.failed_tests,
            test_report.skipped_tests
        ]
        colors = ['#4CAF50', '#F44336', '#FFC107']
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors)
        ax.set_title('Test Results Summary')
        plots['test_summary'] = fig
        
        # Execution time by test
        if test_report.results:
            fig, ax = plt.subplots(figsize=(10, 6))
            test_names = [result.test_id for result in test_report.results]
            execution_times = [result.execution_time for result in test_report.results]
            success = [result.success for result in test_report.results]
            colors = ['#4CAF50' if s else '#F44336' for s in success]
            
            y_pos = np.arange(len(test_names))
            ax.barh(y_pos, execution_times, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(test_names)
            ax.set_xlabel('Execution Time (s)')
            ax.set_title('Test Execution Time')
            plots['execution_time'] = fig
        
        return plots
    
    def _generate_summary(self, test_report: TestReport) -> str:
        """Generate a markdown summary of the test report"""
        summary = f"""
# Test Report Summary

- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Suite ID**: {test_report.suite_id}
- **Total Tests**: {test_report.total_tests}
- **Passed**: {test_report.passed_tests}
- **Failed**: {test_report.failed_tests}
- **Skipped**: {test_report.skipped_tests}
- **Total Execution Time**: {test_report.total_execution_time:.2f}s

## Test Results

| Test ID | Success | Execution Time (s) | Errors |
|---------|---------|-------------------|--------|
"""
        
        for result in test_report.results:
            success = "✅" if result.success else "❌"
            errors = len(result.errors)
            summary += f"| {result.test_id} | {success} | {result.execution_time:.2f} | {errors} |\n"
        
        return summary
    
    def _get_default_template(self) -> str:
        """Get default HTML template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Test Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .header {
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            margin-bottom: 20px;
        }
        .summary {
            margin-bottom: 20px;
        }
        .plot {
            margin-bottom: 20px;
            text-align: center;
        }
        .results {
            margin-bottom: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .success {
            color: #4CAF50;
        }
        .failure {
            color: #F44336;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Report</h1>
        <p>Generated on {{ timestamp }}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {{ report.total_tests }}</p>
        <p>Passed: {{ report.passed_tests }}</p>
        <p>Failed: {{ report.failed_tests }}</p>
        <p>Skipped: {{ report.skipped_tests }}</p>
        <p>Total Execution Time: {{ report.total_execution_time }}s</p>
    </div>
    
    <div class="plots">
        <h2>Plots</h2>
        {% for name, path in plots.items() %}
        <div class="plot">
            <h3>{{ name }}</h3>
            <img src="{{ path }}" alt="{{ name }}">
        </div>
        {% endfor %}
    </div>
    
    <div class="results">
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test ID</th>
                <th>Success</th>
                <th>Execution Time (s)</th>
                <th>Errors</th>
            </tr>
            {% for result in report.results %}
            <tr>
                <td>{{ result.test_id }}</td>
                <td class="{{ 'success' if result.success else 'failure' }}">
                    {{ '✅' if result.success else '❌' }}
                </td>
                <td>{{ result.execution_time }}</td>
                <td>{{ result.errors|length }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


class PerformanceReportGenerator:
    """
    Generates performance reports for the trading system
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Output directory
        self.output_dir = self.config.get('output_dir', 'performance_reports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("Performance report generator initialized")
    
    def generate_report(self, performance_data: Dict[str, Any]) -> str:
        """
        Generate a performance report
        
        Args:
            performance_data: Performance metrics data
            
        Returns:
            Path to the generated report
        """
        # Create report directory
        report_id = str(uuid.uuid4())
        report_dir = os.path.join(self.output_dir, report_id)
        Path(report_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate plots
        plots = self._generate_plots(performance_data)
        
        # Save plots
        for plot_name, fig in plots.items():
            plot_path = os.path.join(report_dir, f"{plot_name}.png")
            fig.savefig(plot_path)
            plt.close(fig)
        
        # Save JSON data
        json_path = os.path.join(report_dir, 'performance.json')
        with open(json_path, 'w') as f:
            json.dump(performance_data, f, default=str, indent=2)
        
        # Generate HTML report
        html_path = os.path.join(report_dir, 'performance.html')
        self._generate_html_report(performance_data, plots, html_path)
        
        logger.info(f"Performance report generated at {html_path}")
        
        return html_path
    
    def _generate_plots(self, performance_data: Dict[str, Any]) -> Dict[str, plt.Figure]:
        """Generate performance plots"""
        plots = {}
        
        # Latency by component
        if 'latency' in performance_data:
            latency_data = performance_data['latency']
            
            if latency_data:
                fig, ax = plt.subplots(figsize=(10, 6))
                components = []
                avg_latencies = []
                p95_latencies = []
                
                for component, metrics in latency_data.items():
                    components.append(component)
                    avg_latencies.append(metrics.get('avg', 0))
                    p95_latencies.append(metrics.get('p95', 0))
                
                x = np.arange(len(components))
                width = 0.35
                
                ax.bar(x - width/2, avg_latencies, width, label='Average')
                ax.bar(x + width/2, p95_latencies, width, label='P95')
                
                ax.set_ylabel('Latency (ms)')
                ax.set_title('Latency by Component')
                ax.set_xticks(x)
                ax.set_xticklabels(components)
                ax.legend()
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                plots['latency'] = fig
        
        # Throughput by component
        if 'throughput' in performance_data:
            throughput_data = performance_data['throughput']
            
            if throughput_data:
                fig, ax = plt.subplots(figsize=(10, 6))
                components = []
                throughputs = []
                
                for component, metrics in throughput_data.items():
                    components.append(component)
                    throughputs.append(metrics.get('throughput', 0))
                
                ax.bar(components, throughputs)
                ax.set_ylabel('Throughput (events/s)')
                ax.set_title('Throughput by Component')
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                plots['throughput'] = fig
        
        # Resource usage
        if 'resources' in performance_data:
            resources = performance_data['resources']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            labels = ['CPU', 'Memory']
            values = [
                resources.get('cpu_percent', 0),
                resources.get('memory_percent', 0)
            ]
            
            ax.bar(labels, values)
            ax.set_ylabel('Usage (%)')
            ax.set_title('Resource Usage')
            ax.set_ylim(0, 100)
            
            plots['resources'] = fig
        
        return plots
    
    def _generate_html_report(self, 
                            performance_data: Dict[str, Any], 
                            plots: Dict[str, plt.Figure],
                            output_path: str):
        """Generate HTML performance report"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Performance Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .header {
            background-color: #2196F3;
            color: white;
            padding: 10px;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 20px;
        }
        .plot {
            margin-bottom: 20px;
            text-align: center;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Report</h1>
        <p>Generated on {timestamp}</p>
    </div>
    
    <div class="section">
        <h2>Plots</h2>
        {plots_html}
    </div>
    
    <div class="section">
        <h2>Latency Metrics</h2>
        {latency_table}
    </div>
    
    <div class="section">
        <h2>Throughput Metrics</h2>
        {throughput_table}
    </div>
    
    <div class="section">
        <h2>Resource Usage</h2>
        {resource_table}
    </div>
</body>
</html>
        """
        
        # Generate plots HTML
        plots_html = ""
        for name, _ in plots.items():
            plots_html += f"""
        <div class="plot">
            <h3>{name.capitalize()}</h3>
            <img src="{name}.png" alt="{name}">
        </div>
            """
        
        # Generate latency table
        latency_table = """
        <table>
            <tr>
                <th>Component</th>
                <th>Average (ms)</th>
                <th>P95 (ms)</th>
                <th>Max (ms)</th>
                <th>Count</th>
            </tr>
        """
        
        if 'latency' in performance_data:
            for component, metrics in performance_data['latency'].items():
                latency_table += f"""
            <tr>
                <td>{component}</td>
                <td>{metrics.get('avg', 0):.2f}</td>
                <td>{metrics.get('p95', 0):.2f}</td>
                <td>{metrics.get('max', 0):.2f}</td>
                <td>{metrics.get('count', 0)}</td>
            </tr>
                """
        
        latency_table += "</table>"
        
        # Generate throughput table
        throughput_table = """
        <table>
            <tr>
                <th>Component</th>
                <th>Throughput (events/s)</th>
            </tr>
        """
        
        if 'throughput' in performance_data:
            for component, metrics in performance_data['throughput'].items():
                throughput_table += f"""
            <tr>
                <td>{component}</td>
                <td>{metrics.get('throughput', 0):.2f}</td>
            </tr>
                """
        
        throughput_table += "</table>"
        
        # Generate resource table
        resource_table = """
        <table>
            <tr>
                <th>Resource</th>
                <th>Usage</th>
            </tr>
        """
        
        if 'resources' in performance_data:
            resources = performance_data['resources']
            resource_table += f"""
            <tr>
                <td>CPU</td>
                <td>{resources.get('cpu_percent', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Memory</td>
                <td>{resources.get('memory_percent', 0):.1f}%</td>
            </tr>
            <tr>
                <td>Disk Read</td>
                <td>{resources.get('disk_read_bps', 0) / 1024 / 1024:.2f} MB/s</td>
            </tr>
            <tr>
                <td>Disk Write</td>
                <td>{resources.get('disk_write_bps', 0) / 1024 / 1024:.2f} MB/s</td>
            </tr>
            <tr>
                <td>Network Send</td>
                <td>{resources.get('net_send_bps', 0) / 1024 / 1024:.2f} MB/s</td>
            </tr>
            <tr>
                <td>Network Receive</td>
                <td>{resources.get('net_recv_bps', 0) / 1024 / 1024:.2f} MB/s</td>
            </tr>
            """
        
        resource_table += "</table>"
        
        # Format HTML
        html = html.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            plots_html=plots_html,
            latency_table=latency_table,
            throughput_table=throughput_table,
            resource_table=resource_table
        )
        
        # Write HTML to file
        with open(output_path, 'w') as f:
            f.write(html)
