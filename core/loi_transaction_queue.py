"""
LOI Transaction Queue Management System

High-performance priority queue for managing LOI processing workflow.
Supports priority scoring, batching, and real-time processing.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import heapq
import threading
import logging

logger = logging.getLogger(__name__)

class LOITransactionType(Enum):
    """Core LOI transaction types"""
    NEW_LOI_REQUEST = "new_loi_request"
    DOCUMENT_GENERATION = "document_generation"
    STORAGE_UPLOAD = "storage_upload"
    SIGNATURE_REQUEST = "signature_request"
    STATUS_UPDATE = "status_update"
    COMPLETION_NOTIFICATION = "completion_notification"

class LOITransactionStatus(Enum):
    """LOI transaction lifecycle states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_SIGNATURE = "waiting_signature"
    SIGNED = "signed"

class LOITransactionPriority(Enum):
    """Priority levels for LOI processing"""
    URGENT = 1          # VIP customers, time-sensitive deals
    HIGH = 2            # High-value deals, existing customers
    NORMAL = 3          # Standard LOI requests
    LOW = 4             # Bulk processing, non-urgent
    BACKGROUND = 5      # Cleanup, maintenance tasks

@dataclass
class LOITransaction:
    """Individual LOI transaction with processing metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: LOITransactionType = LOITransactionType.NEW_LOI_REQUEST
    priority: LOITransactionPriority = LOITransactionPriority.NORMAL
    status: LOITransactionStatus = LOITransactionStatus.PENDING
    
    # Core LOI data
    customer_data: Dict[str, Any] = field(default_factory=dict)
    crm_form_data: Dict[str, Any] = field(default_factory=dict)
    document_data: Dict[str, Any] = field(default_factory=dict)
    
    # Processing context
    workflow_stage: str = "initial"
    processing_context: Dict[str, Any] = field(default_factory=dict)
    
    # Document tracking
    document_id: Optional[str] = None
    google_drive_url: Optional[str] = None
    signature_request_id: Optional[str] = None
    
    # Processing insights
    complexity_score: float = 0.0
    estimated_processing_time: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    
    # Timing and tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Workflow dependencies
    parent_transaction_id: Optional[str] = None
    child_transaction_ids: List[str] = field(default_factory=list)
    dependency_ids: List[str] = field(default_factory=list)
    
    # Processing history
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __lt__(self, other):
        """Priority queue ordering: lower numbers = higher priority"""
        if not isinstance(other, LOITransaction):
            return NotImplemented
        
        # First by priority level
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        
        # Then by complexity score (higher complexity = higher priority for resource allocation)
        if self.complexity_score != other.complexity_score:
            return self.complexity_score > other.complexity_score
        
        # Finally by age (older first)
        return self.created_at < other.created_at
    
    def add_processing_event(self, event_type: str, event_data: Dict[str, Any]):
        """Record processing event for this transaction"""
        self.processing_history.append({
            'timestamp': datetime.now(),
            'event_type': event_type,
            'data': event_data
        })
    
    def add_error(self, error_type: str, error_message: str, error_details: Dict[str, Any] = None):
        """Record error for this transaction"""
        self.error_history.append({
            'timestamp': datetime.now(),
            'error_type': error_type,
            'message': error_message,
            'details': error_details or {}
        })
    
    def calculate_processing_duration(self) -> Optional[float]:
        """Calculate how long this transaction took to process"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_customer_info(self) -> Dict[str, Any]:
        """Extract customer information"""
        return {
            'company_name': self.customer_data.get('company_name', ''),
            'contact_name': self.customer_data.get('contact_name', ''),
            'email': self.customer_data.get('email', ''),
            'phone': self.customer_data.get('phone', ''),
            'is_vip': self.customer_data.get('is_vip_customer', False)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for processing"""
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'customer_data': self.customer_data,
            'crm_form_data': self.crm_form_data,
            'document_data': self.document_data,
            'workflow_stage': self.workflow_stage,
            'complexity_score': self.complexity_score,
            'risk_factors': self.risk_factors,
            'created_at': self.created_at.isoformat(),
            'document_id': self.document_id,
            'google_drive_url': self.google_drive_url,
            'signature_request_id': self.signature_request_id
        }

class LOITransactionQueue:
    """High-performance priority queue for LOI processing workflow"""
    
    def __init__(self, max_size: int = 5000, batch_size: int = 25):
        self.max_size = max_size
        self.batch_size = batch_size
        
        # Thread-safe priority queue
        self._queue: List[LOITransaction] = []
        self._queue_lock = threading.Lock()
        
        # Quick lookups
        self._transactions: Dict[str, LOITransaction] = {}
        self._processing: Dict[str, LOITransaction] = {}
        self._completed: Dict[str, LOITransaction] = {}
        
        # Workflow tracking
        self._by_workflow_stage: Dict[str, List[str]] = {
            'initial': [],
            'document_generation': [],
            'storage_upload': [],
            'signature_pending': [],
            'completed': [],
            'failed': []
        }
        
        # Metrics
        self._total_processed = 0
        self._total_failed = 0
        self._average_processing_time = 0.0
        self._loi_completion_rate = 0.0
        
        # Event handlers
        self._on_transaction_added: Optional[Callable] = None
        self._on_transaction_completed: Optional[Callable] = None
        self._on_workflow_stage_changed: Optional[Callable] = None
        
        logger.info(f"🚀 LOI Transaction Queue initialized (max_size={max_size}, batch_size={batch_size})")
    
    def add_loi_transaction(self, transaction: LOITransaction) -> bool:
        """Add LOI transaction to priority queue"""
        with self._queue_lock:
            if len(self._queue) >= self.max_size:
                logger.warning(f"⚠️ LOI Queue at capacity ({self.max_size}), rejecting transaction {transaction.id}")
                return False
            
            # Calculate priority adjustments for LOI-specific factors
            self._adjust_loi_priority(transaction)
            
            # Add to queue and lookups
            heapq.heappush(self._queue, transaction)
            self._transactions[transaction.id] = transaction
            
            # Track by workflow stage
            self._by_workflow_stage[transaction.workflow_stage].append(transaction.id)
            
            logger.info(f"📥 Added LOI transaction {transaction.id} "
                       f"(type={transaction.type.value}, priority={transaction.priority.value}, "
                       f"customer={transaction.get_customer_info()['company_name']})")
            
            # Trigger event handler
            if self._on_transaction_added:
                try:
                    self._on_transaction_added(transaction)
                except Exception as e:
                    logger.error(f"❌ Error in transaction_added handler: {e}")
            
            return True
    
    def _adjust_loi_priority(self, transaction: LOITransaction):
        """Adjust priority based on LOI-specific business rules"""
        
        customer_info = transaction.get_customer_info()
        
        # VIP customer priority boost
        if customer_info.get('is_vip'):
            if transaction.priority.value > LOITransactionPriority.HIGH.value:
                transaction.priority = LOITransactionPriority.HIGH
                logger.info(f"👑 VIP customer priority boost for {transaction.id}")
        
        # High-value deal priority boost
        fuel_data = transaction.crm_form_data
        monthly_volume = (fuel_data.get('monthly_gasoline_volume', 0) + 
                         fuel_data.get('monthly_diesel_volume', 0))
        
        if monthly_volume > 50000:  # High volume threshold
            if transaction.priority.value > LOITransactionPriority.HIGH.value:
                transaction.priority = LOITransactionPriority.HIGH
                logger.info(f"📈 High-volume deal priority boost for {transaction.id}")
        
        # Urgency based on conversion date
        if 'estimated_conversion_date' in fuel_data:
            # If conversion date is soon, increase priority
            try:
                conversion_date = datetime.fromisoformat(fuel_data['estimated_conversion_date'])
                days_until_conversion = (conversion_date - datetime.now()).days
                
                if days_until_conversion <= 30:  # Within 30 days
                    transaction.priority = LOITransactionPriority.URGENT
                    logger.info(f"⏰ Urgent conversion date priority for {transaction.id}")
            except:
                pass
    
    def get_next_batch(self, size: Optional[int] = None, 
                      transaction_type: Optional[LOITransactionType] = None) -> List[LOITransaction]:
        """Get next batch of LOI transactions for processing"""
        batch_size = size or self.batch_size
        batch = []
        
        with self._queue_lock:
            temp_queue = []
            
            while len(batch) < batch_size and self._queue:
                transaction = heapq.heappop(self._queue)
                
                # Filter by transaction type if specified
                if transaction_type and transaction.type != transaction_type:
                    temp_queue.append(transaction)
                    continue
                
                # Move to processing state
                transaction.status = LOITransactionStatus.PROCESSING
                transaction.started_at = datetime.now()
                
                self._processing[transaction.id] = transaction
                batch.append(transaction)
            
            # Put back filtered transactions
            for transaction in temp_queue:
                heapq.heappush(self._queue, transaction)
        
        if batch:
            logger.info(f"📦 Retrieved LOI batch of {len(batch)} transactions for processing")
        
        return batch
    
    def complete_loi_transaction(self, transaction_id: str, outcome: Dict[str, Any]):
        """Mark LOI transaction as completed with outcome"""
        transaction = self._processing.pop(transaction_id, None)
        if not transaction:
            transaction = self._transactions.get(transaction_id)
            if not transaction:
                logger.warning(f"⚠️ LOI Transaction {transaction_id} not found for completion")
                return
        
        # Update transaction state
        transaction.status = LOITransactionStatus.COMPLETED
        transaction.completed_at = datetime.now()
        transaction.add_processing_event('completion', outcome)
        
        # Move to completed tracking
        self._completed[transaction_id] = transaction
        
        # Update workflow stage tracking
        self._update_workflow_stage_tracking(transaction, 'completed')
        
        # Update metrics
        self._total_processed += 1
        processing_time = transaction.calculate_processing_duration()
        if processing_time:
            self._average_processing_time = (
                (self._average_processing_time * (self._total_processed - 1) + processing_time) 
                / self._total_processed
            )
        
        logger.info(f"✅ Completed LOI transaction {transaction_id} in {processing_time:.2f}s")
        
        # Trigger event handler
        if self._on_transaction_completed:
            try:
                self._on_transaction_completed(transaction)
            except Exception as e:
                logger.error(f"❌ Error in transaction_completed handler: {e}")
    
    def fail_loi_transaction(self, transaction_id: str, error: str, error_details: Dict[str, Any] = None):
        """Mark LOI transaction as failed"""
        transaction = self._processing.pop(transaction_id, None)
        if not transaction:
            transaction = self._transactions.get(transaction_id)
            if not transaction:
                logger.warning(f"⚠️ LOI Transaction {transaction_id} not found for failure")
                return
        
        transaction.status = LOITransactionStatus.FAILED
        transaction.completed_at = datetime.now()
        transaction.add_error('processing_failure', error, error_details)
        
        # Update workflow stage tracking
        self._update_workflow_stage_tracking(transaction, 'failed')
        
        self._total_failed += 1
        logger.error(f"❌ Failed LOI transaction {transaction_id}: {error}")
    
    def update_workflow_stage(self, transaction_id: str, new_stage: str, stage_data: Dict[str, Any] = None):
        """Update workflow stage for LOI transaction"""
        transaction = self._transactions.get(transaction_id)
        if not transaction:
            logger.warning(f"⚠️ LOI Transaction {transaction_id} not found for stage update")
            return
        
        old_stage = transaction.workflow_stage
        transaction.workflow_stage = new_stage
        transaction.add_processing_event('stage_change', {
            'old_stage': old_stage,
            'new_stage': new_stage,
            'stage_data': stage_data or {}
        })
        
        # Update stage tracking
        self._update_workflow_stage_tracking(transaction, new_stage, old_stage)
        
        logger.info(f"🔄 LOI Transaction {transaction_id} moved from {old_stage} to {new_stage}")
        
        # Trigger event handler
        if self._on_workflow_stage_changed:
            try:
                self._on_workflow_stage_changed(transaction, old_stage, new_stage)
            except Exception as e:
                logger.error(f"❌ Error in workflow_stage_changed handler: {e}")
    
    def _update_workflow_stage_tracking(self, transaction: LOITransaction, new_stage: str, old_stage: str = None):
        """Update internal workflow stage tracking"""
        transaction_id = transaction.id
        
        # Remove from old stage
        if old_stage and old_stage in self._by_workflow_stage:
            if transaction_id in self._by_workflow_stage[old_stage]:
                self._by_workflow_stage[old_stage].remove(transaction_id)
        
        # Add to new stage
        if new_stage in self._by_workflow_stage:
            if transaction_id not in self._by_workflow_stage[new_stage]:
                self._by_workflow_stage[new_stage].append(transaction_id)
    
    def get_loi_queue_stats(self) -> Dict[str, Any]:
        """Get LOI queue performance statistics"""
        with self._queue_lock:
            queue_size = len(self._queue)
            processing_size = len(self._processing)
            completed_size = len(self._completed)
        
        # Calculate completion rate
        total_transactions = self._total_processed + self._total_failed
        completion_rate = self._total_processed / total_transactions if total_transactions > 0 else 0.0
        
        return {
            'queue_size': queue_size,
            'processing_size': processing_size,
            'completed_size': completed_size,
            'total_processed': self._total_processed,
            'total_failed': self._total_failed,
            'completion_rate': completion_rate,
            'average_processing_time': self._average_processing_time,
            'workflow_stages': {
                stage: len(transactions) 
                for stage, transactions in self._by_workflow_stage.items()
            }
        }
    
    def get_transactions_by_stage(self, stage: str) -> List[LOITransaction]:
        """Get all transactions in a specific workflow stage"""
        transaction_ids = self._by_workflow_stage.get(stage, [])
        return [self._transactions[tid] for tid in transaction_ids if tid in self._transactions]
    
    def set_event_handlers(self, 
                          on_added: Optional[Callable] = None,
                          on_completed: Optional[Callable] = None,
                          on_stage_changed: Optional[Callable] = None):
        """Set event handlers for queue events"""
        self._on_transaction_added = on_added
        self._on_transaction_completed = on_completed
        self._on_workflow_stage_changed = on_stage_changed
    
    def cleanup_old_transactions(self, max_age_hours: int = 72):
        """Clean up old completed/failed transactions"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for tx_id, transaction in self._completed.items():
            if (transaction.completed_at and 
                transaction.completed_at.timestamp() < cutoff_time):
                to_remove.append(tx_id)
        
        for tx_id in to_remove:
            if tx_id in self._completed:
                del self._completed[tx_id]
            if tx_id in self._transactions:
                del self._transactions[tx_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old LOI transactions")
    
    def get_transaction(self, transaction_id: str) -> Optional[LOITransaction]:
        """Get transaction by ID"""
        return self._transactions.get(transaction_id)
    
    def __len__(self) -> int:
        """Get total number of transactions in system"""
        with self._queue_lock:
            return len(self._queue) + len(self._processing)