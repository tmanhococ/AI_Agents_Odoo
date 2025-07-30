# AI Agents Orchestrator for Odoo 17

A comprehensive AI agents orchestrator system for Odoo 17 that integrates with the Model Context Protocol (MCP) and provides intelligent automation capabilities through OdooBot.

## Features

### 🤖 AI Agents
- **Planner Agent**: Plans and coordinates complex tasks
- **Router Agent**: Routes requests to appropriate specialized agents
- **CRM Agent**: Handles CRM-related operations
- **Sales Agent**: Manages sales processes
- **Inventory Agent**: Controls inventory operations
- **Accounting Agent**: Handles financial tasks
- **HR Agent**: Manages human resources

### 🎯 Orchestrator Architecture
- **Central Coordination**: Manages task distribution and execution
- **Task Queue**: Handles asynchronous task processing
- **Performance Monitoring**: Tracks agent and system performance
- **Error Handling**: Robust error recovery and retry mechanisms

### 🔌 MCP Protocol Integration
- **Standard Compliance**: Full MCP protocol implementation
- **Tools & Resources**: Exposes agents as MCP tools and resources
- **Client Support**: Compatible with any MCP client
- **Async Processing**: Non-blocking request handling

### 💬 OdooBot Integration
- **Natural Language**: Chat with AI through OdooBot
- **Context Awareness**: Understands current record context
- **Multi-step Tasks**: Handles complex multi-agent workflows
- **Real-time Responses**: Immediate feedback and progress updates

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Addon
```bash
# Copy addon to Odoo addons directory
cp -r ai_agents_orchestrator /path/to/odoo/addons/

# Update addons list in Odoo
# Go to Apps > Update Apps List
```

### 3. Install Module
- Go to **Apps** in Odoo
- Search for "AI Agents Orchestrator"
- Click **Install**

## Configuration

### 1. Setup Default Agents
The system automatically creates default agents:
- Planner Agent
- Router Agent
- CRM Agent
- Sales Agent
- Inventory Agent
- Accounting Agent
- HR Agent

### 2. Configure Orchestrator
1. Go to **AI Agents > Orchestrators**
2. Edit the default orchestrator
3. Assign Planner and Router agents
4. Add specialized agents as needed

### 3. Start MCP Server
1. Go to **AI Agents > MCP Servers**
2. Edit the default server
3. Click **Start Server**

## Usage

### Chat with OdooBot

Simply start a conversation with OdooBot and ask naturally:

```
"Create a new lead for Microsoft with contact John Doe"
"Find all customers in New York"
"Check stock levels for product XYZ"
"Generate a sales report for this month"
"Show me employees in the sales department"
```

### MCP Client Integration

Configure your MCP client (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "odoo-ai": {
      "command": "python",
      "args": ["-m", "ai_agents_orchestrator.mcp_server"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "your_database",
        "ODOO_USERNAME": "your_username",
        "ODOO_PASSWORD": "your_password"
      }
    }
  }
}
```

### Available MCP Tools

#### Process Request
```python
process_request(
    goal: str,
    context: Optional[Dict] = None,
    constraints: Optional[Dict] = None
)
```

#### Execute Agent
```python
execute_agent(
    agent_type: str,
    task_data: Dict
)
```

#### Get Agent Status
```python
get_agent_status()
```

### Available MCP Resources

- `ai://agents` - List all available agents
- `ai://agent/{agent_id}` - Get agent details
- `ai://orchestrator/status` - Get orchestrator status

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OdooBot UI    │    │   MCP Client    │    │   Web API       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    AI Orchestrator        │
                    │  ┌─────────────────────┐  │
                    │  │   Task Queue        │  │
                    │  └─────────────────────┘  │
                    │  ┌─────────────────────┐  │
                    │  │   Agent Registry    │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    AI Agents              │
                    │  ┌─────┐ ┌─────┐ ┌─────┐  │
                    │  │CRM  │ │Sales│ │HR   │  │
                    │  └─────┘ └─────┘ └─────┘  │
                    │  ┌─────┐ ┌─────┐ ┌─────┐  │
                    │  │Inv  │ │Acc  │ │Custom│  │
                    │  └─────┘ └─────┘ └─────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Odoo ERP System        │
                    └───────────────────────────┘
```

## Development

### Adding Custom Agents

1. Create a new agent type:
```python
class CustomAgent(models.Model):
    _name = 'ai.agent.custom'
    _inherit = 'ai.agent'
    
    def _execute_custom_task(self, task_data):
        # Your custom logic here
        return {'status': 'completed', 'result': 'custom_result'}
```

2. Register with orchestrator:
```python
# In data file
<record id="ai_agent_custom" model="ai.agent">
    <field name="name">Custom Agent</field>
    <field name="agent_type">custom</field>
    <field name="description">Custom agent for specific tasks</field>
</record>
```

### Extending MCP Tools

Add new tools to the MCP server:

```python
@mcp.tool(description="Your custom tool")
def custom_tool(ctx: Context, param: str) -> Dict[str, Any]:
    # Your tool implementation
    return {"result": "success"}
```

## Troubleshooting

### Common Issues

1. **MCP Server won't start**
   - Check dependencies: `pip install mcp pydantic anyio`
   - Verify Odoo connection settings
   - Check logs in Odoo

2. **Agents not responding**
   - Verify agent state is 'active'
   - Check agent capabilities configuration
   - Review task logs

3. **OdooBot not recognizing requests**
   - Ensure AI keywords are present in message
   - Check orchestrator configuration
   - Verify conversation creation

### Logs

Check Odoo logs for detailed error information:
```bash
tail -f /var/log/odoo/odoo.log | grep "ai_agents"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the LGPL-3 License.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Contact the development team

## Roadmap

- [ ] Advanced AI model integration
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] API rate limiting
- [ ] Advanced security features 