#!/usr/bin/env python
"""
AlphaAlgo Approval Dashboard - Web Interface

Launch the web dashboard for managing approval requests.

Usage:
    python run_approval_dashboard.py                # Start dashboard
    python run_approval_dashboard.py --port 8080    # Custom port
    python run_approval_dashboard.py --setup        # Run setup wizard
"""

import argparse
import asyncio
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.unified_approval import (
    get_approval_hub,
    ApprovalCategory,
    ApprovalPriority,
    RiskLevel,
    ApprovalStatus,
)

try:
    from flask import Flask, render_template_string, request, jsonify, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not installed. Install with: pip install flask")


# HTML Template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AlphaAlgo Approval Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0a0e27;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 16px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #1a1f3a;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .stat-card h3 { font-size: 14px; color: #888; margin-bottom: 10px; text-transform: uppercase; }
        .stat-card .value { font-size: 32px; font-weight: bold; color: #667eea; }
        .section {
            background: #1a1f3a;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .section h2 {
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .request-card {
            background: #0f1429;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #888;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .request-card:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
        }
        .request-card.critical { border-left-color: #ef4444; }
        .request-card.high { border-left-color: #f59e0b; }
        .request-card.medium { border-left-color: #10b981; }
        .request-card.low { border-left-color: #6b7280; }
        .request-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        .request-title { font-size: 18px; font-weight: 600; margin-bottom: 5px; }
        .request-meta {
            font-size: 13px;
            color: #888;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.critical { background: #ef4444; color: white; }
        .badge.high { background: #f59e0b; color: white; }
        .badge.medium { background: #10b981; color: white; }
        .badge.low { background: #6b7280; color: white; }
        .badge.risk-critical { background: #dc2626; }
        .badge.risk-high { background: #ea580c; }
        .badge.risk-medium { background: #ca8a04; }
        .badge.risk-low { background: #16a34a; }
        .request-description { margin: 15px 0; line-height: 1.6; }
        .request-details {
            background: #0a0e27;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            font-size: 13px;
        }
        .request-details dt {
            color: #888;
            margin-top: 8px;
            font-weight: 600;
        }
        .request-details dd { margin-left: 0; margin-top: 4px; }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-approve {
            background: #10b981;
            color: white;
        }
        .btn-approve:hover { background: #059669; }
        .btn-reject {
            background: #ef4444;
            color: white;
        }
        .btn-reject:hover { background: #dc2626; }
        .btn-details {
            background: #667eea;
            color: white;
        }
        .btn-details:hover { background: #5568d3; }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            transition: transform 0.2s;
        }
        .refresh-btn:hover { transform: scale(1.1); }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #1a1f3a;
            padding: 30px;
            border-radius: 15px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .modal-close {
            background: none;
            border: none;
            color: #888;
            font-size: 24px;
            cursor: pointer;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            background: #0a0e27;
            border: 1px solid #333;
            border-radius: 6px;
            color: #e0e0e0;
            margin-top: 8px;
            font-family: inherit;
        }
        textarea { min-height: 100px; resize: vertical; }
        label { display: block; margin-top: 15px; color: #888; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AlphaAlgo Approval Dashboard</h1>
            <p>Centralized approval management for all bot requests</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>Pending</h3>
                <div class="value" id="stat-pending">{{ stats.pending_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Approved Today</h3>
                <div class="value" id="stat-approved">{{ stats.approved }}</div>
            </div>
            <div class="stat-card">
                <h3>Rejected Today</h3>
                <div class="value" id="stat-rejected">{{ stats.rejected }}</div>
            </div>
            <div class="stat-card">
                <h3>Approval Rate</h3>
                <div class="value" id="stat-rate">{{ "%.0f"|format(stats.approval_rate * 100) }}%</div>
            </div>
        </div>

        {% if requests %}
            {% for priority_name, priority_requests in requests_by_priority.items() %}
                {% if priority_requests %}
                <div class="section">
                    <h2>{{ priority_emoji[priority_name] }} {{ priority_name }} Priority ({{ priority_requests|length }})</h2>
                    {% for req in priority_requests %}
                    <div class="request-card {{ priority_name.lower() }}">
                        <div class="request-header">
                            <div>
                                <div class="request-title">{{ req.title }}</div>
                                <div class="request-meta">
                                    <span>ID: {{ req.request_id }}</span>
                                    <span>Category: {{ req.category.value }}</span>
                                    <span>Requested by: {{ req.requester }}</span>
                                </div>
                            </div>
                            <div>
                                <span class="badge {{ priority_name.lower() }}">{{ priority_name }}</span>
                                <span class="badge risk-{{ req.risk_level.value }}">{{ req.risk_level.value }}</span>
                            </div>
                        </div>
                        
                        <div class="request-description">{{ req.description }}</div>
                        
                        <div class="request-details">
                            <dl>
                                <dt>Created:</dt>
                                <dd>{{ req.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</dd>
                                {% if req.expires_at %}
                                <dt>Expires:</dt>
                                <dd>{{ req.expires_at.strftime('%Y-%m-%d %H:%M:%S') }}
                                    {% if req.time_remaining() %}
                                        (in {{ "%.1f"|format(req.time_remaining().total_seconds() / 3600) }} hours)
                                    {% else %}
                                        (EXPIRED)
                                    {% endif %}
                                </dd>
                                {% endif %}
                                {% if req.test_score %}
                                <dt>Test Score:</dt>
                                <dd>{{ "%.1f"|format(req.test_score * 100) }}%</dd>
                                {% endif %}
                            </dl>
                        </div>
                        
                        <div class="button-group">
                            <button class="btn btn-approve" onclick="approveRequest('{{ req.request_id }}')">
                                ✓ Approve
                            </button>
                            <button class="btn btn-reject" onclick="rejectRequest('{{ req.request_id }}')">
                                ✗ Reject
                            </button>
                            <button class="btn btn-details" onclick="showDetails('{{ req.request_id }}')">
                                📋 Details
                            </button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            {% endfor %}
        {% else %}
            <div class="section">
                <div class="empty-state">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <h2>All Clear!</h2>
                    <p>No pending approval requests at the moment.</p>
                </div>
            </div>
        {% endif %}
    </div>

    <button class="refresh-btn" onclick="location.reload()">↻</button>

    <!-- Approve Modal -->
    <div id="approveModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Approve Request</h2>
                <button class="modal-close" onclick="closeModal('approveModal')">×</button>
            </div>
            <form id="approveForm">
                <input type="hidden" id="approve-request-id">
                <label>Approver Name:</label>
                <input type="text" id="approve-approver" value="human" required>
                <label>Reason (optional):</label>
                <textarea id="approve-reason"></textarea>
                <label>Conditions (optional, one per line):</label>
                <textarea id="approve-conditions"></textarea>
                <div class="button-group" style="margin-top: 20px;">
                    <button type="submit" class="btn btn-approve">✓ Approve</button>
                    <button type="button" class="btn btn-reject" onclick="closeModal('approveModal')">Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Reject Modal -->
    <div id="rejectModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Reject Request</h2>
                <button class="modal-close" onclick="closeModal('rejectModal')">×</button>
            </div>
            <form id="rejectForm">
                <input type="hidden" id="reject-request-id">
                <label>Approver Name:</label>
                <input type="text" id="reject-approver" value="human" required>
                <label>Reason (required):</label>
                <textarea id="reject-reason" required></textarea>
                <div class="button-group" style="margin-top: 20px;">
                    <button type="submit" class="btn btn-reject">✗ Reject</button>
                    <button type="button" class="btn btn-details" onclick="closeModal('rejectModal')">Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        function approveRequest(requestId) {
            document.getElementById('approve-request-id').value = requestId;
            document.getElementById('approveModal').classList.add('active');
        }

        function rejectRequest(requestId) {
            document.getElementById('reject-request-id').value = requestId;
            document.getElementById('rejectModal').classList.add('active');
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }

        function showDetails(requestId) {
            window.location.href = '/approval/' + requestId;
        }

        document.getElementById('approveForm').onsubmit = async function(e) {
            e.preventDefault();
            const requestId = document.getElementById('approve-request-id').value;
            const approver = document.getElementById('approve-approver').value;
            const reason = document.getElementById('approve-reason').value;
            const conditions = document.getElementById('approve-conditions').value
                .split('\\n')
                .filter(c => c.trim())
                .map(c => c.trim());

            const response = await fetch('/api/approve', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({requestId, approver, reason, conditions})
            });

            if (response.ok) {
                alert('Request approved!');
                location.reload();
            } else {
                alert('Failed to approve request');
            }
        };

        document.getElementById('rejectForm').onsubmit = async function(e) {
            e.preventDefault();
            const requestId = document.getElementById('reject-request-id').value;
            const approver = document.getElementById('reject-approver').value;
            const reason = document.getElementById('reject-reason').value;

            const response = await fetch('/api/reject', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({requestId, approver, reason})
            });

            if (response.ok) {
                alert('Request rejected!');
                location.reload();
            } else {
                alert('Failed to reject request');
            }
        };

        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""


def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    hub = get_approval_hub()
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        requests = hub.get_pending_requests()
        stats = hub.get_stats()
        
        # Group by priority
        requests_by_priority = {
            'CRITICAL': [r for r in requests if r.priority == ApprovalPriority.CRITICAL],
            'HIGH': [r for r in requests if r.priority == ApprovalPriority.HIGH],
            'MEDIUM': [r for r in requests if r.priority == ApprovalPriority.MEDIUM],
            'LOW': [r for r in requests if r.priority == ApprovalPriority.LOW],
        }
        
        priority_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟡',
            'MEDIUM': '🟢',
            'LOW': '⚪',
        }
        
        return render_template_string(
            DASHBOARD_HTML,
            requests=requests,
            requests_by_priority=requests_by_priority,
            stats=stats,
            priority_emoji=priority_emoji,
        )
    
    @app.route('/api/approve', methods=['POST'])
    async def api_approve():
        """API endpoint to approve request"""
        data = request.json
        success = await hub.approve(
            data['requestId'],
            data['approver'],
            reason=data.get('reason'),
            conditions=data.get('conditions'),
        )
        return jsonify({'success': success})
    
    @app.route('/api/reject', methods=['POST'])
    async def api_reject():
        """API endpoint to reject request"""
        data = request.json
        success = await hub.reject(
            data['requestId'],
            data['approver'],
            data['reason'],
        )
        return jsonify({'success': success})
    
    @app.route('/approval/<request_id>')
    def approval_details(request_id):
        """View detailed approval request"""
        req = hub.get_request(request_id)
        if not req:
            return "Request not found", 404
        
        return f"<pre>{req.generate_summary()}</pre>"
    
    return app


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AlphaAlgo Approval Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Port to run on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    args = parser.parse_args()
    
    if args.setup:
        print("Setup wizard not yet implemented")
        return
    
    if not FLASK_AVAILABLE:
        print("\n❌ Flask is required to run the web dashboard")
        print("Install with: pip install flask")
        print("\nAlternatively, use the CLI tool: python approve.py")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("  🤖 AlphaAlgo Approval Dashboard")
    print("=" * 70)
    print(f"\n✓ Starting dashboard on http://{args.host}:{args.port}")
    print("\nPress Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    # Open browser
    if not args.no_browser:
        webbrowser.open(f'http://{args.host}:{args.port}')
    
    # Run Flask app
    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
