"""
Blockchain Trade Verification System
Provides immutable verification and audit trail for trading decisions and executions
"""

import hashlib
import json
import time
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import os
import base64
import uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, load_pem_public_key,
    Encoding, PrivateFormat, PublicFormat, NoEncryption
)

logger = logging.getLogger(__name__)


class Block:
    """Block in the blockchain"""
    
    def __init__(self, index, timestamp, data, previous_hash):
        """Initialize a new block"""
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate hash of the block"""
        # Convert block data to string
        block_string = json.dumps(self._serialize_for_hash(), sort_keys=True)
        # Calculate hash
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        """Mine block with proof of work"""
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        logger.debug(f"Block mined: {self.hash}")
    
    def _serialize_for_hash(self):
        """Serialize block for hashing"""
        # Handle datetime objects for JSON serialization
        serialized_data = self._recursive_serialize(self.data)
        
        return {
            'index': self.index,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'data': serialized_data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }
    
    def _recursive_serialize(self, obj):
        """Recursively serialize objects for JSON"""
        if isinstance(obj, dict):
            return {k: self._recursive_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._recursive_serialize(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)


class TradeBlockchain:
    """Blockchain for trade verification"""
    
    def __init__(self, difficulty=4):
        """Initialize the blockchain"""
        self.chain = []
        self.difficulty = difficulty
        self.pending_transactions = []
        self.keys = self._generate_or_load_keys()
        
        # Create genesis block if chain is empty
        if not self.chain:
            self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the genesis block"""
        genesis_block = Block(0, datetime.now(), {"message": "Genesis Block"}, "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        logger.info("Genesis block created")
    
    def get_latest_block(self):
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    async def add_transaction(self, transaction_data):
        """Add a transaction to pending transactions"""
        # Add timestamp if not present
        if 'timestamp' not in transaction_data:
            transaction_data['timestamp'] = datetime.now()
        
        # Add transaction ID if not present
        if 'transaction_id' not in transaction_data:
            transaction_id = str(uuid.uuid4())
            transaction_data['transaction_id'] = transaction_id
        
        # Add digital signature
        signature = self._sign_data(transaction_data)
        transaction_data['signature'] = signature
        
        # Add to pending transactions
        self.pending_transactions.append(transaction_data)
        logger.debug(f"Transaction added: {transaction_data['transaction_id']}")
        
        # Mine block if enough transactions
        if len(self.pending_transactions) >= 5:
            await self.mine_pending_transactions()
        
        return transaction_data['transaction_id']
    
    async def mine_pending_transactions(self):
        """Mine pending transactions into a block"""
        if not self.pending_transactions:
            logger.debug("No pending transactions to mine")
            return False
        
        # Create new block
        new_block = Block(
            len(self.chain),
            datetime.now(),
            self.pending_transactions,
            self.get_latest_block().hash
        )
        
        # Mine block
        logger.info("Mining new block...")
        new_block.mine_block(self.difficulty)
        
        # Add block to chain
        self.chain.append(new_block)
        
        # Clear pending transactions
        self.pending_transactions = []
        
        # Save blockchain
        self._save_blockchain()
        
        logger.info(f"Block mined and added to chain: {new_block.hash}")
        return True
    
    def is_chain_valid(self):
        """Validate the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check hash
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Invalid hash for block {current_block.index}")
                return False
            
            # Check previous hash
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Invalid previous hash for block {current_block.index}")
                return False
        
        logger.info("Blockchain is valid")
        return True
    
    def get_transaction(self, transaction_id):
        """Get transaction by ID"""
        # Check pending transactions
        for transaction in self.pending_transactions:
            if transaction.get('transaction_id') == transaction_id:
                return {'status': 'pending', 'transaction': transaction}
        
        # Check blocks
        for block in reversed(self.chain):
            for transaction in block.data:
                if isinstance(transaction, dict) and transaction.get('transaction_id') == transaction_id:
                    return {
                        'status': 'confirmed',
                        'transaction': transaction,
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'timestamp': block.timestamp
                    }
        
        return {'status': 'not_found'}
    
    def get_transactions_by_symbol(self, symbol):
        """Get all transactions for a symbol"""
        transactions = []
        
        # Check blocks
        for block in self.chain:
            for transaction in block.data:
                if isinstance(transaction, dict) and transaction.get('symbol') == symbol:
                    transactions.append({
                        'transaction': transaction,
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'timestamp': block.timestamp
                    })
        
        # Check pending transactions
        for transaction in self.pending_transactions:
            if transaction.get('symbol') == symbol:
                transactions.append({
                    'transaction': transaction,
                    'status': 'pending'
                })
        
        return transactions
    
    def verify_transaction(self, transaction_data, signature):
        """Verify transaction signature"""
        try:
            # Create a copy without the signature
            data_to_verify = transaction_data.copy()
            if 'signature' in data_to_verify:
                del data_to_verify['signature']
            
            # Convert to string
            data_string = json.dumps(self._recursive_serialize(data_to_verify), sort_keys=True)
            
            # Verify signature
            signature_bytes = base64.b64decode(signature)
            self.keys['public_key'].verify(
                signature_bytes,
                data_string.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def _sign_data(self, data):
        """Sign data with private key"""
        try:
            # Create a copy without the signature
            data_to_sign = data.copy()
            if 'signature' in data_to_sign:
                del data_to_sign['signature']
            
            # Convert to string
            data_string = json.dumps(self._recursive_serialize(data_to_sign), sort_keys=True)
            
            # Sign data
            signature = self.keys['private_key'].sign(
                data_string.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode()
        except Exception as e:
            logger.error(f"Error signing data: {e}")
            return ""
    
    def _generate_or_load_keys(self):
        """Generate or load RSA keys"""
        key_dir = "keys"
        private_key_path = os.path.join(key_dir, "private_key.pem")
        public_key_path = os.path.join(key_dir, "public_key.pem")
        
        # Create directory if it doesn't exist
        os.makedirs(key_dir, exist_ok=True)
        
        # Check if keys exist
        if os.path.exists(private_key_path) and os.path.exists(public_key_path):
            # Load keys
            with open(private_key_path, "rb") as f:
                private_key = load_pem_private_key(f.read(), password=None)
            
            with open(public_key_path, "rb") as f:
                public_key = load_pem_public_key(f.read())
            
            logger.info("RSA keys loaded")
        else:
            # Generate keys
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Save keys
            with open(private_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,
                    encryption_algorithm=NoEncryption()
                ))
            
            with open(public_key_path, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=Encoding.PEM,
                    format=PublicFormat.SubjectPublicKeyInfo
                ))
            
            logger.info("RSA keys generated")
        
        return {'private_key': private_key, 'public_key': public_key}
    
    def _save_blockchain(self):
        """Save blockchain to file"""
        blockchain_dir = "blockchain"
        os.makedirs(blockchain_dir, exist_ok=True)
        
        # Serialize blockchain
        serialized_chain = []
        for block in self.chain:
            serialized_block = {
                'index': block.index,
                'timestamp': block.timestamp.isoformat() if isinstance(block.timestamp, datetime) else block.timestamp,
                'data': self._recursive_serialize(block.data),
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            }
            serialized_chain.append(serialized_block)
        
        # Save to file
        with open(os.path.join(blockchain_dir, "blockchain.json"), "w") as f:
            json.dump(serialized_chain, f, indent=2)
        
        logger.debug("Blockchain saved to file")
    
    def _load_blockchain(self):
        """Load blockchain from file"""
        blockchain_dir = "blockchain"
        blockchain_file = os.path.join(blockchain_dir, "blockchain.json")
        
        if not os.path.exists(blockchain_file):
            logger.info("No blockchain file found, creating genesis block")
            self._create_genesis_block()
            return
        
        try:
            with open(blockchain_file, "r") as f:
                serialized_chain = json.load(f)
            
            # Deserialize blockchain
            self.chain = []
            for serialized_block in serialized_chain:
                # Convert timestamp to datetime
                if isinstance(serialized_block['timestamp'], str):
                    serialized_block['timestamp'] = datetime.fromisoformat(serialized_block['timestamp'])
                
                # Create block
                block = Block(
                    serialized_block['index'],
                    serialized_block['timestamp'],
                    serialized_block['data'],
                    serialized_block['previous_hash']
                )
                block.hash = serialized_block['hash']
                block.nonce = serialized_block['nonce']
                
                self.chain.append(block)
            
            logger.info(f"Blockchain loaded from file: {len(self.chain)} blocks")
        except Exception as e:
            logger.error(f"Error loading blockchain: {e}")
            self._create_genesis_block()
    
    def _recursive_serialize(self, obj):
        """Recursively serialize objects for JSON"""
        if isinstance(obj, dict):
            return {k: self._recursive_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._recursive_serialize(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)


class TradeVerificationSystem:
    """Trade verification system using blockchain"""
    
    def __init__(self, config: Dict = None):
        """Initialize the trade verification system"""
        self.config = config or {}
        self.blockchain = TradeBlockchain(difficulty=self.config.get('difficulty', 4))
        
        # Load blockchain
        self.blockchain._load_blockchain()
        
        # Start background mining task
        self.mining_task = None
        self.mining_interval = self.config.get('mining_interval_seconds', 300)  # 5 minutes
        
        logger.info("Trade Verification System initialized")
    
    async def start_mining_task(self):
        """Start background mining task"""
        if self.mining_task is not None:
            logger.warning("Mining task already running")
            return
        
        self.mining_task = asyncio.create_task(self._mining_loop())
        logger.info("Mining task started")
    
    async def stop_mining_task(self):
        """Stop background mining task"""
        if self.mining_task is None:
            logger.warning("No mining task running")
            return
        
        self.mining_task.cancel()
        try:
            await self.mining_task
        except asyncio.CancelledError:
            pass
        
        self.mining_task = None
        logger.info("Mining task stopped")
    
    async def _mining_loop(self):
        """Background mining loop"""
        try:
            while True:
                # Mine pending transactions
                await self.blockchain.mine_pending_transactions()
                
                # Wait for next mining interval
                await asyncio.sleep(self.mining_interval)
        except asyncio.CancelledError:
            logger.info("Mining loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in mining loop: {e}")
    
    async def verify_trade(self, trade_data: Dict) -> Dict:
        """
        Verify a trade and add it to the blockchain
        
        Args:
            trade_data: Trade data to verify
            
        Returns:
            Dictionary with verification result
        """
        # Add trade to blockchain
        transaction_id = await self.blockchain.add_transaction(trade_data)
        
        logger.info(f"Trade verified and added to blockchain: {transaction_id}")
        
        return {
            'status': 'verified',
            'transaction_id': transaction_id
        }
    
    async def get_trade_verification(self, transaction_id: str) -> Dict:
        """
        Get trade verification details
        
        Args:
            transaction_id: Transaction ID to look up
            
        Returns:
            Dictionary with verification details
        """
        result = self.blockchain.get_transaction(transaction_id)
        
        if result['status'] == 'not_found':
            logger.warning(f"Transaction not found: {transaction_id}")
        else:
            logger.info(f"Transaction found: {transaction_id}, status: {result['status']}")
        
        return result
    
    async def get_trades_by_symbol(self, symbol: str) -> List[Dict]:
        """
        Get all trades for a symbol
        
        Args:
            symbol: Symbol to look up
            
        Returns:
            List of trades for the symbol
        """
        transactions = self.blockchain.get_transactions_by_symbol(symbol)
        
        logger.info(f"Found {len(transactions)} transactions for symbol {symbol}")
        
        return transactions
    
    async def verify_blockchain(self) -> Dict:
        """
        Verify the integrity of the blockchain
        
        Returns:
            Dictionary with verification result
        """
        is_valid = self.blockchain.is_chain_valid()
        
        if is_valid:
            logger.info("Blockchain integrity verified")
            return {'status': 'valid', 'blocks': len(self.blockchain.chain)}
        else:
            logger.error("Blockchain integrity check failed")
            return {'status': 'invalid', 'blocks': len(self.blockchain.chain)}
    
    async def generate_audit_report(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Generate audit report for trades
        
        Args:
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            Dictionary with audit report
        """
        # Default to last 24 hours if no dates provided
        if start_date is None:
            start_date = datetime.now() - timedelta(days=1)
        
        if end_date is None:
            end_date = datetime.now()
        
        # Collect transactions within date range
        transactions = []
        
        for block in self.blockchain.chain:
            # Skip if block timestamp is outside date range
            block_time = block.timestamp
            if isinstance(block_time, str):
                block_time = datetime.fromisoformat(block_time)
            
            if block_time < start_date or block_time > end_date:
                continue
            
            for transaction in block.data:
                if isinstance(transaction, dict):
                    # Check transaction timestamp if available
                    tx_time = transaction.get('timestamp')
                    if isinstance(tx_time, str):
                        tx_time = datetime.fromisoformat(tx_time)
                    
                    if tx_time and (tx_time < start_date or tx_time > end_date):
                        continue
                    
                    transactions.append({
                        'transaction': transaction,
                        'block_index': block.index,
                        'block_hash': block.hash,
                        'timestamp': block_time
                    })
        
        # Generate report
        report = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_transactions': len(transactions),
            'transactions': transactions,
            'blockchain_status': 'valid' if self.blockchain.is_chain_valid() else 'invalid',
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Audit report generated: {len(transactions)} transactions")
        
        return report
