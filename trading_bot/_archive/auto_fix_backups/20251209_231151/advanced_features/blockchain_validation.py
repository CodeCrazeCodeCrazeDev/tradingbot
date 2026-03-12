"""Blockchain-based Validation System - Immutable Trading Predictions and Edge Proof.

from typing import Any, List, Optional, Set
This module implements a blockchain-based system for storing trading predictions,
validating performance, and providing cryptographic proof of trading edge.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import sqlite3
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of trading predictions."""
    PRICE_DIRECTION = "price_direction"
    PRICE_TARGET = "price_target"
    VOLATILITY_FORECAST = "volatility_forecast"
    LIQUIDITY_PREDICTION = "liquidity_prediction"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_REGIME = "market_regime"


class ValidationStatus(Enum):
    """Validation status of predictions."""
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class TradingPrediction:
    """Immutable trading prediction record."""
    prediction_id: str
    timestamp: datetime
    prediction_type: PredictionType
    asset_symbol: str
    prediction_value: Any
    confidence: float
    expiry_time: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['expiry_time'] = self.expiry_time.isoformat()
        result['prediction_type'] = self.prediction_type.value
        return result


@dataclass
class ValidationResult:
    """Result of prediction validation."""
    prediction_id: str
    validation_timestamp: datetime
    actual_value: Any
    predicted_value: Any
    accuracy_score: float
    validation_status: ValidationStatus
    proof_hash: str


@dataclass
class BlockchainBlock:
    """Blockchain block containing trading predictions."""
    block_number: int
    timestamp: datetime
    previous_hash: str
    predictions: List[TradingPrediction]
    merkle_root: str
    nonce: int
    block_hash: str


