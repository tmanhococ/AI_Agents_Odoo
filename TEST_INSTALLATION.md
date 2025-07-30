# Hướng dẫn Test Installation AI Agents Orchestrator

## ✅ Kiểm tra Installation

Module đã được test và load thành công! Dưới đây là các bước để verify:

### 1. Khởi động Odoo
```bash
cd /d:/ERPProject/odoo17
python odoo-bin -c odoo.conf --dev=all
```

### 2. Cài đặt Module
1. Mở trình duyệt: `http://localhost:8069`
2. Tạo database mới hoặc sử dụng database hiện có
3. Vào **Apps** > **Update Apps List**
4. Tìm "AI Agents Orchestrator"
5. Click **Install**

### 3. Verify Installation
Sau khi cài đặt, kiểm tra:

#### 3.1 Menu Items
- Vào **AI Agents** menu (sẽ xuất hiện ở menu chính)
- Kiểm tra các sub-menus:
  - AI Agents > Agents
  - Orchestrators > Orchestrators
  - Tasks
  - Conversations
  - MCP Servers

#### 3.2 Models
Kiểm tra các models đã được tạo:
- `ai.agent` - AI Agents
- `ai.task` - AI Tasks
- `ai.orchestrator` - AI Orchestrators
- `ai.conversation` - AI Conversations
- `ai.mcp.server` - MCP Servers

#### 3.3 Default Data
Kiểm tra data mặc định đã được tạo:
- 7 AI Agents (Planner, Router, CRM, Sales, Inventory, Accounting, HR)
- 1 AI Orchestrator
- 1 MCP Server

### 4. Test Basic Functionality

#### 4.1 Test AI Agents
1. Vào **AI Agents > AI Agents > Agents**
2. Kiểm tra 7 agents đã được tạo
3. Edit một agent và verify form view hoạt động

#### 4.2 Test Orchestrator
1. Vào **AI Agents > Orchestrators > Orchestrators**
2. Edit orchestrator mặc định
3. Assign Planner và Router agents
4. Click **Start** button

#### 4.3 Test MCP Server
1. Vào **AI Agents > MCP Servers**
2. Edit MCP server mặc định
3. Click **Start Server** button

#### 4.4 Test OdooBot Integration
1. Vào **Discuss**
2. Chat với OdooBot:
   - "Help me with AI features"
   - "Show AI agents status"
   - "What can you do?"

### 5. Test API Endpoints

#### 5.1 REST API
```bash
# Test status endpoint
curl -X GET "http://localhost:8069/ai_agents/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test agents endpoint
curl -X GET "http://localhost:8069/ai_agents/agents" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 5.2 MCP Protocol
```bash
# Install MCP client
pip install mcp

# Connect to MCP server
mcp connect http://localhost:8080
```

### 6. Troubleshooting

#### 6.1 Nếu gặp lỗi "Module not found"
- Kiểm tra `addons_path` trong `odoo.conf`
- Restart Odoo server

#### 6.2 Nếu gặp lỗi "Model not found"
- Kiểm tra file `__init__.py` trong thư mục `models`
- Kiểm tra imports trong các model files

#### 6.3 Nếu gặp lỗi "Access rights"
- Kiểm tra file `data/ir_model_access_data.xml`
- Verify thứ tự load data files trong `__manifest__.py`

#### 6.4 Nếu gặp lỗi "View not found"
- Kiểm tra các file XML trong thư mục `views`
- Verify file names trong `__manifest__.py`

### 7. Performance Monitoring

#### 7.1 Logs
```bash
# Odoo logs
python odoo-bin -c odoo.conf --log-level=debug

# MCP Server logs
# Check trong Odoo interface > AI Agents > MCP Servers
```

#### 7.2 Metrics
- Vào **AI Agents > Tasks** để xem task performance
- Vào **AI Agents > Conversations** để xem conversation history
- Vào **AI Agents > Orchestrators** để xem orchestrator metrics

### 8. Development

#### 8.1 Thêm Agent mới
1. Tạo record trong `ai.agent` model
2. Implement logic trong `_execute_custom_task`
3. Update MCP tools/resources

#### 8.2 Customize Views
1. Edit files trong thư mục `views`
2. Update `__manifest__.py` nếu thêm file mới
3. Restart Odoo và update module

### 9. Success Indicators

✅ Module loads without errors
✅ All models created successfully
✅ All views display correctly
✅ Default data loaded
✅ Menu items appear
✅ OdooBot integration works
✅ API endpoints respond
✅ MCP server starts

### 10. Next Steps

Sau khi verify installation thành công:

1. **Configure AI Services**: Set up external AI providers
2. **Customize Agents**: Add business-specific logic
3. **Train Models**: Configure AI models for your use cases
4. **Monitor Performance**: Set up monitoring and alerts
5. **Scale**: Add more agents and orchestrators as needed

## 🎉 Installation Complete!

Module AI Agents Orchestrator đã được cài đặt và test thành công. Bạn có thể bắt đầu sử dụng các tính năng AI trong Odoo! 