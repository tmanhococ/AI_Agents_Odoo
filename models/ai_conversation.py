# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class AIConversation(models.Model):
    _name = 'ai.conversation'
    _description = 'AI Conversation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Conversation Name', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user, tracking=True)
    
    # Conversation Data
    request_data = fields.Text(string='Request Data', help="JSON request data")
    response_data = fields.Text(string='Response Data', help="JSON response data")
    conversation_history = fields.Text(string='Conversation History', help="JSON conversation history")
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='active', tracking=True)
    
    # Context
    orchestrator_id = fields.Many2one('ai.orchestrator', string='Orchestrator', tracking=True)
    task_ids = fields.One2many('ai.task', 'conversation_id', string='Tasks')
    
    # Performance
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now, tracking=True)
    end_time = fields.Datetime(string='End Time', tracking=True)
    duration = fields.Float(string='Duration (seconds)', compute='_compute_duration')
    
    # Analysis
    request_type = fields.Selection([
        ('crm', 'CRM'),
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('accounting', 'Accounting'),
        ('hr', 'HR'),
        ('general', 'General'),
        ('custom', 'Custom')
    ], string='Request Type', compute='_compute_request_type', store=True)
    
    complexity = fields.Selection([
        ('simple', 'Simple'),
        ('medium', 'Medium'),
        ('complex', 'Complex')
    ], string='Complexity', compute='_compute_complexity', store=True)
    
    success = fields.Boolean(string='Success', compute='_compute_success', store=True)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for conversation in self:
            if conversation.start_time and conversation.end_time:
                start = fields.Datetime.from_string(conversation.start_time)
                end = fields.Datetime.from_string(conversation.end_time)
                conversation.duration = (end - start).total_seconds()
            else:
                conversation.duration = 0.0

    @api.depends('request_data')
    def _compute_request_type(self):
        for conversation in self:
            request_data = conversation.get_request_data()
            goal = request_data.get('goal', '').lower()
            
            if any(keyword in goal for keyword in ['lead', 'customer', 'opportunity', 'crm']):
                conversation.request_type = 'crm'
            elif any(keyword in goal for keyword in ['sale', 'order', 'quotation', 'invoice']):
                conversation.request_type = 'sales'
            elif any(keyword in goal for keyword in ['stock', 'inventory', 'warehouse', 'product']):
                conversation.request_type = 'inventory'
            elif any(keyword in goal for keyword in ['account', 'financial', 'invoice', 'payment']):
                conversation.request_type = 'accounting'
            elif any(keyword in goal for keyword in ['employee', 'hr', 'attendance', 'recruitment']):
                conversation.request_type = 'hr'
            elif any(keyword in goal for keyword in ['custom', 'specific']):
                conversation.request_type = 'custom'
            else:
                conversation.request_type = 'general'

    @api.depends('task_ids')
    def _compute_complexity(self):
        for conversation in self:
            task_count = len(conversation.task_ids)
            if task_count <= 2:
                conversation.complexity = 'simple'
            elif task_count <= 5:
                conversation.complexity = 'medium'
            else:
                conversation.complexity = 'complex'

    @api.depends('state')
    def _compute_success(self):
        for conversation in self:
            conversation.success = conversation.state == 'completed'

    def write(self, vals):
        """Override write to handle state changes"""
        if vals.get('state') == 'completed' and not self.end_time:
            vals['end_time'] = fields.Datetime.now()
        
        result = super().write(vals)
        
        # Handle state transitions
        if 'state' in vals:
            self._handle_state_change(vals['state'])
        
        return result

    def _handle_state_change(self, new_state):
        """Handle state change logic"""
        if new_state == 'completed':
            self._on_conversation_complete()
        elif new_state == 'failed':
            self._on_conversation_fail()

    def _on_conversation_complete(self):
        """Called when conversation completes successfully"""
        self.message_post(body=_("Conversation completed successfully"))
        _logger.info(f"Conversation {self.name} completed successfully")

    def _on_conversation_fail(self):
        """Called when conversation fails"""
        self.message_post(body=_("Conversation failed"))
        _logger.error(f"Conversation {self.name} failed")

    def get_request_data(self):
        """Get parsed request data"""
        if self.request_data:
            try:
                return json.loads(self.request_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_response_data(self):
        """Get parsed response data"""
        if self.response_data:
            try:
                return json.loads(self.response_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_conversation_history(self):
        """Get parsed conversation history"""
        if self.conversation_history:
            try:
                return json.loads(self.conversation_history)
            except json.JSONDecodeError:
                return []
        return []

    def add_message(self, role, content, metadata=None):
        """Add a message to conversation history"""
        history = self.get_conversation_history()
        
        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': fields.Datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        history.append(message)
        self.conversation_history = json.dumps(history, indent=2)

    def process_with_orchestrator(self, request_data):
        """Process conversation with orchestrator"""
        try:
            # Update request data
            self.request_data = json.dumps(request_data, indent=2)
            
            # Add user message to history
            self.add_message('user', request_data.get('goal', ''), request_data)
            
            # Get default orchestrator
            orchestrator = self.orchestrator_id or self.env['ai.orchestrator'].get_default_orchestrator()
            if not orchestrator:
                raise ValidationError(_("No orchestrator available"))
            
            self.orchestrator_id = orchestrator.id
            
            # Process request
            result = orchestrator.process_request(request_data)
            
            # Update response data
            self.response_data = json.dumps(result, indent=2)
            
            # Add assistant response to history
            self.add_message('assistant', str(result), result)
            
            # Mark as completed
            self.state = 'completed'
            
            return result
            
        except Exception as e:
            self.state = 'failed'
            self.message_post(body=_("Conversation failed: %s") % str(e))
            raise

    def retry(self):
        """Retry a failed conversation"""
        if self.state == 'failed':
            request_data = self.get_request_data()
            if request_data:
                self.state = 'active'
                return self.process_with_orchestrator(request_data)
        else:
            raise ValidationError(_("Cannot retry this conversation"))

    def cancel(self):
        """Cancel an active conversation"""
        if self.state == 'active':
            self.state = 'cancelled'
            self.message_post(body=_("Conversation cancelled by user"))
        else:
            raise ValidationError(_("Cannot cancel conversation in state: %s") % self.state)

    def get_summary(self):
        """Get conversation summary"""
        request_data = self.get_request_data()
        response_data = self.get_response_data()
        
        return {
            'id': self.id,
            'name': self.name,
            'user': self.user_id.name,
            'request_type': self.request_type,
            'complexity': self.complexity,
            'goal': request_data.get('goal', ''),
            'status': self.state,
            'duration': self.duration,
            'task_count': len(self.task_ids),
            'success': self.success
        }

    @api.model
    def get_user_conversations(self, user_id=None, limit=10):
        """Get conversations for a user"""
        if not user_id:
            user_id = self.env.user.id
        
        return self.search([
            ('user_id', '=', user_id)
        ], limit=limit)

    @api.model
    def cleanup_old_conversations(self, days=30):
        """Clean up old completed/failed conversations"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_conversations = self.search([
            ('create_date', '<', cutoff_date),
            ('state', 'in', ['completed', 'failed', 'cancelled'])
        ])
        
        count = len(old_conversations)
        old_conversations.unlink()
        
        _logger.info(f"Cleaned up {count} old conversations")
        return count 