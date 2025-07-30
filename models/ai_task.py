# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class AITask(models.Model):
    _name = 'ai.task'
    _description = 'AI Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Task Name', required=True, tracking=True)
    task_type = fields.Selection([
        ('planner', 'Planning'),
        ('router', 'Routing'),
        ('crm', 'CRM'),
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('accounting', 'Accounting'),
        ('hr', 'HR'),
        ('custom', 'Custom'),
    ], string='Task Type', required=True, tracking=True)
    
    # Agent Assignment
    agent_id = fields.Many2one('ai.agent', string='Assigned Agent', required=True, tracking=True)
    orchestrator_id = fields.Many2one('ai.orchestrator', string='Orchestrator', tracking=True)
    
    # Task Data
    input_data = fields.Text(string='Input Data', help="JSON input data for the task")
    output_data = fields.Text(string='Output Data', help="JSON output data from the task")
    
    # Status and Timing
    state = fields.Selection([
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='pending', tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium', tracking=True)
    
    start_time = fields.Datetime(string='Start Time', tracking=True)
    end_time = fields.Datetime(string='End Time', tracking=True)
    response_time = fields.Float(string='Response Time (seconds)', compute='_compute_response_time', store=True)
    
    # Error Handling
    error_message = fields.Text(string='Error Message')
    retry_count = fields.Integer(string='Retry Count', default=0)
    max_retries = fields.Integer(string='Max Retries', default=3)
    
    # Context
    conversation_id = fields.Many2one('ai.conversation', string='Conversation', tracking=True)
    user_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, tracking=True)
    
    # Performance
    execution_duration = fields.Float(string='Execution Duration (s)', compute='_compute_execution_duration')
    success = fields.Boolean(string='Success', compute='_compute_success', store=True)

    @api.depends('start_time', 'end_time')
    def _compute_response_time(self):
        for task in self:
            if task.start_time and task.end_time:
                start = fields.Datetime.from_string(task.start_time)
                end = fields.Datetime.from_string(task.end_time)
                task.response_time = (end - start).total_seconds()
            else:
                task.response_time = 0.0

    @api.depends('start_time', 'end_time')
    def _compute_execution_duration(self):
        for task in self:
            if task.start_time and task.end_time:
                start = fields.Datetime.from_string(task.start_time)
                end = fields.Datetime.from_string(task.end_time)
                task.execution_duration = (end - start).total_seconds()
            else:
                task.execution_duration = 0.0

    @api.depends('state')
    def _compute_success(self):
        for task in self:
            task.success = task.state == 'completed'

    @api.model
    def create(self, vals):
        """Override create to set start time when task starts running"""
        if vals.get('state') == 'running' and not vals.get('start_time'):
            vals['start_time'] = fields.Datetime.now()
        return super().create(vals)

    def write(self, vals):
        """Override write to handle state changes"""
        if vals.get('state') == 'running' and not self.start_time:
            vals['start_time'] = fields.Datetime.now()
        elif vals.get('state') in ['completed', 'failed'] and not self.end_time:
            vals['end_time'] = fields.Datetime.now()
        
        result = super().write(vals)
        
        # Handle state transitions
        if 'state' in vals:
            self._handle_state_change(vals['state'])
        
        return result

    def _handle_state_change(self, new_state):
        """Handle state change logic"""
        if new_state == 'running':
            self._on_task_start()
        elif new_state == 'completed':
            self._on_task_complete()
        elif new_state == 'failed':
            self._on_task_fail()

    def _on_task_start(self):
        """Called when task starts running"""
        self.message_post(body=_("Task started execution"))
        _logger.info(f"Task {self.name} started execution")

    def _on_task_complete(self):
        """Called when task completes successfully"""
        self.message_post(body=_("Task completed successfully"))
        _logger.info(f"Task {self.name} completed successfully")

    def _on_task_fail(self):
        """Called when task fails"""
        self.message_post(body=_("Task failed: %s") % self.error_message)
        _logger.error(f"Task {self.name} failed: {self.error_message}")

    def execute(self):
        """Execute the task using the assigned agent"""
        try:
            self.state = 'running'
            
            # Parse input data
            input_data = {}
            if self.input_data:
                try:
                    input_data = json.loads(self.input_data)
                except json.JSONDecodeError as e:
                    raise ValidationError(_("Invalid input data format: %s") % str(e))
            
            # Execute task
            result = self.agent_id.execute_task({
                'type': self.task_type,
                'input': input_data
            })
            
            # Store result
            self.output_data = json.dumps(result, indent=2)
            self.state = 'completed'
            
            return result
            
        except Exception as e:
            self.state = 'failed'
            self.error_message = str(e)
            self.retry_count += 1
            
            if self.retry_count < self.max_retries:
                # Schedule retry
                self.env.ref('ai_agents_orchestrator.ir_cron_retry_failed_tasks').method_direct_trigger()
            
            raise

    def retry(self):
        """Retry a failed task"""
        if self.state == 'failed' and self.retry_count < self.max_retries:
            self.state = 'pending'
            self.error_message = ''
            self.execute()
        else:
            raise ValidationError(_("Cannot retry this task"))

    def cancel(self):
        """Cancel a pending or running task"""
        if self.state in ['pending', 'running']:
            self.state = 'cancelled'
            self.message_post(body=_("Task cancelled by user"))
        else:
            raise ValidationError(_("Cannot cancel task in state: %s") % self.state)

    def get_input_data(self):
        """Get parsed input data"""
        if self.input_data:
            try:
                return json.loads(self.input_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_output_data(self):
        """Get parsed output data"""
        if self.output_data:
            try:
                return json.loads(self.output_data)
            except json.JSONDecodeError:
                return {}
        return {}

    @api.model
    def cleanup_old_tasks(self, days=30):
        """Clean up old completed/failed tasks"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_tasks = self.search([
            ('create_date', '<', cutoff_date),
            ('state', 'in', ['completed', 'failed', 'cancelled'])
        ])
        
        count = len(old_tasks)
        old_tasks.unlink()
        
        _logger.info(f"Cleaned up {count} old tasks")
        return count

    def action_view_related_records(self):
        """Action to view related records based on task type"""
        if self.task_type == 'crm':
            return {
                'name': _('CRM Records'),
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'tree,form',
                'domain': [],
            }
        elif self.task_type == 'sales':
            return {
                'name': _('Sales Orders'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'tree,form',
                'domain': [],
            }
        # Add more task types as needed
        return False 