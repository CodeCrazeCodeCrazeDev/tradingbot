"""
Knowledge Transfer - Transfers Learned Knowledge to Trading Bot

Converts learned concepts into actionable trading components:
- Strategy implementations
- Indicator code
- Risk management rules
- Trading signals
"""

import json
import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import logging
import ast
import re

logger = logging.getLogger(__name__)


class TransferType(Enum):
    """Types of knowledge transfer"""
    INDICATOR = auto()
    STRATEGY = auto()
    RISK_RULE = auto()
    SIGNAL_LOGIC = auto()
    EXECUTION_ALGO = auto()
    PATTERN_DETECTOR = auto()


@dataclass
class TransferableKnowledge:
    """Knowledge ready for transfer to the bot"""
    id: str
    name: str
    transfer_type: TransferType
    source_concepts: List[str]
    code: str
    parameters: Dict[str, Any]
    validation_status: str  # pending, validated, failed
    test_results: Dict[str, Any]
    integration_path: str  # Where in the bot to integrate
    priority: int  # 1-10
    created_at: datetime
    transferred_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'transfer_type': self.transfer_type.name,
            'source_concepts': self.source_concepts,
            'code': self.code,
            'parameters': self.parameters,
            'validation_status': self.validation_status,
            'test_results': self.test_results,
            'integration_path': self.integration_path,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'transferred_at': self.transferred_at.isoformat() if self.transferred_at else None,
        }


