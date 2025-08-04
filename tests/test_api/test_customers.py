"""
客户API端点测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestCustomersAPI:
    """客户API测试类"""
    
    @pytest.fixture
    def sample_customer_data(self):
        """示例客户数据"""
        return {
            "name": "API测试客户",
            "company": "API测试公司",
            "industry": "软件开发",
            "size": "medium",
            "contact": {
                "phone": "13800138000",
                "email": "api@test.com"
            },
            "profile": {
                "decision_making_style": "数据驱动",
                "business_priorities": ["降本增效"],
                "pain_points": ["效率低下"]
            },
            "tags": ["API测试"],
            "notes": "通过API创建的测试客户"
        }
    
    def test_create_customer(self, sync_client: TestClient, sample_customer_data: dict):
        """测试创建客户API"""
        response = sync_client.post("/api/v1/customers/", json=sample_customer_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API测试客户"
        assert data["company"] == "API测试公司"
        assert data["industry"] == "软件开发"
        assert data["contact"]["phone"] == "13800138000"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_customer_minimal_data(self, sync_client: TestClient):
        """测试使用最小数据创建客户"""
        minimal_data = {
            "name": "最小客户",
            "company": "最小公司"
        }
        
        response = sync_client.post("/api/v1/customers/", json=minimal_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "最小客户"
        assert data["company"] == "最小公司"
        assert data["status"] == "prospect"  # 默认状态
    
    def test_create_customer_invalid_data(self, sync_client: TestClient):
        """测试使用无效数据创建客户"""
        invalid_data = {
            "name": "",  # 空名称
            "company": "测试公司"
        }
        
        response = sync_client.post("/api/v1/customers/", json=invalid_data)
        
        assert response.status_code == 422  # 验证错误
    
    def test_get_customer(self, sync_client: TestClient, sample_customer_data: dict):
        """测试获取单个客户API"""
        # 先创建客户
        create_response = sync_client.post("/api/v1/customers/", json=sample_customer_data)
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        # 获取客户
        response = sync_client.get(f"/api/v1/customers/{customer_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        assert data["name"] == "API测试客户"
        assert data["company"] == "API测试公司"
    
    def test_get_customer_not_found(self, sync_client: TestClient):
        """测试获取不存在的客户"""
        import uuid
        non_existent_id = str(uuid.uuid4())
        
        response = sync_client.get(f"/api/v1/customers/{non_existent_id}")
        
        assert response.status_code == 404
        assert "客户不存在" in response.json()["detail"]
    
    def test_update_customer(self, sync_client: TestClient, sample_customer_data: dict):
        """测试更新客户API"""
        # 先创建客户
        create_response = sync_client.post("/api/v1/customers/", json=sample_customer_data)
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        # 更新数据
        update_data = {
            "name": "更新后的客户",
            "industry": "制造业",
            "contact": {
                "phone": "13900139000",
                "email": "updated@test.com"
            }
        }
        
        # 执行更新
        response = sync_client.put(f"/api/v1/customers/{customer_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的客户"
        assert data["industry"] == "制造业"
        assert data["contact"]["phone"] == "13900139000"
        assert data["company"] == "API测试公司"  # 未更新的字段保持不变
    
    def test_update_customer_not_found(self, sync_client: TestClient):
        """测试更新不存在的客户"""
        import uuid
        non_existent_id = str(uuid.uuid4())
        update_data = {"name": "不存在的客户"}
        
        response = sync_client.put(f"/api/v1/customers/{non_existent_id}", json=update_data)
        
        assert response.status_code == 404
        assert "客户不存在" in response.json()["detail"]
    
    def test_delete_customer(self, sync_client: TestClient, sample_customer_data: dict):
        """测试删除客户API"""
        # 先创建客户
        create_response = sync_client.post("/api/v1/customers/", json=sample_customer_data)
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        # 删除客户
        response = sync_client.delete(f"/api/v1/customers/{customer_id}")
        
        assert response.status_code == 200
        assert "客户删除成功" in response.json()["message"]
        
        # 验证客户已被删除
        get_response = sync_client.get(f"/api/v1/customers/{customer_id}")
        assert get_response.status_code == 404
    
    def test_delete_customer_not_found(self, sync_client: TestClient):
        """测试删除不存在的客户"""
        import uuid
        non_existent_id = str(uuid.uuid4())
        
        response = sync_client.delete(f"/api/v1/customers/{non_existent_id}")
        
        assert response.status_code == 404
        assert "客户不存在" in response.json()["detail"]
    
    def test_get_customers_list(self, sync_client: TestClient):
        """测试获取客户列表API"""
        # 创建几个测试客户
        for i in range(3):
            customer_data = {
                "name": f"列表客户{i}",
                "company": f"列表公司{i}",
                "industry": "软件开发"
            }
            sync_client.post("/api/v1/customers/", json=customer_data)
        
        # 获取客户列表
        response = sync_client.get("/api/v1/customers/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    def test_get_customers_list_with_pagination(self, sync_client: TestClient):
        """测试带分页的客户列表API"""
        response = sync_client.get("/api/v1/customers/?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5