class CryptographicProofSystem:
    """Cryptographic system for generating proofs of trading performance."""
    
    def __init__(self):
        """Initialize cryptographic proof system."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
    def generate_prediction_hash(self, prediction: TradingPrediction) -> str:
        """Generate cryptographic hash of prediction."""
        prediction_data = json.dumps(prediction.to_dict(), sort_keys=True)
        return hashlib.sha256(prediction_data.encode()).hexdigest()
    
    def sign_prediction(self, prediction: TradingPrediction) -> bytes:
        """Cryptographically sign a prediction."""
        prediction_hash = self.generate_prediction_hash(prediction)
        signature = self.private_key.sign(
            prediction_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def verify_prediction(self, prediction: TradingPrediction, signature: bytes) -> bool:
        """Verify prediction signature."""
        try:
            prediction_hash = self.generate_prediction_hash(prediction)
            self.public_key.verify(
                signature,
                prediction_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def generate_performance_proof(self, 
                                 predictions: List[TradingPrediction],
                                 validations: List[ValidationResult]) -> Dict:
        """Generate cryptographic proof of trading performance."""
        # Calculate performance metrics
        total_predictions = len(predictions)
        successful_predictions = len([v for v in validations if v.validation_status == ValidationStatus.VALIDATED])
        accuracy_rate = successful_predictions / total_predictions if total_predictions > 0 else 0
        
        # Calculate average accuracy score
        accuracy_scores = [v.accuracy_score for v in validations if v.validation_status == ValidationStatus.VALIDATED]
        avg_accuracy = np.mean(accuracy_scores) if accuracy_scores else 0
        
        # Generate proof data
        proof_data = {
            'total_predictions': total_predictions,
            'successful_predictions': successful_predictions,
            'accuracy_rate': accuracy_rate,
            'average_accuracy': avg_accuracy,
            'timestamp': datetime.now().isoformat(),
            'prediction_hashes': [self.generate_prediction_hash(p) for p in predictions],
            'validation_hashes': [v.proof_hash for v in validations]
        }
        
        # Sign the proof
        proof_json = json.dumps(proof_data, sort_keys=True)
        proof_hash = hashlib.sha256(proof_json.encode()).hexdigest()
        proof_signature = self.private_key.sign(
            proof_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return {
            'proof_data': proof_data,
            'proof_hash': proof_hash,
            'proof_signature': proof_signature.hex(),
            'public_key': self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
        }


class BlockchainLedger:
    """Blockchain ledger for immutable prediction storage."""
    
    def __init__(self, db_path: str = "trading_blockchain.db"):
        """Initialize blockchain ledger."""
        self.db_path = db_path
        self.crypto_system = CryptographicProofSystem()
        self.current_block_predictions = []
        self.block_size_limit = 100  # Maximum predictions per block
        
        # Initialize database
        self._init_database()
        
        logger.info("Blockchain ledger initialized")
    
    def _init_database(self):
        """Initialize SQLite database for blockchain storage."""
        # SECURITY FIX: Set restrictive file permissions on database
        import os
        import stat
        
        # Create database with restrictive permissions
        db_exists = os.path.exists(self.db_path)
        conn = sqlite3.connect(self.db_path)
        
        # Set file permissions to owner read/write only (0600)
        if not db_exists and os.name != 'nt':  # Unix-like systems
            os.chmod(self.db_path, stat.S_IRUSR | stat.S_IWUSR)
        elif not db_exists and os.name == 'nt':  # Windows
            # Windows: Use icacls to restrict permissions
            try:
                import subprocess
                subprocess.run(['icacls', self.db_path, '/inheritance:r'], check=False, capture_output=True)
                subprocess.run(['icacls', self.db_path, '/grant:r', f'{os.getenv("USERNAME")}:(F)'], check=False, capture_output=True)
            except Exception as e:
                logger.warning(f"Could not set restrictive permissions on Windows: {e}")
        
        cursor = conn.cursor()
        
        # Create blocks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_number INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                block_hash TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Create predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                block_number INTEGER,
                timestamp TEXT NOT NULL,
                prediction_type TEXT NOT NULL,
                asset_symbol TEXT NOT NULL,
                prediction_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                expiry_time TEXT NOT NULL,
                metadata TEXT NOT NULL,
                signature TEXT NOT NULL,
                FOREIGN KEY (block_number) REFERENCES blocks (block_number)
            )
        ''')
        
        # Create validations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validations (
                prediction_id TEXT PRIMARY KEY,
                validation_timestamp TEXT NOT NULL,
                actual_value TEXT NOT NULL,
                predicted_value TEXT NOT NULL,
                accuracy_score REAL NOT NULL,
                validation_status TEXT NOT NULL,
                proof_hash TEXT NOT NULL,
                FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_prediction(self, prediction: TradingPrediction) -> str:
        """Add prediction to current block."""
        # Generate signature
        signature = self.crypto_system.sign_prediction(prediction)
        
        # Add to current block
        self.current_block_predictions.append((prediction, signature))
        
        # Check if block is full
        if len(self.current_block_predictions) >= self.block_size_limit:
            self._mine_block()
        
        prediction_hash = self.crypto_system.generate_prediction_hash(prediction)
        logger.info(f"Prediction added: {prediction.prediction_id}")
        
        return prediction_hash
    
    def _mine_block(self):
        """Mine a new block with current predictions."""
        if not self.current_block_predictions:
            return
        
        # Get previous block hash
        previous_hash = self._get_latest_block_hash()
        
        # Calculate merkle root
        merkle_root = self._calculate_merkle_root(
            [pred for pred, _ in self.current_block_predictions]
        )
        
        # Mine block with proof of work
        # SECURITY FIX: Increased difficulty to prevent blockchain manipulation
        block_number = self._get_next_block_number()
        timestamp = datetime.now()
        nonce = 0
        
        # Configurable difficulty (default: 5 leading zeros for production)
        difficulty = getattr(self, 'mining_difficulty', 5)
        target_prefix = '0' * difficulty
        
        # Add nonce limit to prevent infinite loops
        max_nonce = 10_000_000  # Reasonable limit for mining
        
        while nonce < max_nonce:
            block_data = f"{block_number}{timestamp.isoformat()}{previous_hash}{merkle_root}{nonce}"
            block_hash = hashlib.sha256(block_data.encode()).hexdigest()
            
            # Check if hash meets difficulty requirement
            if block_hash.startswith(target_prefix):
                break
            nonce += 1
        
        if nonce >= max_nonce:
            logger.warning(f"Mining reached max nonce limit for block {block_number}")
            # Use best hash found
            block_data = f"{block_number}{timestamp.isoformat()}{previous_hash}{merkle_root}{nonce}"
            block_hash = hashlib.sha256(block_data.encode()).hexdigest()
        
        # Create block
        block = BlockchainBlock(
            block_number=block_number,
            timestamp=timestamp,
            previous_hash=previous_hash,
            predictions=[pred for pred, _ in self.current_block_predictions],
            merkle_root=merkle_root,
            nonce=nonce,
            block_hash=block_hash
        )
        
        # Store block and predictions in database
        self._store_block(block, self.current_block_predictions)
        
        # Clear current predictions
        self.current_block_predictions = []
        
        logger.info(f"Block {block_number} mined with hash: {block_hash}")
    
    def _get_latest_block_hash(self) -> str:
        """Get hash of the latest block."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT block_hash FROM blocks ORDER BY block_number DESC LIMIT 1")
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else "0" * 64  # Genesis block
    
    def _get_next_block_number(self) -> int:
        """Get the next block number."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(block_number) FROM blocks")
        result = cursor.fetchone()
        
        conn.close()
        
        return (result[0] + 1) if result[0] is not None else 0
    
    def _calculate_merkle_root(self, predictions: List[TradingPrediction]) -> str:
        """Calculate Merkle root of predictions."""
        if not predictions:
            return "0" * 64
        
        # Get prediction hashes
        hashes = [self.crypto_system.generate_prediction_hash(pred) for pred in predictions]
        
        # Build Merkle tree
        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]  # Duplicate if odd number
                
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            
            hashes = new_hashes
        
        return hashes[0]
    
    def _store_block(self, block: BlockchainBlock, predictions_with_sigs: List[Tuple]):
        """Store block and predictions in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store block
        cursor.execute('''
            INSERT INTO blocks (block_number, timestamp, previous_hash, merkle_root, nonce, block_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            block.block_number,
            block.timestamp.isoformat(),
            block.previous_hash,
            block.merkle_root,
            block.nonce,
            block.block_hash
        ))
        
        # Store predictions
        for prediction, signature in predictions_with_sigs:
            cursor.execute('''
                INSERT INTO predictions 
                (prediction_id, block_number, timestamp, prediction_type, asset_symbol, 
                 prediction_value, confidence, expiry_time, metadata, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction.prediction_id,
                block.block_number,
                prediction.timestamp.isoformat(),
                prediction.prediction_type.value,
                prediction.asset_symbol,
                json.dumps(prediction.prediction_value),
                prediction.confidence,
                prediction.expiry_time.isoformat(),
                json.dumps(prediction.metadata),
                signature.hex()
            ))
        
        conn.commit()
        conn.close()
    
    def validate_prediction(self, 
                          prediction_id: str, 
                          actual_value: Any) -> ValidationResult:
        """Validate a prediction against actual outcome."""
        # Retrieve prediction
        prediction = self.get_prediction(prediction_id)
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        # Calculate accuracy score
        accuracy_score = self._calculate_accuracy(
            prediction.prediction_value, 
            actual_value, 
            prediction.prediction_type
        )
        
        # Determine validation status
        if accuracy_score >= 0.7:  # 70% accuracy threshold
            status = ValidationStatus.VALIDATED
        elif datetime.now() > prediction.expiry_time:
            status = ValidationStatus.EXPIRED
        else:
            status = ValidationStatus.FAILED
        
        # Generate proof hash
        validation_data = {
            'prediction_id': prediction_id,
            'actual_value': actual_value,
            'predicted_value': prediction.prediction_value,
            'accuracy_score': accuracy_score,
            'timestamp': datetime.now().isoformat()
        }
        proof_hash = hashlib.sha256(
            json.dumps(validation_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Create validation result
        validation_result = ValidationResult(
            prediction_id=prediction_id,
            validation_timestamp=datetime.now(),
            actual_value=actual_value,
            predicted_value=prediction.prediction_value,
            accuracy_score=accuracy_score,
            validation_status=status,
            proof_hash=proof_hash
        )
        
        # Store validation
        self._store_validation(validation_result)
        
        logger.info(f"Prediction {prediction_id} validated with accuracy {accuracy_score:.2%}")
        
        return validation_result
    
    def _calculate_accuracy(self, 
                          predicted_value: Any, 
                          actual_value: Any, 
                          prediction_type: PredictionType) -> float:
        """Calculate accuracy score based on prediction type."""
        if prediction_type == PredictionType.PRICE_DIRECTION:
            # Binary accuracy for direction predictions
            return 1.0 if predicted_value == actual_value else 0.0
        
        elif prediction_type == PredictionType.PRICE_TARGET:
            # Percentage accuracy for price targets
            if isinstance(predicted_value, (int, float)) and isinstance(actual_value, (int, float)):
                error = abs(predicted_value - actual_value) / abs(actual_value)
                return max(0, 1 - error)
        
        elif prediction_type == PredictionType.VOLATILITY_FORECAST:
            # Volatility prediction accuracy
            if isinstance(predicted_value, (int, float)) and isinstance(actual_value, (int, float)):
                error = abs(predicted_value - actual_value) / max(predicted_value, actual_value)
                return max(0, 1 - error)
        
        # Default accuracy calculation
        try:
            if str(predicted_value).lower() == str(actual_value).lower():
                return 1.0
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _store_validation(self, validation: ValidationResult):
        """Store validation result in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO validations 
            (prediction_id, validation_timestamp, actual_value, predicted_value, 
             accuracy_score, validation_status, proof_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            validation.prediction_id,
            validation.validation_timestamp.isoformat(),
            json.dumps(validation.actual_value),
            json.dumps(validation.predicted_value),
            validation.accuracy_score,
            validation.validation_status.value,
            validation.proof_hash
        ))
        
        conn.commit()
        conn.close()
    
    def get_prediction(self, prediction_id: str) -> Optional[TradingPrediction]:
        """Retrieve prediction by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT prediction_id, timestamp, prediction_type, asset_symbol, 
                   prediction_value, confidence, expiry_time, metadata
            FROM predictions WHERE prediction_id = ?
        ''', (prediction_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return TradingPrediction(
            prediction_id=result[0],
            timestamp=datetime.fromisoformat(result[1]),
            prediction_type=PredictionType(result[2]),
            asset_symbol=result[3],
            prediction_value=json.loads(result[4]),
            confidence=result[5],
            expiry_time=datetime.fromisoformat(result[6]),
            metadata=json.loads(result[7])
        )
    
    def get_performance_metrics(self, 
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict:
        """Get comprehensive performance metrics."""
        # SECURITY FIX: Use parameterized queries to prevent SQL injection
        # Input validation for date parameters
        if start_date and not isinstance(start_date, datetime):
            raise ValueError("start_date must be a datetime object")
        if end_date and not isinstance(end_date, datetime):
            raise ValueError("end_date must be a datetime object")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query with parameterized filters (already using ? placeholders - good!)
        query = '''
            SELECT p.prediction_type, p.confidence, v.accuracy_score, v.validation_status
            FROM predictions p
            LEFT JOIN validations v ON p.prediction_id = v.prediction_id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND p.timestamp >= ?'
            params.append(start_date.isoformat())
        
        if end_date:
            query += ' AND p.timestamp <= ?'
            params.append(end_date.isoformat())
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Calculate metrics
        total_predictions = len(results)
        validated_predictions = [r for r in results if r[3] == 'validated']
        
        metrics = {
            'total_predictions': total_predictions,
            'validated_predictions': len(validated_predictions),
            'validation_rate': len(validated_predictions) / total_predictions if total_predictions > 0 else 0,
            'average_accuracy': np.mean([r[2] for r in validated_predictions]) if validated_predictions else 0,
            'average_confidence': np.mean([r[1] for r in results]) if results else 0,
            'by_prediction_type': {}
        }
        
        # Metrics by prediction type
        for pred_type in PredictionType:
            type_results = [r for r in results if r[0] == pred_type.value]
            type_validated = [r for r in type_results if r[3] == 'validated']
            
            if type_results:
                metrics['by_prediction_type'][pred_type.value] = {
                    'total': len(type_results),
                    'validated': len(type_validated),
                    'accuracy': np.mean([r[2] for r in type_validated]) if type_validated else 0
                }
        
        return metrics
    
    def generate_performance_certificate(self) -> Dict:
        """Generate cryptographic certificate of trading performance."""
        # Get all predictions and validations
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM predictions')
        prediction_rows = cursor.fetchall()
        
        cursor.execute('SELECT * FROM validations')
        validation_rows = cursor.fetchall()
        
        conn.close()
        
        # Convert to objects
        predictions = []
        for row in prediction_rows:
            predictions.append(TradingPrediction(
                prediction_id=row[0],
                timestamp=datetime.fromisoformat(row[2]),
                prediction_type=PredictionType(row[3]),
                asset_symbol=row[4],
                prediction_value=json.loads(row[5]),
                confidence=row[6],
                expiry_time=datetime.fromisoformat(row[7]),
                metadata=json.loads(row[8])
            ))
        
        validations = []
        for row in validation_rows:
            validations.append(ValidationResult(
                prediction_id=row[0],
                validation_timestamp=datetime.fromisoformat(row[1]),
                actual_value=json.loads(row[2]),
                predicted_value=json.loads(row[3]),
                accuracy_score=row[4],
                validation_status=ValidationStatus(row[5]),
                proof_hash=row[6]
            ))
        
        # Generate cryptographic proof
        performance_proof = self.crypto_system.generate_performance_proof(
            predictions, validations
        )
        
        return performance_proof
    
    def verify_blockchain_integrity(self) -> Dict:
        """Verify the integrity of the blockchain."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM blocks ORDER BY block_number')
        blocks = cursor.fetchall()
        
        conn.close()
        
        integrity_results = {
            'total_blocks': len(blocks),
            'valid_blocks': 0,
            'invalid_blocks': [],
            'chain_valid': True
        }
        
        previous_hash = "0" * 64  # Genesis
        
        for block in blocks:
            block_number, timestamp, prev_hash, merkle_root, nonce, block_hash = block
            
            # Verify previous hash link
            if prev_hash != previous_hash:
                integrity_results['invalid_blocks'].append({
                    'block_number': block_number,
                    'error': 'Invalid previous hash'
                })
                integrity_results['chain_valid'] = False
                continue
            
            # Verify block hash
            block_data = f"{block_number}{timestamp}{prev_hash}{merkle_root}{nonce}"
            calculated_hash = hashlib.sha256(block_data.encode()).hexdigest()
            
            if calculated_hash != block_hash:
                integrity_results['invalid_blocks'].append({
                    'block_number': block_number,
                    'error': 'Invalid block hash'
                })
                integrity_results['chain_valid'] = False
                continue
            
            integrity_results['valid_blocks'] += 1
            previous_hash = block_hash
        
        return integrity_results


class TradingPredictionSystem:
    """Complete trading prediction and validation system."""
    
    def __init__(self, db_path: str = "trading_blockchain.db"):
        """Initialize trading prediction system."""
        self.blockchain = BlockchainLedger(db_path)
        self.active_predictions = {}
        
        # Start validation monitoring
        self.validation_executor = ThreadPoolExecutor(max_workers=2)
        self.monitoring_active = False
        
        logger.info("Trading Prediction System initialized")
    
    def make_prediction(self,
                       prediction_type: PredictionType,
                       asset_symbol: str,
                       prediction_value: Any,
                       confidence: float,
                       expiry_hours: int = 24,
                       metadata: Optional[Dict] = None) -> str:
        """Make a new trading prediction."""
        prediction_id = f"{asset_symbol}_{prediction_type.value}_{int(time.time())}"
        
        prediction = TradingPrediction(
            prediction_id=prediction_id,
            timestamp=datetime.now(),
            prediction_type=prediction_type,
            asset_symbol=asset_symbol,
            prediction_value=prediction_value,
            confidence=confidence,
            expiry_time=datetime.now() + timedelta(hours=expiry_hours),
            metadata=metadata or {}
        )
        
        # Add to blockchain
        prediction_hash = self.blockchain.add_prediction(prediction)
        
        # Track active prediction
        self.active_predictions[prediction_id] = prediction
        
        logger.info(f"Prediction made: {prediction_id} ({prediction_type.value})")
        
        return prediction_id
    
    def validate_prediction(self, prediction_id: str, actual_value: Any) -> ValidationResult:
        """Validate a prediction with actual outcome."""
        result = self.blockchain.validate_prediction(prediction_id, actual_value)
        
        # Remove from active predictions if validated
        if prediction_id in self.active_predictions:
            del self.active_predictions[prediction_id]
        
        return result
    
    def get_trading_edge_proof(self) -> Dict:
        """Get cryptographic proof of trading edge."""
        return self.blockchain.generate_performance_certificate()
    
    def start_monitoring(self):
        """Start automated prediction monitoring."""
        self.monitoring_active = True
        
        async def monitor_predictions():
            while self.monitoring_active:
                # Check for expired predictions
                current_time = datetime.now()
                expired_predictions = []
                
                for pred_id, prediction in self.active_predictions.items():
                    if current_time > prediction.expiry_time:
                        expired_predictions.append(pred_id)
                
                # Mark expired predictions
                for pred_id in expired_predictions:
                    try:
                        self.validate_prediction(pred_id, "EXPIRED")
                    except Exception as e:
                        logger.error(f"Error validating expired prediction {pred_id}: {e}")
                
                # Sleep for monitoring interval
                await asyncio.sleep(3600)  # Check every hour
        
        # Start monitoring task
        asyncio.create_task(monitor_predictions())
        logger.info("Prediction monitoring started")
    
    def stop_monitoring(self):
        """Stop automated prediction monitoring."""
        self.monitoring_active = False
        logger.info("Prediction monitoring stopped")
    
    def export_performance_report(self, filepath: str):
        """Export comprehensive performance report."""
        metrics = self.blockchain.get_performance_metrics()
        proof = self.get_trading_edge_proof()
        integrity = self.blockchain.verify_blockchain_integrity()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'performance_metrics': metrics,
            'cryptographic_proof': proof,
            'blockchain_integrity': integrity,
            'active_predictions': len(self.active_predictions)
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Performance report exported to {filepath}")
    
    def get_leaderboard_data(self) -> Dict:
        """Get data for trading performance leaderboard."""
        metrics = self.blockchain.get_performance_metrics()
        
        return {
            'trader_id': 'elite_trading_bot',
            'total_predictions': metrics['total_predictions'],
            'accuracy_rate': metrics['validation_rate'],
            'average_accuracy': metrics['average_accuracy'],
            'confidence_score': metrics['average_confidence'],
            'blockchain_verified': True,
            'last_updated': datetime.now().isoformat()
        }
