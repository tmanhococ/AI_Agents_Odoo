# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class AIOrchestrator(models.Model):
    _name = 'ai.orchestrator'
    _description = 'AI Orchestrator'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Orchestrator Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    
    # Configuration
    max_concurrent_tasks = fields.Integer(string='Max Concurrent Tasks', default=10)
    task_timeout = fields.Integer(string='Task Timeout (seconds)', default=300)
    enable_retry = fields.Boolean(string='Enable Retry', default=True)
    max_retries = fields.Integer(string='Max Retries', default=3)
    
    # Agent Management
    agent_ids = fields.Many2many('ai.agent', string='Available Agents')
    planner_agent_id = fields.Many2one('ai.agent', string='Planner Agent', 
                                      domain=[('agent_type', '=', 'planner')])
    router_agent_id = fields.Many2one('ai.agent', string='Router Agent',
                                     domain=[('agent_type', '=', 'router')])
    
    # Task Queue
    task_ids = fields.One2many('ai.task', 'orchestrator_id', string='Tasks')
    pending_task_count = fields.Integer(string='Pending Tasks', compute='_compute_task_counts')
    running_task_count = fields.Integer(string='Running Tasks', compute='_compute_task_counts')
    completed_task_count = fields.Integer(string='Completed Tasks', compute='_compute_task_counts')
    failed_task_count = fields.Integer(string='Failed Tasks', compute='_compute_task_counts')
    
    # Performance
    total_tasks_processed = fields.Integer(string='Total Tasks Processed', compute='_compute_performance')
    success_rate = fields.Float(string='Success Rate (%)', compute='_compute_performance')
    avg_processing_time = fields.Float(string='Avg Processing Time (s)', compute='_compute_performance')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error')
    ], default='draft', tracking=True)
    
    last_activity = fields.Datetime(string='Last Activity', tracking=True)
    error_message = fields.Text(string='Last Error Message')

    @api.depends('task_ids')
    def _compute_task_counts(self):
        for orchestrator in self:
            tasks = orchestrator.task_ids
            orchestrator.pending_task_count = len(tasks.filtered(lambda t: t.state == 'pending'))
            orchestrator.running_task_count = len(tasks.filtered(lambda t: t.state == 'running'))
            orchestrator.completed_task_count = len(tasks.filtered(lambda t: t.state == 'completed'))
            orchestrator.failed_task_count = len(tasks.filtered(lambda t: t.state == 'failed'))

    @api.depends('task_ids')
    def _compute_performance(self):
        for orchestrator in self:
            tasks = orchestrator.task_ids
            orchestrator.total_tasks_processed = len(tasks)
            
            if tasks:
                completed_tasks = tasks.filtered(lambda t: t.state == 'completed')
                orchestrator.success_rate = (len(completed_tasks) / len(tasks)) * 100
                
                # Calculate average processing time
                processing_times = [t.execution_duration for t in completed_tasks if t.execution_duration]
                orchestrator.avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            else:
                orchestrator.success_rate = 0.0
                orchestrator.avg_processing_time = 0.0

    @api.model
    def process_request(self, request_data):
        """Process a request through the orchestrator"""
        try:
            # Create conversation if not exists
            conversation = self.env['ai.conversation'].create({
                'user_id': self.env.user.id,
                'request_data': json.dumps(request_data),
                'state': 'active'
            })
            
            # Step 1: Use Planner Agent to create plan
            plan = self._create_execution_plan(request_data, conversation)
            
            # Step 2: Execute plan using Router Agent
            result = self._execute_plan(plan, conversation)
            
            # Step 3: Update conversation
            conversation.write({
                'response_data': json.dumps(result),
                'state': 'completed'
            })
            
            return result
            
        except Exception as e:
            _logger.error(f"Orchestrator error: {str(e)}")
            raise

    def _create_execution_plan(self, request_data, conversation):
        """Create execution plan using Planner Agent"""
        if not self.planner_agent_id:
            raise ValidationError(_("No Planner Agent configured"))
        
        # Create planning task
        task = self.env['ai.task'].create({
            'name': f"Plan: {request_data.get('goal', 'Unknown')}",
            'task_type': 'planner',
            'agent_id': self.planner_agent_id.id,
            'orchestrator_id': self.id,
            'conversation_id': conversation.id,
            'input_data': json.dumps({
                'goal': request_data.get('goal', ''),
                'context': request_data.get('context', {}),
                'constraints': request_data.get('constraints', {})
            }),
            'priority': 'high'
        })
        
        # Execute planning task
        result = task.execute()
        return result.get('plan', {})

    def _execute_plan(self, plan, conversation):
        """Execute plan using Router Agent and specialized agents"""
        if not self.router_agent_id:
            raise ValidationError(_("No Router Agent configured"))
        
        results = []
        
        for step in plan.get('steps', []):
            # Route step to appropriate agent
            routing_result = self._route_step(step, conversation)
            
            if routing_result.get('status') == 'routed':
                # Execute step with target agent
                step_result = self._execute_step(step, routing_result, conversation)
                results.append(step_result)
            else:
                results.append({'error': routing_result.get('error', 'Routing failed')})
        
        return {
            'plan': plan,
            'results': results,
            'status': 'completed'
        }

    def _route_step(self, step, conversation):
        """Route a step to appropriate agent using Router Agent"""
        task = self.env['ai.task'].create({
            'name': f"Route: {step.get('action', 'Unknown')}",
            'task_type': 'router',
            'agent_id': self.router_agent_id.id,
            'orchestrator_id': self.id,
            'conversation_id': conversation.id,
            'input_data': json.dumps({
                'type': step.get('action', ''),
                'context': step.get('context', {}),
                'requirements': step.get('requirements', {})
            }),
            'priority': 'medium'
        })
        
        return task.execute()

    def _execute_step(self, step, routing_result, conversation):
        """Execute a step using the routed agent"""
        agent_id = routing_result.get('agent_id')
        if not agent_id:
            return {'error': 'No agent assigned'}
        
        agent = self.env['ai.agent'].browse(agent_id)
        if not agent.exists():
            return {'error': 'Agent not found'}
        
        # Create execution task
        task = self.env['ai.task'].create({
            'name': f"Execute: {step.get('action', 'Unknown')}",
            'task_type': agent.agent_type,
            'agent_id': agent.id,
            'orchestrator_id': self.id,
            'conversation_id': conversation.id,
            'input_data': json.dumps({
                'action': step.get('action', ''),
                'data': step.get('data', {}),
                'context': step.get('context', {})
            }),
            'priority': step.get('priority', 'medium')
        })
        
        return task.execute()

    def start(self):
        """Start the orchestrator"""
        if not self.planner_agent_id or not self.router_agent_id:
            raise ValidationError(_("Planner and Router agents must be configured"))
        
        self.state = 'active'
        self.last_activity = fields.Datetime.now()
        self.message_post(body=_("Orchestrator started"))

    def pause(self):
        """Pause the orchestrator"""
        self.state = 'paused'
        self.message_post(body=_("Orchestrator paused"))

    def resume(self):
        """Resume the orchestrator"""
        self.state = 'active'
        self.message_post(body=_("Orchestrator resumed"))

    def stop(self):
        """Stop the orchestrator"""
        self.state = 'draft'
        self.message_post(body=_("Orchestrator stopped"))

    def get_available_agents(self, agent_type=None):
        """Get available agents by type"""
        domain = [('active', '=', True), ('state', '=', 'active')]
        if agent_type:
            domain.append(('agent_type', '=', agent_type))
        
        return self.env['ai.agent'].search(domain)

    def get_task_queue_status(self):
        """Get current task queue status"""
        return {
            'pending': self.pending_task_count,
            'running': self.running_task_count,
            'completed': self.completed_task_count,
            'failed': self.failed_task_count,
            'total': len(self.task_ids)
        }

    @api.model
    def get_default_orchestrator(self):
        """Get the default orchestrator"""
        return self.search([('active', '=', True)], limit=1)

    @api.model
    def create_default_orchestrator(self):
        """Create default orchestrator if it doesn't exist"""
        existing = self.search([('name', '=', 'Default AI Orchestrator')], limit=1)
        if existing:
            return existing
        
        # Get planner and router agents
        planner_agent = self.env['ai.agent'].search([('agent_type', '=', 'planner')], limit=1)
        router_agent = self.env['ai.agent'].search([('agent_type', '=', 'router')], limit=1)
        
        if not planner_agent or not router_agent:
            # Create default agents first
            self.env['ai.agent'].create_default_agents()
            planner_agent = self.env['ai.agent'].search([('agent_type', '=', 'planner')], limit=1)
            router_agent = self.env['ai.agent'].search([('agent_type', '=', 'router')], limit=1)
        
        if planner_agent and router_agent:
            orchestrator = self.create({
                'name': 'Default AI Orchestrator',
                'description': 'Default orchestrator for AI agents',
                'active': True,
                'state': 'active',
                'planner_agent_id': planner_agent.id,
                'router_agent_id': router_agent.id,
                'agent_ids': [(6, 0, self.env['ai.agent'].search([]).ids)]
            })
            
            # Create default MCP server
            self.env['ai.mcp.server'].create({
                'name': 'Odoo AI MCP Server',
                'description': 'MCP Server for AI Orchestrator integration',
                'active': True,
                'orchestrator_id': orchestrator.id,
                'agent_ids': [(6, 0, self.env['ai.agent'].search([]).ids)]
            })
            
            return orchestrator
        
        return False

    def cleanup_completed_tasks(self, days=7):
        """Clean up old completed tasks"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_tasks = self.task_ids.filtered(lambda t: 
            t.state in ['completed', 'failed', 'cancelled'] and 
            t.create_date < cutoff_date
        )
        
        count = len(old_tasks)
        old_tasks.unlink()
        
        _logger.info(f"Cleaned up {count} old tasks from orchestrator {self.name}")
        return count 