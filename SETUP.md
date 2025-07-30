# Hướng dẫn Setup và Chạy AI Agents Orchestrator

## 1. Cài đặt Dependencies

```bash
cd /d:/ERPProject/odoo17
pip install mcp>=0.1.1 pydantic>=2.0.0 anyio>=3.7.0 requests>=2.31.0 jsonschema>=4.17.0 structlog>=23.1.0
```

## 2. Cấu hình Odoo

File `odoo.conf` đã được cập nhật với:
```ini
addons_path = addons, ../custom_addons, addons/ai_agents_orchestrator
```

## 3. Chạy Odoo

```bash
cd /d:/ERPProject/odoo17
python odoo-bin -c odoo.conf --dev=all
```

## 4. Cài đặt Module

1. Mở trình duyệt: `http://localhost:8069`
2. Tạo database mới hoặc sử dụng database hiện có
3. Vào **Apps** > **Update Apps List**
4. Tìm "AI Agents Orchestrator"
5. Click **Install**

## 5. Cấu hình sau cài đặt

### 5.1 Kiểm tra Agents
1. Vào **AI Agents > AI Agents > Agents**
2. Kiểm tra các agents mặc định đã được tạo:
   - Planner Agent
   - Router Agent
   - CRM Agent
   - Sales Agent
   - Inventory Agent
   - Accounting Agent
   - HR Agent

### 5.2 Cấu hình Orchestrator
1. Vào **AI Agents > Orchestrators > Orchestrators**
2. Edit orchestrator mặc định
3. Assign Planner và Router agents:
   - **Planner Agent**: Chọn Planner Agent
   - **Router Agent**: Chọn Router Agent
4. Click **Start**

### 5.3 Cấu hình MCP Server
1. Vào **AI Agents > MCP Servers**
2. Edit MCP server mặc định
3. Click **Start Server**

## 6. Test OdooBot Integration

1. Vào **Discuss**
2. Chat với OdooBot:
   - "Help me with AI features"
   - "Show AI agents status"
   - "Create a test lead"
   - "What can you do?"

## 7. Test MCP Protocol

### 7.1 Sử dụng MCP Client
```bash
# Cài đặt MCP client
pip install mcp

# Kết nối tới MCP server
mcp connect http://localhost:8080
```

### 7.2 Test MCP Tools
```python
# Test process_request tool
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "process_request",
        "arguments": {
            "request_data": {
                "type": "crm",
                "action": "create_lead",
                "data": {
                    "name": "Test Lead",
                    "email": "test@example.com"
                }
            }
        }
    }
}
```

## 8. Troubleshooting

### 8.1 Lỗi Import
- Kiểm tra dependencies đã cài đặt đầy đủ
- Restart Odoo server

### 8.2 Lỗi MCP Server
- Kiểm tra port 8080 không bị sử dụng
- Kiểm tra logs trong Odoo

### 8.3 Lỗi OdooBot
- Kiểm tra module mail_bot đã được cài đặt
- Kiểm tra quyền truy cập

## 9. Monitoring

### 9.1 Logs
- Odoo logs: `python odoo-bin -c odoo.conf --log-level=debug`
- MCP Server logs: Trong Odoo interface

### 9.2 Performance
- Vào **AI Agents > Tasks** để xem task history
- Vào **AI Agents > Conversations** để xem conversation history

## 10. Development

### 10.1 Thêm Agent mới
1. Tạo record trong `ai.agent` model
2. Implement logic trong `_execute_custom_task`
3. Cập nhật MCP tools/resources

### 10.2 Customize Orchestrator
1. Edit `ai.orchestrator` model
2. Modify `process_request` method
3. Update planning logic

## 11. API Endpoints

### 11.1 REST API
- `GET /ai_agents/status` - Get system status
- `POST /ai_agents/process_request` - Process AI request
- `GET /ai_agents/agents` - Get all agents

### 11.2 MCP Protocol
- `ai://agents` - List all agents
- `ai://agent/{agent_id}` - Get agent details
- `ai://orchestrator/status` - Get orchestrator status

## 12. Security

- Tất cả API endpoints yêu cầu authentication
- MCP server chỉ chạy trên localhost
- Access rights được định nghĩa trong `ir.model.access.csv`

## 13. Backup & Restore

### 13.1 Backup
```bash
pg_dump -h localhost -U odoo_dev -d your_database > backup.sql
```

### 13.2 Restore
```bash
psql -h localhost -U odoo_dev -d your_database < backup.sql
```

## 14. Support

Nếu gặp vấn đề:
1. Kiểm tra logs
2. Restart services
3. Kiểm tra dependencies
4. Verify configuration 