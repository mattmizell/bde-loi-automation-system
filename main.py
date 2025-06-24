"""
LOI Automation System - Main Application

FastAPI application that provides the web API and dashboard for the
Better Day Energy Letter of Intent automation system.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Import our core components
from .core.loi_coordinator import LOIAutomationCoordinator, LOIWorkflowStages
from .core.loi_transaction_queue import LOITransaction, LOITransactionType, LOITransactionPriority
from .integrations.crm_integration import handle_crm_integration
from .integrations.crm_document_storage import handle_document_storage
from .integrations.postgresql_esignature import handle_postgresql_esignature
from .integrations.ai_integration import handle_ai_decision
from .handlers.document_generator import handle_document_generation
from .database.connection import get_db_manager, get_db_session
from .config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global coordinator instance
coordinator: Optional[LOIAutomationCoordinator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global coordinator
    
    # Startup
    logger.info("🚀 Starting LOI Automation System...")
    
    settings = get_settings()
    
    # Initialize database
    logger.info("🗄️ Initializing database...")
    db_manager = get_db_manager()
    db_manager.initialize()
    
    # Initialize coordinator
    coordinator = LOIAutomationCoordinator(
        max_queue_size=settings.coordinator.max_queue_size,
        batch_size=settings.coordinator.batch_size
    )
    
    # Register handlers
    coordinator.register_integration_handler('crm', handle_crm_integration)
    coordinator.register_integration_handler('crm_document_storage', handle_document_storage)
    coordinator.register_integration_handler('postgresql_esignature', handle_postgresql_esignature)
    coordinator.register_integration_handler('ai_decision', handle_ai_decision)
    coordinator.register_workflow_handler('document_generation', handle_document_generation)
    
    # Register event callbacks
    coordinator.register_callback('loi_request_received', _on_loi_request_received)
    coordinator.register_callback('document_generated', _on_document_generated)
    coordinator.register_callback('signature_requested', _on_signature_requested)
    coordinator.register_callback('signature_completed', _on_signature_completed)
    coordinator.register_callback('workflow_completed', _on_workflow_completed)
    coordinator.register_callback('performance_alert', _on_performance_alert)
    
    # Start processing
    coordinator.start_processing()
    
    logger.info("✅ LOI Automation System started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down LOI Automation System...")
    if coordinator:
        coordinator.stop_processing()
    logger.info("✅ LOI Automation System stopped")

# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="Better Day Energy LOI Automation System",
    description="Automated Letter of Intent processing for VP Racing fuel supply agreements",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class LOIRequestModel(BaseModel):
    """Model for LOI request submission"""
    company_name: str = Field(..., description="Company/Business name")
    contact_name: str = Field(..., description="Contact person name")
    contact_title: Optional[str] = Field(None, description="Contact person title")
    email: str = Field(..., description="Contact email address")
    phone: str = Field(..., description="Contact phone number")
    business_address: Dict[str, str] = Field(..., description="Business address")
    monthly_gasoline_volume: float = Field(..., ge=0, description="Monthly gasoline volume in gallons")
    monthly_diesel_volume: float = Field(..., ge=0, description="Monthly diesel volume in gallons")
    current_fuel_supplier: Optional[str] = Field(None, description="Current fuel supplier")
    estimated_conversion_date: Optional[str] = Field(None, description="Estimated conversion date")
    image_funding_amount: Optional[float] = Field(0, ge=0, description="Image funding amount")
    incentive_funding_amount: Optional[float] = Field(0, ge=0, description="Incentive funding amount")
    total_estimated_incentives: Optional[float] = Field(0, ge=0, description="Total estimated incentives")
    canopy_installation_required: Optional[bool] = Field(False, description="Canopy installation required")
    current_branding_to_remove: Optional[str] = Field(None, description="Current branding to remove")
    special_requirements_notes: Optional[str] = Field(None, description="Special requirements or notes")
    priority: Optional[str] = Field("normal", description="Processing priority")
    source: Optional[str] = Field("api", description="Request source")

class LOIStatusResponse(BaseModel):
    """Response model for LOI status"""
    transaction_id: str
    status: str
    workflow_stage: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    customer_company: str
    document_id: Optional[str]
    google_drive_url: Optional[str]
    signature_request_id: Optional[str]
    processing_history: List[Dict[str, Any]]

class SystemStatusResponse(BaseModel):
    """Response model for system status"""
    system_name: str
    version: str
    status: str
    running: bool
    queue_stats: Dict[str, Any]
    metrics: Dict[str, Any]
    active_workflows: int

# Event callback functions
def _on_loi_request_received(data: Dict[str, Any]):
    """Handle LOI request received event"""
    transaction = data['transaction']
    logger.info(f"📥 LOI request received: {transaction.id} for {transaction.customer_data.get('company_name')}")

def _on_document_generated(data: Dict[str, Any]):
    """Handle document generated event"""
    transaction = data['transaction']
    logger.info(f"📄 Document generated for LOI: {transaction.id}")

def _on_signature_requested(data: Dict[str, Any]):
    """Handle signature requested event"""
    transaction = data['transaction']
    logger.info(f"✍️ Signature requested for LOI: {transaction.id}")

def _on_signature_completed(data: Dict[str, Any]):
    """Handle signature completed event"""
    transaction = data['transaction']
    logger.info(f"🎉 Signature completed for LOI: {transaction.id}")

def _on_workflow_completed(data: Dict[str, Any]):
    """Handle workflow completed event"""
    transaction = data['transaction']
    logger.info(f"✅ LOI workflow completed: {transaction.id}")

def _on_performance_alert(data: Dict[str, Any]):
    """Handle performance alert"""
    logger.warning(f"⚠️ Performance Alert: {data['message']}")

# Dependency to get coordinator
def get_coordinator() -> LOIAutomationCoordinator:
    """Get the global coordinator instance"""
    if coordinator is None:
        raise HTTPException(status_code=503, detail="LOI Automation System not ready")
    return coordinator

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic system information"""
    return """
    <html>
        <head>
            <title>Better Day Energy LOI Automation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #1f4e79; }
                .status { background: #f0f8ff; padding: 20px; border-radius: 5px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1 class="header">Better Day Energy LOI Automation System</h1>
            <div class="status">
                <h3>System Status: ✅ Online</h3>
                <p>Automated Letter of Intent processing for VP Racing fuel supply agreements</p>
            </div>
            
            <h3>Available Endpoints:</h3>
            <div class="endpoint"><strong>GET /api/v1/status</strong> - System status</div>
            <div class="endpoint"><strong>POST /api/v1/loi/submit</strong> - Submit LOI request</div>
            <div class="endpoint"><strong>GET /api/v1/loi/{transaction_id}</strong> - Get LOI status</div>
            <div class="endpoint"><strong>GET /api/v1/loi/list</strong> - List all LOIs</div>
            <div class="endpoint"><strong>GET /docs</strong> - API documentation</div>
            
            <h3>Dashboard:</h3>
            <div class="endpoint"><strong>GET /dashboard</strong> - LOI processing dashboard</div>
            
            <p style="margin-top: 30px; color: #666;">
                Version: 1.0.0 | Better Day Energy | VP Racing Supply Agreements
            </p>
        </body>
    </html>
    """