class KnowledgeTransfer:
    """
    Transfers learned knowledge to the trading bot.
    
    Features:
    - Convert concepts to code
    - Validate code before transfer
    - Safe integration with existing bot
    - Track transfer history
    """
    
    # Code templates for different transfer types
    CODE_TEMPLATES = {
        TransferType.INDICATOR: '''
class {class_name}:
    """
    {description}
    
    Learned from: {sources}
    """
    
    def __init__(self, {params}):
        {init_code}
    
    def calculate(self, prices):
        """Calculate indicator value"""
        {calc_code}
        return result
''',
        
        TransferType.STRATEGY: '''
class {class_name}Strategy:
    """
    {description}
    
    Learned from: {sources}
    """
    
    def __init__(self, {params}):
        {init_code}
    
    def generate_signal(self, market_data):
        """Generate trading signal"""
        {signal_code}
        return signal
    
    def get_entry_conditions(self, market_data):
        """Check entry conditions"""
        {entry_code}
        return conditions_met
    
    def get_exit_conditions(self, market_data, position):
        """Check exit conditions"""
        {exit_code}
        return should_exit
''',
        
        TransferType.RISK_RULE: '''
class {class_name}RiskRule:
    """
    {description}
    
    Learned from: {sources}
    """
    
    def __init__(self, {params}):
        {init_code}
    
    def validate_trade(self, trade_params):
        """Validate if trade meets risk rules"""
        {validation_code}
        return is_valid, reason
    
    def calculate_position_size(self, capital, risk_per_trade):
        """Calculate appropriate position size"""
        {sizing_code}
        return position_size
''',
        
        TransferType.SIGNAL_LOGIC: '''
class {class_name}Signal:
    """
    {description}
    
    Learned from: {sources}
    """
    
    def __init__(self, {params}):
        {init_code}
    
    def evaluate(self, market_data):
        """Evaluate signal conditions"""
        {eval_code}
        return signal_strength, direction
''',
    }
    
    def __init__(self, data_dir: str = "autonomous_learner_data", bot_dir: str = "trading_bot"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.bot_dir = Path(bot_dir)
        self.transfer_dir = self.data_dir / "transfers"
        self.transfer_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "transfer_log.db"
        self._init_database()
        
        self.pending_transfers: List[TransferableKnowledge] = []
        self.completed_transfers: List[TransferableKnowledge] = []
        
        logger.info("KnowledgeTransfer initialized")
    
    def _init_database(self):
        """Initialize transfer log database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id TEXT PRIMARY KEY,
                name TEXT,
                transfer_type TEXT,
                source_concepts TEXT,
                code TEXT,
                parameters TEXT,
                validation_status TEXT,
                test_results TEXT,
                integration_path TEXT,
                priority INTEGER,
                created_at TEXT,
                transferred_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfer_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_id TEXT,
                action TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_indicator_transfer(self, concept_name: str, concept_data: Dict) -> TransferableKnowledge:
        """Create a transferable indicator from a learned concept"""
        class_name = self._to_class_name(concept_name)
        
        # Extract code from concept
        code_template = concept_data.get('code_template', '')
        
        # Build full indicator class
        code = self.CODE_TEMPLATES[TransferType.INDICATOR].format(
            class_name=class_name,
            description=concept_data.get('description', ''),
            sources=', '.join(concept_data.get('sources', [])),
            params='period=14',
            init_code='self.period = period',
            calc_code=code_template if code_template else 'result = prices[-1]',
        )
        
        transfer = TransferableKnowledge(
            id=hashlib.md5(f"indicator_{concept_name}".encode()).hexdigest()[:12],
            name=f"{class_name}Indicator",
            transfer_type=TransferType.INDICATOR,
            source_concepts=[concept_name],
            code=code,
            parameters={'period': 14},
            validation_status='pending',
            test_results={},
            integration_path='trading_bot/indicators/learned/',
            priority=5,
            created_at=datetime.now(),
            transferred_at=None,
        )
        
        self.pending_transfers.append(transfer)
        self._store_transfer(transfer)
        
        return transfer
    
    def create_strategy_transfer(self, concept_name: str, concept_data: Dict) -> TransferableKnowledge:
        """Create a transferable strategy from learned concepts"""
        class_name = self._to_class_name(concept_name)
        
        code = self.CODE_TEMPLATES[TransferType.STRATEGY].format(
            class_name=class_name,
            description=concept_data.get('description', ''),
            sources=', '.join(concept_data.get('sources', [])),
            params='',
            init_code='pass',
            signal_code="signal = {'direction': 'HOLD', 'strength': 0.0}",
            entry_code='conditions_met = False',
            exit_code='should_exit = False',
        )
        
        transfer = TransferableKnowledge(
            id=hashlib.md5(f"strategy_{concept_name}".encode()).hexdigest()[:12],
            name=f"{class_name}Strategy",
            transfer_type=TransferType.STRATEGY,
            source_concepts=[concept_name],
            code=code,
            parameters={},
            validation_status='pending',
            test_results={},
            integration_path='trading_bot/strategies/learned/',
            priority=7,
            created_at=datetime.now(),
            transferred_at=None,
        )
        
        self.pending_transfers.append(transfer)
        self._store_transfer(transfer)
        
        return transfer
    
    def create_risk_rule_transfer(self, concept_name: str, concept_data: Dict) -> TransferableKnowledge:
        """Create a transferable risk rule from learned concepts"""
        class_name = self._to_class_name(concept_name)
        
        code_template = concept_data.get('code_template', '')
        
        code = self.CODE_TEMPLATES[TransferType.RISK_RULE].format(
            class_name=class_name,
            description=concept_data.get('description', ''),
            sources=', '.join(concept_data.get('sources', [])),
            params='max_risk=0.02',
            init_code='self.max_risk = max_risk',
            validation_code='is_valid = True; reason = "OK"',
            sizing_code=code_template if code_template else 'position_size = capital * risk_per_trade',
        )
        
        transfer = TransferableKnowledge(
            id=hashlib.md5(f"risk_{concept_name}".encode()).hexdigest()[:12],
            name=f"{class_name}RiskRule",
            transfer_type=TransferType.RISK_RULE,
            source_concepts=[concept_name],
            code=code,
            parameters={'max_risk': 0.02},
            validation_status='pending',
            test_results={},
            integration_path='trading_bot/risk/learned/',
            priority=9,  # High priority for risk rules
            created_at=datetime.now(),
            transferred_at=None,
        )
        
        self.pending_transfers.append(transfer)
        self._store_transfer(transfer)
        
        return transfer
    
    def validate_transfer(self, transfer: TransferableKnowledge) -> bool:
        """Validate code before transfer"""
        try:
            # Check syntax
            ast.parse(transfer.code)
            
            # Check for dangerous patterns
            dangerous_patterns = [
                'os.system', 'subprocess', 'eval(', 'exec(',
                '__import__', 'open(', 'file(', 'input(',
            ]
            
            for pattern in dangerous_patterns:
                if pattern in transfer.code:
                    logger.warning(f"Dangerous pattern found: {pattern}")
                    transfer.validation_status = 'failed'
                    transfer.test_results['error'] = f"Dangerous pattern: {pattern}"
                    return False
            
            transfer.validation_status = 'validated'
            transfer.test_results['syntax'] = 'passed'
            transfer.test_results['safety'] = 'passed'
            
            self._store_transfer(transfer)
            return True
            
        except SyntaxError as e:
            transfer.validation_status = 'failed'
            transfer.test_results['error'] = str(e)
            self._store_transfer(transfer)
            return False
    
    def execute_transfer(self, transfer: TransferableKnowledge) -> bool:
        """Execute the knowledge transfer to the bot"""
        if transfer.validation_status != 'validated':
            if not self.validate_transfer(transfer):
                return False
        
            # Create target directory
            target_dir = self.bot_dir / transfer.integration_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py if needed
            init_file = target_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Learned components from autonomous learning."""\n')
            
            # Write the code file
            file_name = f"{transfer.name.lower()}.py"
            target_file = target_dir / file_name
            
            # Add header
            header = f'''"""
Auto-generated from autonomous learning system.
Transfer ID: {transfer.id}
Created: {transfer.created_at.isoformat()}
Source concepts: {', '.join(transfer.source_concepts)}
"""

import numpy as np
from typing import Dict, List, Any, Optional

'''
            
        try:
            target_file.write_text(header + transfer.code)
            
            # Update transfer record
            transfer.transferred_at = datetime.now()
            self._store_transfer(transfer)
            self._log_transfer(transfer.id, 'execute', 'success', f"Transferred to {target_file}")
            
            # Move to completed
            if transfer in self.pending_transfers:
                self.pending_transfers.remove(transfer)
            self.completed_transfers.append(transfer)
            
            logger.info(f"Successfully transferred {transfer.name} to {target_file}")
            return True
            
        except Exception as e:
            self._log_transfer(transfer.id, 'execute', 'failed', str(e))
            logger.error(f"Transfer failed: {e}")
            return False
    
    def _to_class_name(self, name: str) -> str:
        """Convert concept name to class name"""
        # Remove underscores and capitalize
        parts = name.replace('-', '_').split('_')
        return ''.join(p.capitalize() for p in parts)
    
    def _store_transfer(self, transfer: TransferableKnowledge):
        """Store transfer in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO transfers 
            (id, name, transfer_type, source_concepts, code, parameters, 
             validation_status, test_results, integration_path, priority, created_at, transferred_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transfer.id,
            transfer.name,
            transfer.transfer_type.name,
            json.dumps(transfer.source_concepts),
            transfer.code,
            json.dumps(transfer.parameters),
            transfer.validation_status,
            json.dumps(transfer.test_results),
            transfer.integration_path,
            transfer.priority,
            transfer.created_at.isoformat(),
            transfer.transferred_at.isoformat() if transfer.transferred_at else None,
        ))
        
        conn.commit()
        conn.close()
    
    def _log_transfer(self, transfer_id: str, action: str, status: str, details: str):
        """Log transfer action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transfer_log (transfer_id, action, status, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (transfer_id, action, status, details, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_transfer_summary(self) -> Dict[str, Any]:
        """Get summary of all transfers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM transfers')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM transfers WHERE validation_status = "validated"')
        validated = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM transfers WHERE transferred_at IS NOT NULL')
        completed = cursor.fetchone()[0]
        
        cursor.execute('SELECT transfer_type, COUNT(*) FROM transfers GROUP BY transfer_type')
        by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_transfers': total,
            'validated': validated,
            'completed': completed,
            'pending': total - completed,
            'by_type': by_type,
        }
    
    def transfer_all_validated(self) -> Dict[str, Any]:
        """Transfer all validated knowledge to the bot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, transfer_type, source_concepts, code, parameters, 
                   validation_status, test_results, integration_path, priority, created_at
            FROM transfers 
            WHERE validation_status = "validated" AND transferred_at IS NULL
            ORDER BY priority DESC
        ''')
        
        results = {'success': 0, 'failed': 0, 'transfers': []}
        
        for row in cursor.fetchall():
            transfer = TransferableKnowledge(
                id=row[0],
                name=row[1],
                transfer_type=TransferType[row[2]],
                source_concepts=json.loads(row[3]),
                code=row[4],
                parameters=json.loads(row[5]),
                validation_status=row[6],
                test_results=json.loads(row[7]),
                integration_path=row[8],
                priority=row[9],
                created_at=datetime.fromisoformat(row[10]),
                transferred_at=None,
            )
            
            if self.execute_transfer(transfer):
                results['success'] += 1
                results['transfers'].append({'name': transfer.name, 'status': 'success'})
            else:
                results['failed'] += 1
                results['transfers'].append({'name': transfer.name, 'status': 'failed'})
        
        conn.close()
        return results
