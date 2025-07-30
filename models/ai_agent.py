# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class AIAgent(models.Model):
    _name = 'ai.agent'
    _description = 'AI Agent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string='Agent Name', required=True, tracking=True)
    agent_type = fields.Selection([
        ('planner', 'Planner Agent'),
        ('router', 'Router Agent'),
        ('crm', 'CRM Agent'),
        ('sales', 'Sales Agent'),
        ('inventory', 'Inventory Agent'),
        ('accounting', 'Accounting Agent'),
        ('hr', 'HR Agent'),
        ('custom', 'Custom Agent'),
    ], string='Agent Type', required=True, tracking=True)
    
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10, help="Determines the order of agents")
    
    # Agent Configuration
    model_ids = fields.Many2many('ir.model', string='Accessible Models')
    capabilities = fields.Text(string='Capabilities', help="JSON description of agent capabilities")
    configuration = fields.Text(string='Configuration', help="JSON configuration for the agent")
    
    # MCP Integration
    mcp_enabled = fields.Boolean(string='MCP Enabled', default=True)
    mcp_tools = fields.Text(string='MCP Tools', help="JSON list of MCP tools this agent provides")
    mcp_resources = fields.Text(string='MCP Resources', help="JSON list of MCP resources this agent provides")
    
    # Relationships
    task_ids = fields.One2many('ai.task', 'agent_id', string='Tasks')
    
    # Performance Tracking
    total_tasks = fields.Integer(string='Total Tasks', compute='_compute_performance')
    success_rate = fields.Float(string='Success Rate (%)', compute='_compute_performance')
    avg_response_time = fields.Float(string='Avg Response Time (s)', compute='_compute_performance')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('busy', 'Busy'),
        ('error', 'Error'),
        ('archived', 'Archived')
    ], default='draft', tracking=True)
    
    last_activity = fields.Datetime(string='Last Activity', tracking=True)
    error_message = fields.Text(string='Last Error Message')

    @api.depends('task_ids')
    def _compute_performance(self):
        for agent in self:
            tasks = agent.task_ids
            agent.total_tasks = len(tasks)
            
            if tasks:
                completed_tasks = tasks.filtered(lambda t: t.state == 'completed')
                agent.success_rate = (len(completed_tasks) / len(tasks)) * 100
                
                # Calculate average response time
                response_times = [t.response_time for t in completed_tasks if t.response_time]
                agent.avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            else:
                agent.success_rate = 0.0
                agent.avg_response_time = 0.0

    @api.model
    def get_agent_by_type(self, agent_type):
        """Get active agent by type"""
        return self.search([
            ('agent_type', '=', agent_type),
            ('active', '=', True),
            ('state', '=', 'active')
        ], limit=1)

    def execute_task(self, task_data):
        """Execute a task using this agent"""
        try:
            self.state = 'busy'
            self.last_activity = fields.Datetime.now()
            
            # Create task record
            task = self.env['ai.task'].create({
                'agent_id': self.id,
                'task_type': task_data.get('type', 'custom'),
                'input_data': json.dumps(task_data.get('input', {})),
                'state': 'running',
            })
            
            # Execute based on agent type
            result = self._execute_agent_specific_task(task_data)
            
            # Update task
            task.write({
                'output_data': json.dumps(result),
                'state': 'completed',
                'response_time': task.response_time,
            })
            
            self.state = 'active'
            return result
            
        except Exception as e:
            self.state = 'error'
            self.error_message = str(e)
            _logger.error(f"Agent {self.name} error: {str(e)}")
            raise

    def _execute_agent_specific_task(self, task_data):
        """Execute task based on agent type"""
        if self.agent_type == 'planner':
            return self._execute_planner_task(task_data)
        elif self.agent_type == 'router':
            return self._execute_router_task(task_data)
        elif self.agent_type == 'crm':
            return self._execute_crm_task(task_data)
        elif self.agent_type == 'sales':
            return self._execute_sales_task(task_data)
        elif self.agent_type == 'inventory':
            return self._execute_inventory_task(task_data)
        elif self.agent_type == 'accounting':
            return self._execute_accounting_task(task_data)
        elif self.agent_type == 'hr':
            return self._execute_hr_task(task_data)
        else:
            return self._execute_custom_task(task_data)

    def _execute_planner_task(self, task_data):
        """Planner agent: Plan and coordinate tasks"""
        input_data = task_data.get('input', {})
        goal = input_data.get('goal', '')
        
        # Analyze goal and create plan
        plan = {
            'goal': goal,
            'steps': [
                {'action': 'analyze_requirements', 'agent': 'router'},
                {'action': 'execute_tasks', 'agent': 'specialized'},
                {'action': 'validate_results', 'agent': 'planner'},
            ],
            'estimated_duration': '5-10 minutes',
            'priority': 'medium'
        }
        
        return {'plan': plan, 'status': 'planned'}

    def _execute_router_task(self, task_data):
        """Router agent: Route requests to appropriate agents"""
        input_data = task_data.get('input', {})
        request_type = input_data.get('type', '')
        
        # Route based on request type
        routing_map = {
            'crm_lead': 'crm',
            'sales_order': 'sales',
            'inventory_check': 'inventory',
            'accounting_report': 'accounting',
            'hr_employee': 'hr',
        }
        
        target_agent_type = routing_map.get(request_type, 'custom')
        target_agent = self.get_agent_by_type(target_agent_type)
        
        if target_agent:
            return {
                'routed_to': target_agent.name,
                'agent_id': target_agent.id,
                'status': 'routed'
            }
        else:
            return {'error': f'No agent found for type: {request_type}'}

    def _execute_crm_task(self, task_data):
        """CRM agent: Handle CRM-related tasks"""
        input_data = task_data.get('input', {})
        action = input_data.get('action', '')
        
        if action == 'create_lead':
            lead_data = input_data.get('lead_data', {})
            lead = self.env['crm.lead'].create(lead_data)
            return {'lead_id': lead.id, 'status': 'created'}
        
        elif action == 'search_leads':
            domain = input_data.get('domain', [])
            leads = self.env['crm.lead'].search(domain)
            return {'leads': [{'id': l.id, 'name': l.name} for l in leads]}
        
        return {'status': 'unknown_action'}

    def _execute_sales_task(self, task_data):
        """Sales agent: Handle sales-related tasks"""
        input_data = task_data.get('input', {})
        action = input_data.get('action', '')
        
        if action == 'create_order':
            order_data = input_data.get('order_data', {})
            order = self.env['sale.order'].create(order_data)
            return {'order_id': order.id, 'status': 'created'}
        
        return {'status': 'unknown_action'}

    def _execute_inventory_task(self, task_data):
        """Inventory agent: Handle inventory-related tasks"""
        input_data = task_data.get('input', {})
        action = input_data.get('action', '')
        
        if action == 'check_stock':
            product_id = input_data.get('product_id')
            product = self.env['product.product'].browse(product_id)
            return {
                'product_id': product.id,
                'available_qty': product.qty_available,
                'virtual_qty': product.virtual_available
            }
        
        return {'status': 'unknown_action'}

    def _execute_accounting_task(self, task_data):
        """Accounting agent: Handle accounting-related tasks"""
        input_data = task_data.get('input', {})
        action = input_data.get('action', '')
        
        if action == 'create_invoice':
            invoice_data = input_data.get('invoice_data', {})
            invoice = self.env['account.move'].create(invoice_data)
            return {'invoice_id': invoice.id, 'status': 'created'}
        
        return {'status': 'unknown_action'}

    def _execute_hr_task(self, task_data):
        """HR agent: Handle HR-related tasks"""
        input_data = task_data.get('input', {})
        action = input_data.get('action', '')
        
        if action == 'search_employees':
            domain = input_data.get('domain', [])
            employees = self.env['hr.employee'].search(domain)
            return {'employees': [{'id': e.id, 'name': e.name} for e in employees]}
        
        return {'status': 'unknown_action'}

    def _execute_custom_task(self, task_data):
        """Custom agent: Handle custom tasks"""
        # This can be extended with custom logic
        return {'status': 'custom_task_executed', 'data': task_data}

    def get_mcp_tools(self):
        """Get MCP tools for this agent"""
        if self.mcp_tools:
            try:
                return json.loads(self.mcp_tools)
            except json.JSONDecodeError:
                return []
        return []

    def get_mcp_resources(self):
        """Get MCP resources for this agent"""
        if self.mcp_resources:
            try:
                return json.loads(self.mcp_resources)
            except json.JSONDecodeError:
                return []
        return []

    @api.model
    def create_default_agents(self):
        """Create default agents if they don't exist"""
        default_agents = [
            {
                'name': 'Planner Agent',
                'agent_type': 'planner',
                'description': 'Plans and coordinates complex tasks',
                'capabilities': json.dumps({
                    'planning': True,
                    'coordination': True,
                    'task_breakdown': True
                })
            },
            {
                'name': 'Router Agent',
                'agent_type': 'router',
                'description': 'Routes requests to appropriate specialized agents',
                'capabilities': json.dumps({
                    'routing': True,
                    'request_analysis': True,
                    'agent_selection': True
                })
            },
            {
                'name': 'CRM Agent',
                'agent_type': 'crm',
                'description': 'Handles CRM-related tasks and operations',
                'capabilities': json.dumps({
                    'lead_management': True,
                    'opportunity_tracking': True,
                    'customer_analysis': True
                })
            },
            {
                'name': 'Sales Agent',
                'agent_type': 'sales',
                'description': 'Handles sales-related tasks and operations',
                'capabilities': json.dumps({
                    'order_management': True,
                    'quotation_handling': True,
                    'sales_analysis': True
                })
            },
            {
                'name': 'Inventory Agent',
                'agent_type': 'inventory',
                'description': 'Handles inventory-related tasks and operations',
                'capabilities': json.dumps({
                    'stock_management': True,
                    'warehouse_operations': True,
                    'inventory_analysis': True
                })
            },
            {
                'name': 'Accounting Agent',
                'agent_type': 'accounting',
                'description': 'Handles accounting-related tasks and operations',
                'capabilities': json.dumps({
                    'invoice_management': True,
                    'financial_reporting': True,
                    'account_analysis': True
                })
            },
            {
                'name': 'HR Agent',
                'agent_type': 'hr',
                'description': 'Handles HR-related tasks and operations',
                'capabilities': json.dumps({
                    'employee_management': True,
                    'attendance_tracking': True,
                    'hr_analytics': True
                })
            }
        ]
        
        for agent_data in default_agents:
            existing = self.search([('agent_type', '=', agent_data['agent_type'])], limit=1)
            if not existing:
                self.create(agent_data) 