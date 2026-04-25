"""
Governance Token System

Reputation and stake tracking for agents in the governance system.
Implements token-based voting power and delegation.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Types of governance tokens."""
    VOTING = "voting"
    STAKING = "staking"
    REPUTATION = "reputation"
    DELEGATION = "delegation"


class TransactionType(Enum):
    """Types of token transactions."""
    MINT = "mint"
    BURN = "burn"
    TRANSFER = "transfer"
    STAKE = "stake"
    UNSTAKE = "unstake"
    DELEGATE = "delegate"
    UNDELEGATE = "undelegate"
    REWARD = "reward"
    SLASH = "slash"


@dataclass
class TokenTransaction:
    """A token transaction record."""
    transaction_id: str
    transaction_type: TransactionType
    from_holder: Optional[str]
    to_holder: Optional[str]
    amount: float
    token_type: TokenType
    timestamp: datetime
    reason: str
    block_number: int
    signature: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type.value,
            'from_holder': self.from_holder,
            'to_holder': self.to_holder,
            'amount': self.amount,
            'token_type': self.token_type.value,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'block_number': self.block_number,
            'signature': self.signature,
        }


@dataclass
class VotingPower:
    """Voting power breakdown for a holder."""
    holder_id: str
    base_power: float
    staked_power: float
    delegated_power: float
    reputation_multiplier: float
    total_power: float
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'holder_id': self.holder_id,
            'base_power': self.base_power,
            'staked_power': self.staked_power,
            'delegated_power': self.delegated_power,
            'reputation_multiplier': self.reputation_multiplier,
            'total_power': self.total_power,
            'last_updated': self.last_updated.isoformat(),
        }


@dataclass
class TokenHolder:
    """A holder of governance tokens."""
    holder_id: str
    name: str
    balance: float
    staked_balance: float
    delegated_to: Optional[str]
    delegated_from: List[str]
    reputation_score: float
    voting_power: VotingPower
    created_at: datetime
    last_activity: Optional[datetime] = None
    is_active: bool = True
    total_rewards: float = 0.0
    total_slashed: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'holder_id': self.holder_id,
            'name': self.name,
            'balance': self.balance,
            'staked_balance': self.staked_balance,
            'delegated_to': self.delegated_to,
            'delegated_from': self.delegated_from,
            'reputation_score': self.reputation_score,
            'voting_power': self.voting_power.to_dict(),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'total_rewards': self.total_rewards,
            'total_slashed': self.total_slashed,
        }


@dataclass
class DelegationRecord:
    """Record of token delegation."""
    delegation_id: str
    delegator_id: str
    delegatee_id: str
    amount: float
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'delegation_id': self.delegation_id,
            'delegator_id': self.delegator_id,
            'delegatee_id': self.delegatee_id,
            'amount': self.amount,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
        }


