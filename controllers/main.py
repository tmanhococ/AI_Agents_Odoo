# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class AIAgentsController(http.Controller):
    
    @http.route('/ai_agents/status', type='json', auth='user')
    def get_ai_status(self):
        """Get AI system status"""
        try:
            orchestrator = request.env['ai.orchestrator'].get_default_orchestrator()
            if not orchestrator:
                return {'error': 'No orchestrator configured'}
            
            agents = request.env['ai.agent'].search([('active', '=', True)])
            active_agents = agents.filtered(lambda a: a.state == 'active')
            
            return {
                'orchestrator_state': orchestrator.state,
                'total_agents': len(agents),
                'active_agents': len(active_agents),
                'total_tasks': orchestrator.total_tasks_processed,
                'success_rate': orchestrator.success_rate
            }
        except Exception as e:
            _logger.error(f"Error getting AI status: {str(e)}")
            return {'error': str(e)}
    
    @http.route('/ai_agents/process_request', type='json', auth='user')
    def process_ai_request(self, request_data):
        """Process AI request"""
        try:
            orchestrator = request.env['ai.orchestrator'].get_default_orchestrator()
            if not orchestrator:
                return {'error': 'No orchestrator configured'}
            
            result = orchestrator.process_request(request_data)
            return {'success': True, 'result': result}
        except Exception as e:
            _logger.error(f"Error processing AI request: {str(e)}")
            return {'error': str(e)}
    
    @http.route('/ai_agents/agents', type='json', auth='user')
    def get_agents(self):
        """Get all agents"""
        try:
            agents = request.env['ai.agent'].search([('active', '=', True)])
            agent_list = []
            
            for agent in agents:
                agent_list.append({
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.agent_type,
                    'state': agent.state,
                    'total_tasks': agent.total_tasks,
                    'success_rate': agent.success_rate
                })
            
            return {'agents': agent_list}
        except Exception as e:
            _logger.error(f"Error getting agents: {str(e)}")
            return {'error': str(e)} 