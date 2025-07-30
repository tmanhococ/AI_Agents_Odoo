{
    'name': 'AI Agents Orchestrator',
    'version': '1.0.0',
    'category': 'Productivity/AI',
    'summary': 'AI Agents Orchestrator with MCP Protocol Integration',
    'description': """
AI Agents Orchestrator for Odoo 17
==================================

This module provides an AI agents orchestrator system that integrates with Odoo using the Model Context Protocol (MCP).

Features:
- Planner Agent: Plans and coordinates tasks
- Router Agent: Routes requests to appropriate agents
- Specialized Agents: CRM, Sales, Inventory, Accounting agents
- MCP Protocol Integration: Standardized communication
- OdooBot Integration: Chat interface for AI interactions
- Task Automation: Automated workflow execution

Architecture:
- Orchestrator: Central coordination system
- MCP Server: Protocol-compliant communication
- Agent Registry: Dynamic agent management
- Task Queue: Asynchronous task processing
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'mail_bot',
        'web',
        'bus',
    ],
    'data': [
        'data/ir_model_access_data.xml',
        'views/ai_agent_views.xml',
        'views/ai_task_views.xml',
        'views/ai_orchestrator_views.xml',
        'views/ai_conversation_views.xml',
        'views/ai_mcp_server_views.xml',
        'views/menu_views.xml',
        'data/ir_cron_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_backend': [
            'ai_agents_orchestrator/static/src/js/**/*',
            'ai_agents_orchestrator/static/src/css/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
} 