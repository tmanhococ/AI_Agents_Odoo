# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
import asyncio
import threading
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Union

_logger = logging.getLogger(__name__)


class AIMCPServer(models.Model):
    _name = 'ai.mcp.server'
    _description = 'AI MCP Server'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Server Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    
    # MCP Configuration
    server_url = fields.Char(string='Server URL', default='http://localhost:8000')
    mcp_version = fields.Char(string='MCP Version', default='0.1.0')
    server_id = fields.Char(string='Server ID', default='odoo-ai-orchestrator')
    
    # Agent Integration
    orchestrator_id = fields.Many2one('ai.orchestrator', string='Orchestrator', required=True)
    agent_ids = fields.Many2many('ai.agent', string='Registered Agents')
    
    # Server Status
    state = fields.Selection([
        ('stopped', 'Stopped'),
        ('starting', 'Starting'),
        ('running', 'Running'),
        ('error', 'Error')
    ], default='stopped', tracking=True)
    
    port = fields.Integer(string='Port', default=8000)
    host = fields.Char(string='Host', default='localhost')
    
    # Performance
    total_requests = fields.Integer(string='Total Requests', default=0)
    success_rate = fields.Float(string='Success Rate (%)', default=0.0)
    avg_response_time = fields.Float(string='Avg Response Time (s)', default=0.0)
    
    # Configuration
    max_concurrent_requests = fields.Integer(string='Max Concurrent Requests', default=10)
    request_timeout = fields.Integer(string='Request Timeout (s)', default=30)
    enable_logging = fields.Boolean(string='Enable Logging', default=True)
    
    # Error Handling
    error_message = fields.Text(string='Last Error Message')
    last_activity = fields.Datetime(string='Last Activity', tracking=True)

    def start_server(self):
        """Start the MCP server"""
        try:
            self.state = 'starting'
            self.last_activity = fields.Datetime.now()
            
            # Start server in background thread
            thread = threading.Thread(target=self._run_server, daemon=True)
            thread.start()
            
            self.state = 'running'
            self.message_post(body=_("MCP Server started successfully"))
            
        except Exception as e:
            self.state = 'error'
            self.error_message = str(e)
            self.message_post(body=_("Failed to start MCP Server: %s") % str(e))
            raise

    def stop_server(self):
        """Stop the MCP server"""
        try:
            self.state = 'stopped'
            self.message_post(body=_("MCP Server stopped"))
        except Exception as e:
            self.error_message = str(e)
            self.message_post(body=_("Error stopping MCP Server: %s") % str(e))

    def _run_server(self):
        """Run the MCP server in background"""
        try:
            # Import MCP dependencies
            from mcp.server.fastmcp import FastMCP, Context
            from mcp.server.stdio import stdio_server
            import anyio
            
            # Create MCP server
            mcp = self._create_mcp_server()
            
            # Run server
            async def run():
                async with stdio_server() as streams:
                    await mcp._mcp_server.run(
                        streams[0], streams[1], 
                        mcp._mcp_server.create_initialization_options()
                    )
            
            anyio.run(run)
            
        except Exception as e:
            _logger.error(f"MCP Server error: {str(e)}")
            self.state = 'error'
            self.error_message = str(e)

    def _create_mcp_server(self):
        """Create MCP server with tools and resources"""
        from mcp.server.fastmcp import FastMCP, Context
        from pydantic import BaseModel, Field
        from typing import Any, Dict, List, Optional
        
        # Create MCP server
        mcp = FastMCP(
            self.name,
            description=self.description or "AI Orchestrator MCP Server",
            dependencies=["requests"],
        )
        
        # Register MCP Tools
        self._register_mcp_tools(mcp)
        
        # Register MCP Resources
        self._register_mcp_resources(mcp)
        
        return mcp

    def _register_mcp_tools(self, mcp):
        """Register MCP tools"""
        from pydantic import BaseModel, Field
        from typing import Any, Dict, List, Optional
        
        # Tool Models
        class ProcessRequestResponse(BaseModel):
            success: bool = Field(description="Indicates if the request was successful")
            result: Optional[Dict[str, Any]] = Field(default=None, description="Result data")
            error: Optional[str] = Field(default=None, description="Error message, if any")
        
        class AgentExecuteResponse(BaseModel):
            success: bool = Field(description="Indicates if the execution was successful")
            result: Optional[Dict[str, Any]] = Field(default=None, description="Result data")
            error: Optional[str] = Field(default=None, description="Error message, if any")
        
        # Tool: Process Request
        @mcp.tool(description="Process a request through the AI orchestrator")
        def process_request(
            ctx: Context,
            goal: str,
            context: Optional[Dict[str, Any]] = None,
            constraints: Optional[Dict[str, Any]] = None,
        ) -> ProcessRequestResponse:
            """Process a request through the AI orchestrator"""
            try:
                request_data = {
                    'goal': goal,
                    'context': context or {},
                    'constraints': constraints or {}
                }
                
                result = self.orchestrator_id.process_request(request_data)
                
                return ProcessRequestResponse(
                    success=True,
                    result=result
                )
            except Exception as e:
                return ProcessRequestResponse(
                    success=False,
                    error=str(e)
                )
        
        # Tool: Execute Agent
        @mcp.tool(description="Execute a task using a specific agent")
        def execute_agent(
            ctx: Context,
            agent_type: str,
            task_data: Dict[str, Any],
        ) -> AgentExecuteResponse:
            """Execute a task using a specific agent"""
            try:
                agent = self.env['ai.agent'].get_agent_by_type(agent_type)
                if not agent:
                    return AgentExecuteResponse(
                        success=False,
                        error=f"Agent type '{agent_type}' not found"
                    )
                
                result = agent.execute_task(task_data)
                
                return AgentExecuteResponse(
                    success=True,
                    result=result
                )
            except Exception as e:
                return AgentExecuteResponse(
                    success=False,
                    error=str(e)
                )
        
        # Tool: Get Agent Status
        @mcp.tool(description="Get status of all agents")
        def get_agent_status(ctx: Context) -> Dict[str, Any]:
            """Get status of all agents"""
            agents = self.agent_ids
            status = {}
            
            for agent in agents:
                status[agent.name] = {
                    'type': agent.agent_type,
                    'state': agent.state,
                    'total_tasks': agent.total_tasks,
                    'success_rate': agent.success_rate,
                    'last_activity': agent.last_activity.isoformat() if agent.last_activity else None
                }
            
            return status

    def _register_mcp_resources(self, mcp):
        """Register MCP resources"""
        
        # Resource: List Agents
        @mcp.resource(
            "ai://agents", 
            description="List all available AI agents"
        )
        def get_agents() -> str:
            """List all available AI agents"""
            agents = self.agent_ids
            agent_list = []
            
            for agent in agents:
                agent_list.append({
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.agent_type,
                    'state': agent.state,
                    'capabilities': agent.get_mcp_tools(),
                    'resources': agent.get_mcp_resources()
                })
            
            return json.dumps(agent_list, indent=2)
        
        # Resource: Agent Details
        @mcp.resource(
            "ai://agent/{agent_id}",
            description="Get detailed information about a specific agent"
        )
        def get_agent_details(agent_id: str) -> str:
            """Get detailed information about a specific agent"""
            try:
                agent = self.env['ai.agent'].browse(int(agent_id))
                if not agent.exists():
                    return json.dumps({"error": "Agent not found"}, indent=2)
                
                details = {
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.agent_type,
                    'description': agent.description,
                    'state': agent.state,
                    'capabilities': agent.get_mcp_tools(),
                    'resources': agent.get_mcp_resources(),
                    'performance': {
                        'total_tasks': agent.total_tasks,
                        'success_rate': agent.success_rate,
                        'avg_response_time': agent.avg_response_time
                    },
                    'last_activity': agent.last_activity.isoformat() if agent.last_activity else None
                }
                
                return json.dumps(details, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)}, indent=2)
        
        # Resource: Orchestrator Status
        @mcp.resource(
            "ai://orchestrator/status",
            description="Get orchestrator status and performance"
        )
        def get_orchestrator_status() -> str:
            """Get orchestrator status and performance"""
            orchestrator = self.orchestrator_id
            if not orchestrator:
                return json.dumps({"error": "No orchestrator configured"}, indent=2)
            
            status = {
                'id': orchestrator.id,
                'name': orchestrator.name,
                'state': orchestrator.state,
                'task_queue': orchestrator.get_task_queue_status(),
                'performance': {
                    'total_tasks_processed': orchestrator.total_tasks_processed,
                    'success_rate': orchestrator.success_rate,
                    'avg_processing_time': orchestrator.avg_processing_time
                },
                'last_activity': orchestrator.last_activity.isoformat() if orchestrator.last_activity else None
            }
            
            return json.dumps(status, indent=2)

    def process_mcp_request(self, request_data):
        """Process a request from MCP client"""
        try:
            self.total_requests += 1
            self.last_activity = fields.Datetime.now()
            
            # Route to orchestrator
            result = self.orchestrator_id.process_request(request_data)
            
            # Update success rate
            self._update_performance_metrics(True)
            
            return result
            
        except Exception as e:
            self._update_performance_metrics(False)
            self.error_message = str(e)
            raise

    def _update_performance_metrics(self, success):
        """Update performance metrics"""
        # This is a simplified version - in production you'd want more sophisticated metrics
        if success:
            self.success_rate = min(100.0, self.success_rate + 1.0)
        else:
            self.success_rate = max(0.0, self.success_rate - 1.0)

    def get_mcp_configuration(self):
        """Get MCP server configuration"""
        return {
            'name': self.name,
            'version': self.mcp_version,
            'server_id': self.server_id,
            'url': self.server_url,
            'port': self.port,
            'host': self.host,
            'max_concurrent_requests': self.max_concurrent_requests,
            'request_timeout': self.request_timeout,
            'enable_logging': self.enable_logging
        }

    @api.model
    def get_default_server(self):
        """Get the default MCP server"""
        return self.search([('active', '=', True)], limit=1)

    def restart_server(self):
        """Restart the MCP server"""
        self.stop_server()
        self.start_server() 