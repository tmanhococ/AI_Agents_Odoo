# -*- coding: utf-8 -*-

def post_init_hook(cr, registry):
    """Post-install hook to create default data"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Create default orchestrator (this will also create agents and MCP server)
    ai_orchestrator_model = env['ai.orchestrator']
    ai_orchestrator_model.create_default_orchestrator()

def uninstall_hook(cr, registry):
    """Uninstall hook to clean up data"""
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Clean up AI data
    env['ai.mcp.server'].search([]).unlink()
    env['ai.orchestrator'].search([]).unlink()
    env['ai.conversation'].search([]).unlink()
    env['ai.task'].search([]).unlink()
    env['ai.agent'].search([]).unlink() 