@app.get(f"{settings.api.api_prefix}/status", response_model=SystemStatusResponse)
async def get_system_status(coord: LOIAutomationCoordinator = Depends(get_coordinator)):
    """Get system status and metrics"""
    
    status = coord.get_status()
    
    return SystemStatusResponse(
        system_name=status['identity']['name'],
        version=status['identity']['version'],
        status="online" if status['running'] else "offline",
        running=status['running'],
        queue_stats=status['queue'],
        metrics=status['metrics'],
        active_workflows=status['active_workflows']
    )

@app.post(f"{settings.api.api_prefix}/loi/submit")
async def submit_loi_request(
    request: LOIRequestModel,
    background_tasks: BackgroundTasks,
    coord: LOIAutomationCoordinator = Depends(get_coordinator)
):
    """Submit a new LOI request for processing"""
    
    try:
        # Convert request to transaction data
        customer_data = {
            'company_name': request.company_name,
            'contact_name': request.contact_name,
            'contact_title': request.contact_title,
            'email': request.email,
            'phone': request.phone,
            'business_address': request.business_address
        }
        
        crm_form_data = {
            'monthly_gasoline_volume': request.monthly_gasoline_volume,
            'monthly_diesel_volume': request.monthly_diesel_volume,
            'current_fuel_supplier': request.current_fuel_supplier,
            'estimated_conversion_date': request.estimated_conversion_date,
            'image_funding_amount': request.image_funding_amount or 0,
            'incentive_funding_amount': request.incentive_funding_amount or 0,
            'total_estimated_incentives': request.total_estimated_incentives or 0,
            'canopy_installation_required': request.canopy_installation_required,
            'current_branding_to_remove': request.current_branding_to_remove,
            'special_requirements_notes': request.special_requirements_notes
        }
        
        request_data = {
            'customer_data': customer_data,
            'crm_form_data': crm_form_data,
            'source': request.source,
            'priority': request.priority
        }
        
        # Submit to coordinator
        transaction_id = coord.submit_loi_request(request_data)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': 'LOI request submitted successfully',
            'estimated_completion_time': '24-48 hours',
            'submitted_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error submitting LOI request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit LOI request: {str(e)}")

