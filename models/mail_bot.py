# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from markupsafe import Markup
import json
import logging

_logger = logging.getLogger(__name__)


class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'

    def _get_answer(self, record, body, values, command=False):
        """Override to integrate AI agents"""
        odoobot_state = self.env.user.odoobot_state
        
        # Check if this is an AI request
        if self._is_ai_request(body):
            return self._handle_ai_request(record, body, values)
        
        # Fall back to original OdooBot logic
        return super()._get_answer(record, body, values, command)

    def _is_ai_request(self, body):
        """Check if the message is an AI request"""
        ai_keywords = [
            'ai', 'agent', 'assistant', 'help me', 'can you', 'please',
            'create', 'find', 'search', 'analyze', 'report', 'generate'
        ]
        
        body_lower = body.lower()
        return any(keyword in body_lower for keyword in ai_keywords)

    def _handle_ai_request(self, record, body, values):
        """Handle AI request through orchestrator"""
        try:
            # Get default orchestrator
            orchestrator = self.env['ai.orchestrator'].get_default_orchestrator()
            if not orchestrator:
                return Markup(_("AI Orchestrator is not configured. Please contact your administrator."))
            
            # Create conversation
            conversation = self.env['ai.conversation'].create({
                'name': f"AI Request: {body[:50]}...",
                'user_id': self.env.user.id,
                'orchestrator_id': orchestrator.id,
            })
            
            # Prepare request data
            request_data = {
                'goal': body,
                'context': {
                    'user_id': self.env.user.id,
                    'user_name': self.env.user.name,
                    'record_model': record._name if record else None,
                    'record_id': record.id if record else None,
                },
                'constraints': {
                    'max_tasks': 5,
                    'timeout': 60,
                }
            }
            
            # Process request
            result = conversation.process_with_orchestrator(request_data)
            
            # Format response
            response = self._format_ai_response(result)
            
            return Markup(response)
            
        except Exception as e:
            _logger.error(f"AI request error: {str(e)}")
            return Markup(_("Sorry, I encountered an error processing your request. Please try again or contact support."))

    def _format_ai_response(self, result):
        """Format AI response for display"""
        if not result:
            return _("I couldn't process your request. Please try again.")
        
        # Extract plan and results
        plan = result.get('plan', {})
        results = result.get('results', [])
        
        # Build response
        response_parts = []
        
        # Add goal
        if plan.get('goal'):
            response_parts.append(f"<b>Goal:</b> {plan['goal']}")
        
        # Add plan summary
        if plan.get('steps'):
            response_parts.append("<b>Plan:</b>")
            for i, step in enumerate(plan['steps'], 1):
                response_parts.append(f"  {i}. {step.get('action', 'Unknown action')}")
        
        # Add results
        if results:
            response_parts.append("<b>Results:</b>")
            for i, result_item in enumerate(results, 1):
                if result_item.get('status') == 'completed':
                    response_parts.append(f"  ✓ Step {i}: Completed successfully")
                elif result_item.get('error'):
                    response_parts.append(f"  ✗ Step {i}: {result_item['error']}")
                else:
                    response_parts.append(f"  - Step {i}: {str(result_item)}")
        
        # Add estimated duration if available
        if plan.get('estimated_duration'):
            response_parts.append(f"<br/><i>Estimated duration: {plan['estimated_duration']}</i>")
        
        return "<br/>".join(response_parts)

    def _get_ai_help_message(self):
        """Get AI help message"""
        return Markup(_("""
I'm your AI assistant! I can help you with various tasks:

<b>CRM Tasks:</b>
• Create leads and opportunities
• Search for customers
• Analyze sales data

<b>Sales Tasks:</b>
• Create sales orders
• Generate quotations
• Track sales performance

<b>Inventory Tasks:</b>
• Check stock levels
• Manage products
• Warehouse operations

<b>Accounting Tasks:</b>
• Create invoices
• Generate reports
• Financial analysis

<b>HR Tasks:</b>
• Search employees
• Attendance tracking
• HR analytics

Just ask me what you need! For example:
• "Create a new lead for ABC Company"
• "Find all customers in New York"
• "Check stock levels for product XYZ"
• "Generate a sales report for this month"
        """))

    def _is_help_requested(self, body):
        """Check if help is requested"""
        help_keywords = ['help', 'what can you do', 'capabilities', 'features']
        return any(keyword in body.lower() for keyword in help_keywords)

    def _handle_help_request(self, body):
        """Handle help request"""
        if self._is_help_requested(body):
            return self._get_ai_help_message()
        return None

    def _get_ai_status(self):
        """Get AI system status"""
        try:
            orchestrator = self.env['ai.orchestrator'].get_default_orchestrator()
            if not orchestrator:
                return "AI Orchestrator: Not configured"
            
            agents = self.env['ai.agent'].search([('active', '=', True)])
            active_agents = agents.filtered(lambda a: a.state == 'active')
            
            status = f"""
<b>AI System Status:</b>
• Orchestrator: {orchestrator.state}
• Active Agents: {len(active_agents)}/{len(agents)}
• Total Tasks: {orchestrator.total_tasks_processed}
• Success Rate: {orchestrator.success_rate:.1f}%
            """
            
            return Markup(status)
            
        except Exception as e:
            return f"AI System Status: Error - {str(e)}"

    def _is_status_request(self, body):
        """Check if status is requested"""
        status_keywords = ['status', 'health', 'system', 'agents']
        return any(keyword in body.lower() for keyword in status_keywords)

    def _handle_status_request(self, body):
        """Handle status request"""
        if self._is_status_request(body):
            return self._get_ai_status()
        return None

    def _get_ai_agents_info(self):
        """Get information about available agents"""
        try:
            agents = self.env['ai.agent'].search([('active', '=', True)])
            
            if not agents:
                return "No AI agents are currently available."
            
            agent_info = ["<b>Available AI Agents:</b>"]
            
            for agent in agents:
                status_icon = "🟢" if agent.state == 'active' else "🔴"
                agent_info.append(f"{status_icon} <b>{agent.name}</b> ({agent.agent_type})")
                if agent.description:
                    agent_info.append(f"   {agent.description}")
                agent_info.append(f"   Tasks: {agent.total_tasks}, Success: {agent.success_rate:.1f}%")
                agent_info.append("")
            
            return Markup("<br/>".join(agent_info))
            
        except Exception as e:
            return f"Error getting agent information: {str(e)}"

    def _is_agents_request(self, body):
        """Check if agents info is requested"""
        agent_keywords = ['agents', 'list agents', 'show agents', 'available agents']
        return any(keyword in body.lower() for keyword in agent_keywords)

    def _handle_agents_request(self, body):
        """Handle agents request"""
        if self._is_agents_request(body):
            return self._get_ai_agents_info()
        return None

    def _get_ai_examples(self):
        """Get AI usage examples"""
        examples = """
<b>AI Assistant Examples:</b>

<b>CRM:</b>
• "Create a new lead for Microsoft with contact John Doe"
• "Find all leads with value over $10,000"
• "Show me opportunities closing this month"

<b>Sales:</b>
• "Create a sales order for customer ABC Corp"
• "Generate a quotation for product XYZ"
• "Show sales performance for Q1"

<b>Inventory:</b>
• "Check stock levels for all products"
• "Find products with low stock"
• "Show warehouse locations"

<b>Accounting:</b>
• "Create an invoice for customer XYZ"
• "Generate financial report for this month"
• "Show outstanding payments"

<b>HR:</b>
• "Find employees in the sales department"
• "Show attendance for this week"
• "List all active employees"

Just ask naturally - I'll understand and help you!
        """
        return Markup(examples)

    def _is_examples_request(self, body):
        """Check if examples are requested"""
        example_keywords = ['examples', 'show me how', 'how to', 'usage']
        return any(keyword in body.lower() for keyword in example_keywords)

    def _handle_examples_request(self, body):
        """Handle examples request"""
        if self._is_examples_request(body):
            return self._get_ai_examples()
        return None 