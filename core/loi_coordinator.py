"""
LOI AUTOMATION COORDINATOR - Core Engine

The main orchestration engine that coordinates all LOI processing workflow
from CRM form submission to completed signed documents.

This coordinator acts as the central nervous system for Better Day Energy's
LOI automation, managing the complete workflow lifecycle.
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import logging
from dataclasses import dataclass
import uuid

from .loi_transaction_queue import (
    LOITransactionQueue, LOITransaction, LOITransactionType, 
    LOITransactionStatus, LOITransactionPriority
)

logger = logging.getLogger(__name__)

@dataclass
class LOICoordinatorMetrics:
    """Performance metrics for the LOI coordinator"""
    lois_processed: int = 0
    documents_generated: int = 0
    signatures_requested: int = 0
    signatures_completed: int = 0
    average_loi_completion_time: float = 0.0
    conversion_rate: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = None

class LOIWorkflowStages:
    """Define workflow stages for LOI processing"""
    INITIAL = "initial"
    CRM_DATA_RETRIEVED = "crm_data_retrieved"
    DOCUMENT_GENERATED = "document_generated"
    STORED_IN_CRM = "stored_in_crm"
    SIGNATURE_REQUESTED = "signature_requested"
    SIGNATURE_COMPLETED = "signature_completed"
    NOTIFICATION_SENT = "notification_sent"
    COMPLETED = "completed"
    FAILED = "failed"

class LOIAutomationCoordinator:
    """
    The central LOI Automation Coordinator.
    
    Orchestrates the complete Letter of Intent workflow:
    1. CRM form data retrieval
    2. Document generation from template
    3. CRM document storage (no OAuth required!)
    4. E-signature request via DocuSign/Sign.com
    5. Status tracking and notifications
    6. Completion workflow
    """
    
    def __init__(self, max_queue_size: int = 5000, batch_size: int = 25):
        # COORDINATOR IDENTITY
        self.identity = {
            'name': 'Better Day Energy LOI Automation Coordinator',
            'version': '1.0.0',
            'customer': 'Better Day Energy - VP Racing Supply Agreements',
            'initialized_at': datetime.now().isoformat(),
            'capabilities': [
                'crm_integration',
                'document_generation', 
                'crm_document_storage',
                'esignature_workflow',
                'status_tracking',
                'automated_notifications'
            ]
        }
        
        # CORE COMPONENTS
        self.transaction_queue = LOITransactionQueue(max_queue_size, batch_size)
        
        # PROCESSING CONFIGURATION
        self.processing_config = {
            'batch_size': batch_size,
            'processing_interval': 2.0,  # Process every 2 seconds
            'max_concurrent_batches': 3,
            'document_timeout': 60.0,
            'signature_timeout': 604800,  # 7 days
            'retry_attempts': 3,
            'graceful_degradation': True
        }
        
        # HANDLER REGISTRY
        self.workflow_handlers: Dict[str, Callable] = {}
        self.integration_handlers: Dict[str, Callable] = {}
        
        # METRICS AND MONITORING
        self.metrics = LOICoordinatorMetrics()
        self.performance_history = []
        self.active_workflows = {}
        
        # THREADING AND CONTROL
        self.running = False
        self.processing_thread = None
        self.metrics_thread = None
        self.signature_monitoring_thread = None
        
        # EVENT CALLBACKS
        self.event_callbacks = {
            'loi_request_received': [],
            'document_generated': [],
            'signature_requested': [],
            'signature_completed': [],
            'workflow_completed': [],
            'workflow_failed': [],
            'performance_alert': []
        }
        
        # Set up queue event handlers
        self.transaction_queue.set_event_handlers(
            on_added=self._on_transaction_added,
            on_completed=self._on_transaction_completed,
            on_stage_changed=self._on_workflow_stage_changed
        )
        
        logger.info("🏢 BETTER DAY ENERGY LOI AUTOMATION COORDINATOR INITIALIZED")
        logger.info(f"📊 Queue Capacity: {max_queue_size}, Batch Size: {batch_size}")
        logger.info("🔄 Ready to process VP Racing LOI requests")
    
    def register_workflow_handler(self, workflow_stage: str, handler: Callable):
        """Register a handler for specific workflow stages"""
        self.workflow_handlers[workflow_stage] = handler
        logger.info(f"📝 Registered workflow handler for {workflow_stage}")
    
    def register_integration_handler(self, integration_type: str, handler: Callable):
        """Register an integration handler (CRM, Google Drive, DocuSign, etc.)"""
        self.integration_handlers[integration_type] = handler
        logger.info(f"🔗 Registered integration handler for {integration_type}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register event callback"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            logger.info(f"📢 Registered callback for {event_type}")
    
    def submit_loi_request(self, request_data: Dict[str, Any]) -> str:
        """Submit a new LOI request for processing"""
        
        # Extract and validate request data
        customer_data = self._extract_customer_data(request_data)
        crm_form_data = request_data.get('crm_form_data', {})
        
        # Create LOI transaction
        transaction = LOITransaction(
            id=request_data.get('id', str(uuid.uuid4())),
            type=LOITransactionType.NEW_LOI_REQUEST,
            priority=self._determine_priority(customer_data, crm_form_data),
            customer_data=customer_data,
            crm_form_data=crm_form_data,
            workflow_stage=LOIWorkflowStages.INITIAL,
            processing_context={
                'source': request_data.get('source', 'api'),
                'submitted_at': datetime.now().isoformat(),
                'ip_address': request_data.get('ip_address'),
                'user_agent': request_data.get('user_agent')
            }
        )
        
        # Calculate complexity score
        transaction.complexity_score = self._calculate_complexity_score(transaction)
        transaction.estimated_processing_time = self._estimate_processing_time(transaction)
        
        # Submit to queue
        if self.transaction_queue.add_loi_transaction(transaction):
            logger.info(f"📥 LOI request {transaction.id} submitted for processing")
            logger.info(f"🏢 Customer: {customer_data.get('company_name', 'Unknown')}")
            
            # Trigger callback
            self._trigger_callbacks('loi_request_received', {
                'transaction': transaction,
                'customer': customer_data
            })
            
            return transaction.id
        else:
            logger.error(f"❌ Failed to queue LOI request {transaction.id}")
            raise Exception("LOI processing queue is full")
    
    def _extract_customer_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and standardize customer data from request"""
        
        crm_data = request_data.get('crm_form_data', {})
        
        return {
            'company_name': crm_data.get('company_business_name', ''),
            'contact_name': crm_data.get('contact_person_name', ''),
            'contact_title': crm_data.get('contact_person_title', ''),
            'email': crm_data.get('email_address', ''),
            'phone': crm_data.get('phone_number', ''),
            'business_address': {
                'street': crm_data.get('business_address_street', ''),
                'city': crm_data.get('business_address_city', ''),
                'state': crm_data.get('business_address_state', ''),
                'zip': crm_data.get('business_address_zip', '')
            },
            'is_vip_customer': self._determine_vip_status(crm_data),
            'customer_type': self._determine_customer_type(crm_data)
        }
    
    def _determine_priority(self, customer_data: Dict[str, Any], 
                          crm_form_data: Dict[str, Any]) -> LOITransactionPriority:
        """Determine processing priority based on business rules"""
        
        # VIP customers get high priority
        if customer_data.get('is_vip_customer'):
            return LOITransactionPriority.HIGH
        
        # High volume customers get high priority
        monthly_volume = (crm_form_data.get('monthly_gasoline_volume', 0) + 
                         crm_form_data.get('monthly_diesel_volume', 0))
        
        if monthly_volume > 50000:
            return LOITransactionPriority.HIGH
        elif monthly_volume > 20000:
            return LOITransactionPriority.NORMAL
        else:
            return LOITransactionPriority.LOW
    
    def _determine_vip_status(self, crm_data: Dict[str, Any]) -> bool:
        """Determine if customer is VIP based on various factors"""
        
        # High volume threshold
        monthly_volume = (crm_data.get('monthly_gasoline_volume', 0) + 
                         crm_data.get('monthly_diesel_volume', 0))
        
        # High incentive amount threshold  
        total_incentives = crm_data.get('total_estimated_incentives', 0)
        
        return monthly_volume > 100000 or total_incentives > 50000
    
    def _determine_customer_type(self, crm_data: Dict[str, Any]) -> str:
        """Determine customer type for processing logic"""
        
        # Check if existing customer
        current_supplier = crm_data.get('current_fuel_supplier', '').lower()
        if 'vp racing' in current_supplier or 'better day' in current_supplier:
            return 'existing_customer'
        
        # Check if competitor customer
        competitor_keywords = ['shell', 'exxon', 'bp', 'chevron', 'valero']
        if any(keyword in current_supplier for keyword in competitor_keywords):
            return 'competitor_customer'
        
        return 'new_prospect'
    
    def _calculate_complexity_score(self, transaction: LOITransaction) -> float:
        """Calculate complexity score for resource allocation"""
        
        score = 5.0  # Base complexity
        
        crm_data = transaction.crm_form_data
        customer_data = transaction.customer_data
        
        # Volume complexity
        monthly_volume = (crm_data.get('monthly_gasoline_volume', 0) + 
                         crm_data.get('monthly_diesel_volume', 0))
        
        if monthly_volume > 100000:
            score += 3.0
        elif monthly_volume > 50000:
            score += 2.0
        elif monthly_volume > 20000:
            score += 1.0
        
        # Incentive complexity
        total_incentives = crm_data.get('total_estimated_incentives', 0)
        if total_incentives > 100000:
            score += 2.0
        elif total_incentives > 50000:
            score += 1.0
        
        # Canopy installation adds complexity
        if crm_data.get('canopy_installation_required', False):
            score += 1.5
        
        # Special requirements add complexity
        if crm_data.get('special_requirements_notes', '').strip():
            score += 1.0
        
        # VIP customers get additional attention
        if customer_data.get('is_vip_customer'):
            score += 1.0
        
        return min(score, 10.0)  # Cap at 10
    
    def _estimate_processing_time(self, transaction: LOITransaction) -> float:
        """Estimate total processing time in seconds"""
        
        base_time = 300  # 5 minutes base
        
        # Adjust based on complexity
        complexity_multiplier = transaction.complexity_score / 5.0
        
        # Adjust based on customer type
        customer_type = transaction.customer_data.get('customer_type', 'new_prospect')
        type_multipliers = {
            'existing_customer': 0.7,  # Faster processing
            'new_prospect': 1.0,
            'competitor_customer': 1.3  # More careful review
        }
        
        type_multiplier = type_multipliers.get(customer_type, 1.0)
        
        return base_time * complexity_multiplier * type_multiplier
    
    def start_processing(self):
        """Start the LOI automation processing engine"""
        
        if self.running:
            logger.warning("⚠️ LOI Coordinator already running")
            return
        
        self.running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            name="LOIWorkflowProcessor"
        )
        self.processing_thread.start()
        
        # Start metrics thread
        self.metrics_thread = threading.Thread(
            target=self._metrics_loop,
            name="LOIMetrics"
        )
        self.metrics_thread.start()
        
        # Start signature monitoring thread
        self.signature_monitoring_thread = threading.Thread(
            target=self._signature_monitoring_loop,
            name="SignatureMonitor"
        )
        self.signature_monitoring_thread.start()
        
        logger.info("🚀 LOI AUTOMATION PROCESSING ACTIVATED")
        logger.info("📄 Ready to process VP Racing LOI requests")
    
    def stop_processing(self):
        """Stop LOI processing gracefully"""
        
        logger.info("🛑 Stopping LOI automation processing...")
        self.running = False
        
        # Wait for threads to complete
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
            
        if self.signature_monitoring_thread:
            self.signature_monitoring_thread.join(timeout=10)
        
        logger.info("✅ LOI automation stopped gracefully")
    
    def _processing_loop(self):
        """Main processing loop for LOI workflow"""
        
        logger.info("🔄 LOI processing loop activated")
        
        while self.running:
            try:
                # Get next batch of transactions
                batch = self.transaction_queue.get_next_batch()
                
                if batch:
                    batch_id = f"loi_batch_{int(time.time())}_{len(batch)}"
                    logger.info(f"📦 Processing LOI batch {batch_id} with {len(batch)} requests")
                    
                    # Process batch asynchronously
                    self._process_batch_async(batch_id, batch)
                
                # Sleep before next iteration
                time.sleep(self.processing_config['processing_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in LOI processing loop: {e}")
                time.sleep(5)
    
    def _process_batch_async(self, batch_id: str, batch: List[LOITransaction]):
        """Process a batch of LOI transactions asynchronously"""
        
        # Track active batch
        self.active_workflows[batch_id] = {
            'transactions': batch,
            'started_at': datetime.now(),
            'status': 'processing'
        }
        
        # Create and start async processing
        def process_batch():
            try:
                asyncio.run(self._process_batch(batch_id, batch))
            except Exception as e:
                logger.error(f"❌ LOI Batch {batch_id} processing failed: {e}")
            finally:
                # Clean up
                if batch_id in self.active_workflows:
                    del self.active_workflows[batch_id]
        
        # Start in separate thread
        batch_thread = threading.Thread(target=process_batch, name=f"LOIBatch_{batch_id}")
        batch_thread.start()
    
    async def _process_batch(self, batch_id: str, batch: List[LOITransaction]):
        """Process batch of LOI transactions"""
        
        batch_start_time = time.time()
        
        # Process transactions concurrently
        tasks = []
        for transaction in batch:
            task = asyncio.create_task(self._process_loi_workflow(transaction))
            tasks.append(task)
        
        # Wait for all transactions to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update metrics
        batch_duration = time.time() - batch_start_time
        successful_count = sum(1 for result in results if not isinstance(result, Exception))
        
        logger.info(f"✅ LOI Batch {batch_id} completed: {successful_count}/{len(batch)} successful in {batch_duration:.2f}s")
    
    async def _process_loi_workflow(self, transaction: LOITransaction):
        """Process individual LOI transaction through complete workflow"""
        
        start_time = time.time()
        
        try:
            # Execute workflow stages based on current stage
            if transaction.workflow_stage == LOIWorkflowStages.INITIAL:
                await self._execute_crm_data_retrieval(transaction)
            
            elif transaction.workflow_stage == LOIWorkflowStages.CRM_DATA_RETRIEVED:
                await self._execute_document_generation(transaction)
            
            elif transaction.workflow_stage == LOIWorkflowStages.DOCUMENT_GENERATED:
                await self._execute_crm_document_storage(transaction)
            
            elif transaction.workflow_stage == LOIWorkflowStages.STORED_IN_CRM:
                await self._execute_signature_request(transaction)
            
            # Note: Signature completion is handled by the monitoring thread
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            self.transaction_queue.fail_loi_transaction(transaction.id, error_message, {
                'processing_time': processing_time,
                'workflow_stage': transaction.workflow_stage
            })
            
            logger.error(f"❌ LOI workflow {transaction.id} failed at {transaction.workflow_stage}: {error_message}")
            raise e
    
    async def _execute_crm_data_retrieval(self, transaction: LOITransaction):
        """Execute CRM data retrieval stage"""
        
        handler = self.integration_handlers.get('crm')
        if not handler:
            raise Exception("No CRM integration handler registered")
        
        # Execute CRM data retrieval
        if asyncio.iscoroutinefunction(handler):
            crm_result = await handler(transaction)
        else:
            crm_result = handler(transaction)
        
        # Update transaction with retrieved data
        transaction.crm_form_data.update(crm_result.get('form_data', {}))
        transaction.add_processing_event('crm_data_retrieved', crm_result)
        
        # Move to next stage
        self.transaction_queue.update_workflow_stage(
            transaction.id, 
            LOIWorkflowStages.CRM_DATA_RETRIEVED,
            crm_result
        )
        
        logger.info(f"📋 CRM data retrieved for LOI {transaction.id}")
    
    async def _execute_document_generation(self, transaction: LOITransaction):
        """Execute document generation stage"""
        
        handler = self.workflow_handlers.get('document_generation')
        if not handler:
            raise Exception("No document generation handler registered")
        
        # Execute document generation
        if asyncio.iscoroutinefunction(handler):
            doc_result = await handler(transaction)
        else:
            doc_result = handler(transaction)
        
        # Update transaction with document info
        transaction.document_id = doc_result.get('document_id')
        transaction.document_data = doc_result.get('document_data', {})
        transaction.add_processing_event('document_generated', doc_result)
        
        # Move to next stage
        self.transaction_queue.update_workflow_stage(
            transaction.id,
            LOIWorkflowStages.DOCUMENT_GENERATED,
            doc_result
        )
        
        # Update metrics
        self.metrics.documents_generated += 1
        
        # Trigger callback
        self._trigger_callbacks('document_generated', {
            'transaction': transaction,
            'document_result': doc_result
        })
        
        logger.info(f"📄 Document generated for LOI {transaction.id}")
    
    async def _execute_crm_document_storage(self, transaction: LOITransaction):
        """Execute CRM document storage stage - much simpler than Google Drive OAuth!"""
        
        handler = self.integration_handlers.get('crm_document_storage')
        if not handler:
            raise Exception("No CRM document storage integration handler registered")
        
        # Get the generated document path
        document_path = transaction.processing_context.get('generated_document_path')
        if not document_path:
            raise Exception("No generated document path found for CRM storage")
        
        # Execute CRM document storage
        if asyncio.iscoroutinefunction(handler):
            storage_result = await handler(transaction, document_path, 'loi_final')
        else:
            storage_result = handler(transaction, document_path, 'loi_final')
        
        # Update transaction with storage info
        transaction.crm_document_id = storage_result.get('document_id')
        transaction.crm_storage_location = storage_result.get('storage_location')
        transaction.add_processing_event('stored_in_crm', storage_result)
        
        # Move to next stage
        self.transaction_queue.update_workflow_stage(
            transaction.id,
            LOIWorkflowStages.STORED_IN_CRM,
            storage_result
        )
        
        logger.info(f"📁 Document stored in CRM for LOI {transaction.id} - No OAuth required!")
    
    async def _execute_signature_request(self, transaction: LOITransaction):
        """Execute e-signature request stage using PostgreSQL storage"""
        
        handler = self.integration_handlers.get('postgresql_esignature')
        if not handler:
            raise Exception("No PostgreSQL e-signature integration handler registered")
        
        # Execute signature request
        if asyncio.iscoroutinefunction(handler):
            signature_result = await handler(transaction)
        else:
            signature_result = handler(transaction)
        
        # Update transaction with signature info
        transaction.signature_request_id = signature_result.get('signature_request_id')
        transaction.add_processing_event('signature_requested', signature_result)
        
        # Move to next stage
        self.transaction_queue.update_workflow_stage(
            transaction.id,
            LOIWorkflowStages.SIGNATURE_REQUESTED,
            signature_result
        )
        
        # Update metrics
        self.metrics.signatures_requested += 1
        
        # Trigger callback
        self._trigger_callbacks('signature_requested', {
            'transaction': transaction,
            'signature_result': signature_result
        })
        
        logger.info(f"✍️ Signature requested for LOI {transaction.id}")
    
    def _signature_monitoring_loop(self):
        """Monitor pending signatures and update status"""
        
        logger.info("👁️ Signature monitoring loop activated")
        
        while self.running:
            try:
                # Get transactions waiting for signature
                pending_signatures = self.transaction_queue.get_transactions_by_stage(
                    LOIWorkflowStages.SIGNATURE_REQUESTED
                )
                
                if pending_signatures:
                    logger.info(f"🔍 Monitoring {len(pending_signatures)} pending signatures")
                    
                    for transaction in pending_signatures:
                        self._check_signature_status(transaction)
                
                # Sleep for 5 minutes between checks
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error in signature monitoring loop: {e}")
                time.sleep(600)  # Sleep longer on error
    
    def _check_signature_status(self, transaction: LOITransaction):
        """Check signature status for a transaction"""
        
        handler = self.integration_handlers.get('esignature')
        if not handler or not transaction.signature_request_id:
            return
        
        try:
            # Check signature status
            status_result = handler.check_signature_status(transaction.signature_request_id)
            
            if status_result.get('completed'):
                # Signature completed
                self._handle_signature_completion(transaction, status_result)
            
        except Exception as e:
            logger.error(f"❌ Error checking signature status for {transaction.id}: {e}")
    
    def _handle_signature_completion(self, transaction: LOITransaction, status_result: Dict[str, Any]):
        """Handle completed signature"""
        
        # Update transaction
        transaction.add_processing_event('signature_completed', status_result)
        
        # Move to completion stage
        self.transaction_queue.update_workflow_stage(
            transaction.id,
            LOIWorkflowStages.SIGNATURE_COMPLETED,
            status_result
        )
        
        # Update metrics
        self.metrics.signatures_completed += 1
        
        # Trigger callback
        self._trigger_callbacks('signature_completed', {
            'transaction': transaction,
            'status_result': status_result
        })
        
        # Complete the transaction
        self.transaction_queue.complete_loi_transaction(transaction.id, {
            'completion_type': 'signature_completed',
            'signed_document_url': status_result.get('signed_document_url'),
            'completed_at': datetime.now().isoformat()
        })
        
        logger.info(f"🎉 LOI {transaction.id} completed with signature!")
    
    def _on_transaction_added(self, transaction: LOITransaction):
        """Handle transaction added to queue"""
        self._trigger_callbacks('loi_request_received', {'transaction': transaction})
    
    def _on_transaction_completed(self, transaction: LOITransaction):
        """Handle transaction completion"""
        self.metrics.lois_processed += 1
        
        # Calculate completion time
        if transaction.started_at and transaction.completed_at:
            completion_time = (transaction.completed_at - transaction.started_at).total_seconds()
            
            # Update average completion time
            total_time = self.metrics.average_loi_completion_time * (self.metrics.lois_processed - 1)
            self.metrics.average_loi_completion_time = (total_time + completion_time) / self.metrics.lois_processed
        
        self._trigger_callbacks('workflow_completed', {'transaction': transaction})
    
    def _on_workflow_stage_changed(self, transaction: LOITransaction, old_stage: str, new_stage: str):
        """Handle workflow stage changes"""
        logger.info(f"🔄 LOI {transaction.id} workflow: {old_stage} → {new_stage}")
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered callbacks for an event"""
        
        for callback in self.event_callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"❌ Callback error for {event_type}: {e}")
    
    def _metrics_loop(self):
        """Background metrics collection and monitoring"""
        
        while self.running:
            try:
                self._update_metrics()
                self._check_performance_alerts()
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"❌ Metrics loop error: {e}")
                time.sleep(120)
    
    def _update_metrics(self):
        """Update coordinator metrics"""
        
        queue_stats = self.transaction_queue.get_loi_queue_stats()
        
        # Calculate conversion rate
        if self.metrics.signatures_requested > 0:
            self.metrics.conversion_rate = self.metrics.signatures_completed / self.metrics.signatures_requested
        
        # Calculate error rate
        total_processed = queue_stats['total_processed'] + queue_stats['total_failed']
        if total_processed > 0:
            self.metrics.error_rate = queue_stats['total_failed'] / total_processed
        
        self.metrics.last_updated = datetime.now()
    
    def _check_performance_alerts(self):
        """Check for performance issues"""
        
        queue_stats = self.transaction_queue.get_loi_queue_stats()
        
        alerts = []
        
        # High queue utilization
        if queue_stats['queue_size'] > (self.transaction_queue.max_size * 0.8):
            alerts.append({
                'type': 'high_queue_utilization',
                'message': f"LOI queue utilization high: {queue_stats['queue_size']}/{self.transaction_queue.max_size}"
            })
        
        # Low conversion rate
        if self.metrics.conversion_rate < 0.7 and self.metrics.signatures_requested > 10:
            alerts.append({
                'type': 'low_conversion_rate', 
                'message': f"Low signature conversion rate: {self.metrics.conversion_rate:.1%}"
            })
        
        # High error rate
        if self.metrics.error_rate > 0.1:
            alerts.append({
                'type': 'high_error_rate',
                'message': f"High error rate: {self.metrics.error_rate:.1%}"
            })
        
        for alert in alerts:
            self._trigger_callbacks('performance_alert', alert)
            logger.warning(f"⚠️ Performance Alert: {alert['message']}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive coordinator status"""
        
        return {
            'identity': self.identity,
            'running': self.running,
            'queue': self.transaction_queue.get_loi_queue_stats(),
            'metrics': {
                'lois_processed': self.metrics.lois_processed,
                'documents_generated': self.metrics.documents_generated,
                'signatures_requested': self.metrics.signatures_requested,
                'signatures_completed': self.metrics.signatures_completed,
                'average_completion_time': self.metrics.average_loi_completion_time,
                'conversion_rate': self.metrics.conversion_rate,
                'error_rate': self.metrics.error_rate,
                'last_updated': self.metrics.last_updated.isoformat() if self.metrics.last_updated else None
            },
            'active_workflows': len(self.active_workflows),
            'registered_handlers': {
                'workflow': list(self.workflow_handlers.keys()),
                'integration': list(self.integration_handlers.keys())
            }
        }