@app.get(f"{settings.api.api_prefix}/loi/{{transaction_id}}", response_model=LOIStatusResponse)
async def get_loi_status(
    transaction_id: str,
    coord: LOIAutomationCoordinator = Depends(get_coordinator)
):
    """Get status of a specific LOI transaction"""
    
    try:
        transaction = coord.transaction_queue.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="LOI transaction not found")
        
        return LOIStatusResponse(
            transaction_id=transaction.id,
            status=transaction.status.value,
            workflow_stage=transaction.workflow_stage,
            created_at=transaction.created_at.isoformat(),
            started_at=transaction.started_at.isoformat() if transaction.started_at else None,
            completed_at=transaction.completed_at.isoformat() if transaction.completed_at else None,
            customer_company=transaction.customer_data.get('company_name', 'Unknown'),
            document_id=transaction.document_id,
            google_drive_url=transaction.google_drive_url,
            signature_request_id=transaction.signature_request_id,
            processing_history=transaction.processing_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting LOI status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LOI status: {str(e)}")

@app.get(f"{settings.api.api_prefix}/loi/list")
async def list_loi_transactions(
    status: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 100,
    coord: LOIAutomationCoordinator = Depends(get_coordinator)
):
    """List LOI transactions with optional filtering"""
    
    try:
        # Get queue stats to access transactions
        queue_stats = coord.transaction_queue.get_loi_queue_stats()
        
        # Get transactions by stage if specified
        if stage:
            transactions = coord.transaction_queue.get_transactions_by_stage(stage)
        else:
            # Get all transactions (this would need to be implemented in the queue)
            transactions = []
            for stage_name in coord.transaction_queue._by_workflow_stage.keys():
                transactions.extend(coord.transaction_queue.get_transactions_by_stage(stage_name))
        
        # Filter by status if specified
        if status:
            transactions = [t for t in transactions if t.status.value == status]
        
        # Limit results
        transactions = transactions[:limit]
        
        # Convert to response format
        transaction_list = []
        for transaction in transactions:
            transaction_list.append({
                'transaction_id': transaction.id,
                'status': transaction.status.value,
                'workflow_stage': transaction.workflow_stage,
                'customer_company': transaction.customer_data.get('company_name', 'Unknown'),
                'created_at': transaction.created_at.isoformat(),
                'priority': transaction.priority.value
            })
        
        return {
            'transactions': transaction_list,
            'total_count': len(transaction_list),
            'queue_stats': queue_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing LOI transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list LOI transactions: {str(e)}")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """LOI processing dashboard"""
    
    return """
    <html>
        <head>
            <title>LOI Dashboard - Better Day Energy</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: #1f4e79; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
                .stats { display: flex; gap: 20px; margin-bottom: 20px; }
                .stat-card { background: white; padding: 20px; border-radius: 5px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stat-number { font-size: 2em; font-weight: bold; color: #1f4e79; }
                .stat-label { color: #666; margin-top: 5px; }
                .workflows { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .workflow-stage { padding: 10px; margin: 5px 0; background: #f0f8ff; border-radius: 3px; }
                .actions { margin-top: 20px; }
                .btn { background: #1f4e79; color: white; padding: 10px 20px; border: none; border-radius: 3px; text-decoration: none; display: inline-block; margin-right: 10px; }
                .refresh { float: right; }
            </style>
            <script>
                async function loadStats() {
                    try {
                        const response = await fetch('/api/v1/status');
                        const data = await response.json();
                        
                        document.getElementById('queue-size').textContent = data.queue_stats.queue_size;
                        document.getElementById('processing-size').textContent = data.queue_stats.processing_size;
                        document.getElementById('completed-count').textContent = data.queue_stats.completed_size || 0;
                        document.getElementById('completion-rate').textContent = (data.queue_stats.completion_rate * 100).toFixed(1) + '%';
                        
                        // Update workflow stages
                        const stages = data.queue_stats.workflow_stages || {};
                        let stagesHtml = '';
                        for (const [stage, count] of Object.entries(stages)) {
                            stagesHtml += `<div class="workflow-stage">${stage}: ${count} transactions</div>`;
                        }
                        document.getElementById('workflow-stages').innerHTML = stagesHtml;
                        
                    } catch (error) {
                        console.error('Error loading stats:', error);
                    }
                }
                
                // Load stats on page load and refresh every 30 seconds
                window.onload = loadStats;
                setInterval(loadStats, 30000);
            </script>
        </head>
        <body>
            <div class="header">
                <h1>LOI Automation Dashboard</h1>
                <p>Better Day Energy - VP Racing Supply Agreements</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="queue-size">-</div>
                    <div class="stat-label">In Queue</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="processing-size">-</div>
                    <div class="stat-label">Processing</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="completed-count">-</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="completion-rate">-</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
            
            <div class="workflows">
                <h3>Workflow Stages <button class="btn refresh" onclick="loadStats()">Refresh</button></h3>
                <div id="workflow-stages">Loading...</div>
            </div>
            
            <div class="actions">
                <a href="/api/v1/loi/list" class="btn">View All LOIs</a>
                <a href="/docs" class="btn">API Documentation</a>
                <a href="/api/v1/status" class="btn">System Status</a>
            </div>
        </body>
    </html>
    """

@app.get(f"{settings.api.api_prefix}/health")
async def health_check():
    """Health check endpoint"""
    
    db_manager = get_db_manager()
    db_healthy = db_manager.health_check()
    
    return {
        'status': 'healthy' if db_healthy else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'system': 'LOI Automation System',
        'version': '1.0.0',
        'database': 'connected' if db_healthy else 'disconnected'
    }

@app.get(f"{settings.api.api_prefix}/database/status")
async def get_database_status():
    """Get database connection and statistics"""
    
    db_manager = get_db_manager()
    connection_info = db_manager.get_connection_info()
    dashboard_stats = db_manager.get_dashboard_stats()
    
    return {
        'connection': connection_info,
        'statistics': dashboard_stats,
        'timestamp': datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': exc.detail,
            'status_code': exc.status_code,
            'timestamp': datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    
    logger.error(f"❌ Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal server error',
            'message': str(exc),
            'timestamp': datetime.now().isoformat()
        }
    )

# Main function for running the application
def main():
    """Main function to run the LOI Automation System"""
    
    settings = get_settings()
    
    logger.info("🚀 Starting Better Day Energy LOI Automation System")
    logger.info(f"📡 API will be available at http://{settings.api.host}:{settings.api.port}")
    logger.info(f"📊 Dashboard will be available at http://{settings.api.host}:{settings.api.port}/dashboard")
    
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        workers=settings.api.workers,
        log_level=settings.logging.level.lower()
    )

if __name__ == "__main__":
    main()