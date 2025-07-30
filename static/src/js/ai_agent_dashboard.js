/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

class AIAgentDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "ai.orchestrator",
                "get_dashboard_data",
                []
            );
            this.dashboardData = data;
        } catch (error) {
            this.notification.add("Error loading dashboard data", {
                type: "danger"
            });
        }
    }
}

AIAgentDashboard.template = "ai_agent_dashboard";
AIAgentDashboard.components = { Layout };

registry.category("actions").add("ai_agent_dashboard", AIAgentDashboard); 