class GovernanceToken:
    """
    Governance token system for voting power and reputation.
    
    Provides:
    - Token minting and burning
    - Staking and unstaking
    - Delegation of voting power
    - Reputation tracking
    - Reward distribution
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'governance_token_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._holders: Dict[str, TokenHolder] = {}
        self._transactions: List[TokenTransaction] = []
        self._delegations: Dict[str, DelegationRecord] = {}
        
        self._token_config = {
            'total_supply': 1000000.0,
            'circulating_supply': 0.0,
            'staking_reward_rate': 0.05,
            'minimum_stake': 100.0,
            'unstaking_period_hours': 24,
            'delegation_fee_percent': 1.0,
            'reputation_decay_rate': 0.001,
            'max_delegation_percent': 50.0,
        }
        
        self._block_number = 0
        self._treasury_balance = 100000.0
        
        logger.info("✅ Governance Token System initialized")
    
    async def create_holder(
        self,
        holder_id: str,
        name: str,
        initial_balance: float = 0.0,
    ) -> TokenHolder:
        """
        Create a new token holder.
        
        Args:
            holder_id: Unique identifier
            name: Holder name
            initial_balance: Initial token balance
        
        Returns:
            TokenHolder
        """
        if holder_id in self._holders:
            return self._holders[holder_id]
        
        voting_power = VotingPower(
            holder_id=holder_id,
            base_power=initial_balance,
            staked_power=0.0,
            delegated_power=0.0,
            reputation_multiplier=1.0,
            total_power=initial_balance,
            last_updated=datetime.now(timezone.utc),
        )
        
        holder = TokenHolder(
            holder_id=holder_id,
            name=name,
            balance=initial_balance,
            staked_balance=0.0,
            delegated_to=None,
            delegated_from=[],
            reputation_score=1.0,
            voting_power=voting_power,
            created_at=datetime.now(timezone.utc),
        )
        
        self._holders[holder_id] = holder
        
        if initial_balance > 0:
            await self._record_transaction(
                TransactionType.MINT,
                None,
                holder_id,
                initial_balance,
                TokenType.VOTING,
                "Initial token allocation"
            )
            self._token_config['circulating_supply'] += initial_balance
        
        await self._persist_holder(holder)
        
        logger.info(f"Created token holder: {name} (balance: {initial_balance})")
        
        return holder
    
    async def mint_tokens(
        self,
        holder_id: str,
        amount: float,
        reason: str,
    ) -> bool:
        """
        Mint new tokens to a holder.
        
        Args:
            holder_id: ID of the recipient
            amount: Amount to mint
            reason: Reason for minting
        
        Returns:
            True if successful
        """
        if holder_id not in self._holders:
            return False
        
        if self._token_config['circulating_supply'] + amount > self._token_config['total_supply']:
            logger.warning("Cannot mint: would exceed total supply")
            return False
        
        holder = self._holders[holder_id]
        holder.balance += amount
        holder.last_activity = datetime.now(timezone.utc)
        
        self._token_config['circulating_supply'] += amount
        
        await self._update_voting_power(holder)
        await self._record_transaction(
            TransactionType.MINT,
            None,
            holder_id,
            amount,
            TokenType.VOTING,
            reason
        )
        
        await self._persist_holder(holder)
        
        return True
    
    async def burn_tokens(
        self,
        holder_id: str,
        amount: float,
        reason: str,
    ) -> bool:
        """
        Burn tokens from a holder.
        
        Args:
            holder_id: ID of the holder
            amount: Amount to burn
            reason: Reason for burning
        
        Returns:
            True if successful
        """
        if holder_id not in self._holders:
            return False
        
        holder = self._holders[holder_id]
        
        if holder.balance < amount:
            return False
        
        holder.balance -= amount
        holder.last_activity = datetime.now(timezone.utc)
        
        self._token_config['circulating_supply'] -= amount
        
        await self._update_voting_power(holder)
        await self._record_transaction(
            TransactionType.BURN,
            holder_id,
            None,
            amount,
            TokenType.VOTING,
            reason
        )
        
        await self._persist_holder(holder)
        
        return True
    
    async def transfer_tokens(
        self,
        from_holder_id: str,
        to_holder_id: str,
        amount: float,
        reason: str,
    ) -> bool:
        """
        Transfer tokens between holders.
        
        Args:
            from_holder_id: Sender ID
            to_holder_id: Recipient ID
            amount: Amount to transfer
            reason: Reason for transfer
        
        Returns:
            True if successful
        """
        if from_holder_id not in self._holders or to_holder_id not in self._holders:
            return False
        
        from_holder = self._holders[from_holder_id]
        to_holder = self._holders[to_holder_id]
        
        if from_holder.balance < amount:
            return False
        
        from_holder.balance -= amount
        to_holder.balance += amount
        
        from_holder.last_activity = datetime.now(timezone.utc)
        to_holder.last_activity = datetime.now(timezone.utc)
        
        await self._update_voting_power(from_holder)
        await self._update_voting_power(to_holder)
        
        await self._record_transaction(
            TransactionType.TRANSFER,
            from_holder_id,
            to_holder_id,
            amount,
            TokenType.VOTING,
            reason
        )
        
        await self._persist_holder(from_holder)
        await self._persist_holder(to_holder)
        
        return True
    
    async def stake_tokens(
        self,
        holder_id: str,
        amount: float,
    ) -> bool:
        """
        Stake tokens for increased voting power.
        
        Args:
            holder_id: ID of the holder
            amount: Amount to stake
        
        Returns:
            True if successful
        """
        if holder_id not in self._holders:
            return False
        
        holder = self._holders[holder_id]
        
        if holder.balance < amount:
            return False
        
        if amount < self._token_config['minimum_stake']:
            return False
        
        holder.balance -= amount
        holder.staked_balance += amount
        holder.last_activity = datetime.now(timezone.utc)
        
        await self._update_voting_power(holder)
        await self._record_transaction(
            TransactionType.STAKE,
            holder_id,
            holder_id,
            amount,
            TokenType.STAKING,
            "Tokens staked for governance"
        )
        
        await self._persist_holder(holder)
        
        logger.info(f"Holder {holder_id} staked {amount} tokens")
        
        return True
    
    async def unstake_tokens(
        self,
        holder_id: str,
        amount: float,
    ) -> bool:
        """
        Unstake tokens (subject to unstaking period).
        
        Args:
            holder_id: ID of the holder
            amount: Amount to unstake
        
        Returns:
            True if successful
        """
        if holder_id not in self._holders:
            return False
        
        holder = self._holders[holder_id]
        
        if holder.staked_balance < amount:
            return False
        
        holder.staked_balance -= amount
        holder.balance += amount
        holder.last_activity = datetime.now(timezone.utc)
        
        await self._update_voting_power(holder)
        await self._record_transaction(
            TransactionType.UNSTAKE,
            holder_id,
            holder_id,
            amount,
            TokenType.STAKING,
            "Tokens unstaked"
        )
        
        await self._persist_holder(holder)
        
        return True
    
    async def delegate_voting_power(
        self,
        delegator_id: str,
        delegatee_id: str,
        amount: Optional[float] = None,
        duration_hours: Optional[int] = None,
    ) -> Optional[DelegationRecord]:
        """
        Delegate voting power to another holder.
        
        Args:
            delegator_id: ID of the delegator
            delegatee_id: ID of the delegatee
            amount: Amount to delegate (None = all)
            duration_hours: Duration of delegation
        
        Returns:
            DelegationRecord if successful
        """
        if delegator_id not in self._holders or delegatee_id not in self._holders:
            return None
        
        if delegator_id == delegatee_id:
            return None
        
        delegator = self._holders[delegator_id]
        delegatee = self._holders[delegatee_id]
        
        if delegator.delegated_to is not None:
            return None
        
        max_delegation = delegator.voting_power.total_power * (
            self._token_config['max_delegation_percent'] / 100
        )
        
        amount = amount or delegator.voting_power.total_power
        amount = min(amount, max_delegation)
        
        delegation_id = f"DEL-{uuid.uuid4().hex[:12]}"
        
        expires_at = None
        if duration_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        delegation = DelegationRecord(
            delegation_id=delegation_id,
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            amount=amount,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_active=True,
        )
        
        delegator.delegated_to = delegatee_id
        delegatee.delegated_from.append(delegator_id)
        
        self._delegations[delegation_id] = delegation
        
        await self._update_voting_power(delegator)
        await self._update_voting_power(delegatee)
        
        await self._record_transaction(
            TransactionType.DELEGATE,
            delegator_id,
            delegatee_id,
            amount,
            TokenType.DELEGATION,
            f"Voting power delegated for {duration_hours}h" if duration_hours else "Voting power delegated"
        )
        
        await self._persist_holder(delegator)
        await self._persist_holder(delegatee)
        
        logger.info(f"Delegation: {delegator_id} -> {delegatee_id} ({amount} power)")
        
        return delegation
    
    async def undelegate_voting_power(
        self,
        delegator_id: str,
    ) -> bool:
        """
        Remove delegation of voting power.
        
        Args:
            delegator_id: ID of the delegator
        
        Returns:
            True if successful
        """
        if delegator_id not in self._holders:
            return False
        
        delegator = self._holders[delegator_id]
        
        if delegator.delegated_to is None:
            return False
        
        delegatee_id = delegator.delegated_to
        delegatee = self._holders.get(delegatee_id)
        
        delegation = next(
            (d for d in self._delegations.values() 
             if d.delegator_id == delegator_id and d.is_active),
            None
        )
        
        if delegation:
            delegation.is_active = False
        
        delegator.delegated_to = None
        if delegatee and delegator_id in delegatee.delegated_from:
            delegatee.delegated_from.remove(delegator_id)
        
        await self._update_voting_power(delegator)
        if delegatee:
            await self._update_voting_power(delegatee)
        
        await self._record_transaction(
            TransactionType.UNDELEGATE,
            delegator_id,
            delegatee_id,
            delegation.amount if delegation else 0,
            TokenType.DELEGATION,
            "Voting power undelegated"
        )
        
        await self._persist_holder(delegator)
        if delegatee:
            await self._persist_holder(delegatee)
        
        return True
    
    async def distribute_rewards(
        self,
        total_reward: float,
        distribution_type: str = "proportional",
    ) -> Dict[str, float]:
        """
        Distribute rewards to stakers.
        
        Args:
            total_reward: Total reward to distribute
            distribution_type: How to distribute rewards
        
        Returns:
            Dict of holder_id -> reward amount
        """
        rewards = {}
        
        total_staked = sum(h.staked_balance for h in self._holders.values())
        
        if total_staked == 0:
            return rewards
        
        for holder in self._holders.values():
            if holder.staked_balance > 0:
                if distribution_type == "proportional":
                    share = holder.staked_balance / total_staked
                elif distribution_type == "equal":
                    stakers = [h for h in self._holders.values() if h.staked_balance > 0]
                    share = 1 / len(stakers)
                else:
                    share = holder.staked_balance / total_staked
                
                reward = total_reward * share
                holder.balance += reward
                holder.total_rewards += reward
                rewards[holder.holder_id] = reward
                
                await self._record_transaction(
                    TransactionType.REWARD,
                    None,
                    holder.holder_id,
                    reward,
                    TokenType.VOTING,
                    f"Staking reward ({distribution_type})"
                )
                
                await self._persist_holder(holder)
        
        logger.info(f"Distributed {total_reward} rewards to {len(rewards)} stakers")
        
        return rewards
    
    async def slash_holder(
        self,
        holder_id: str,
        amount: float,
        reason: str,
    ) -> bool:
        """
        Slash tokens from a holder as penalty.
        
        Args:
            holder_id: ID of the holder
            amount: Amount to slash
            reason: Reason for slashing
        
        Returns:
            True if successful
        """
        if holder_id not in self._holders:
            return False
        
        holder = self._holders[holder_id]
        
        slashed_from_staked = min(amount, holder.staked_balance)
        remaining = amount - slashed_from_staked
        slashed_from_balance = min(remaining, holder.balance)
        
        total_slashed = slashed_from_staked + slashed_from_balance
        
        holder.staked_balance -= slashed_from_staked
        holder.balance -= slashed_from_balance
        holder.total_slashed += total_slashed
        holder.reputation_score = max(0.1, holder.reputation_score - 0.1)
        
        await self._update_voting_power(holder)
        await self._record_transaction(
            TransactionType.SLASH,
            holder_id,
            None,
            total_slashed,
            TokenType.VOTING,
            reason
        )
        
        await self._persist_holder(holder)
        
        logger.warning(f"Slashed {total_slashed} from holder {holder_id}: {reason}")
        
        return True
    
    async def _update_voting_power(self, holder: TokenHolder):
        """Update voting power for a holder."""
        base_power = holder.balance
        staked_power = holder.staked_balance * 1.5
        
        delegated_power = 0.0
        for delegator_id in holder.delegated_from:
            delegation = next(
                (d for d in self._delegations.values() 
                 if d.delegator_id == delegator_id and d.is_active),
                None
            )
            if delegation:
                delegated_power += delegation.amount
        
        if holder.delegated_to:
            base_power = 0
            staked_power = 0
        
        reputation_multiplier = 0.5 + (holder.reputation_score * 0.5)
        
        total_power = (base_power + staked_power + delegated_power) * reputation_multiplier
        
        holder.voting_power = VotingPower(
            holder_id=holder.holder_id,
            base_power=base_power,
            staked_power=staked_power,
            delegated_power=delegated_power,
            reputation_multiplier=reputation_multiplier,
            total_power=total_power,
            last_updated=datetime.now(timezone.utc),
        )
    
    async def _record_transaction(
        self,
        tx_type: TransactionType,
        from_holder: Optional[str],
        to_holder: Optional[str],
        amount: float,
        token_type: TokenType,
        reason: str,
    ):
        """Record a token transaction."""
        self._block_number += 1
        
        tx_id = f"TX-{uuid.uuid4().hex[:12]}"
        tx_data = f"{tx_id}:{tx_type.value}:{from_holder}:{to_holder}:{amount}:{self._block_number}"
        signature = hashlib.sha256(tx_data.encode()).hexdigest()
        
        transaction = TokenTransaction(
            transaction_id=tx_id,
            transaction_type=tx_type,
            from_holder=from_holder,
            to_holder=to_holder,
            amount=amount,
            token_type=token_type,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            block_number=self._block_number,
            signature=signature,
        )
        
        self._transactions.append(transaction)
    
    def get_holder(self, holder_id: str) -> Optional[TokenHolder]:
        """Get a token holder by ID."""
        return self._holders.get(holder_id)
    
    def get_voting_power(self, holder_id: str) -> Optional[VotingPower]:
        """Get voting power for a holder."""
        holder = self._holders.get(holder_id)
        return holder.voting_power if holder else None
    
    def get_total_voting_power(self) -> float:
        """Get total voting power in the system."""
        return sum(h.voting_power.total_power for h in self._holders.values())
    
    async def _persist_holder(self, holder: TokenHolder):
        """Persist holder to storage."""
        holder_file = self.storage_path / 'holders' / f"{holder.holder_id}.json"
        holder_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(holder_file, 'w') as f:
            json.dump(holder.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get token system statistics."""
        return {
            'total_supply': self._token_config['total_supply'],
            'circulating_supply': self._token_config['circulating_supply'],
            'total_holders': len(self._holders),
            'total_staked': sum(h.staked_balance for h in self._holders.values()),
            'total_delegations': len([d for d in self._delegations.values() if d.is_active]),
            'total_transactions': len(self._transactions),
            'current_block': self._block_number,
            'treasury_balance': self._treasury_balance,
        }
