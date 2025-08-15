"""
工作流API端点

提供业务流程工作流的REST API接口。
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.workflows.customer_discovery import (
    CustomerDiscoveryWorkflow,
    create_customer_discovery_workflow,
    DiscoveryStage,
    Priority,
    ContactMethod
)
from src.workflows.lead_management import (
    LeadManagementWorkflow,
    create_lead_management_workflow,
    WorkflowStage,
    LeadPriority,
    AssignmentStrategy
)
from src.models.lead import LeadStatus
from src.core.auth import get_current_user
from src.schemas.user import UserResponse

router = APIRouter(prefix="/workflows", tags=["workflows"])


# 请求模型
class CustomerDiscoveryRequest(BaseModel):
    """客户发现请求"""
    target_criteria: Dict[str, Any] = Field(
        ...,
        description="目标客户标准",
        example={
            "industry": "制造业",
            "company_size": "中型企业",
            "location": "北京",
            "annual_revenue_min": 1000000,
            "annual_revenue_max": 50000000
        }
    )
    discovery_goals: List[str] = Field(
        ...,
        description="发现目标",
        example=["找到20个潜在客户", "完成10个客户接触", "转化3个合格线索"]
    )
    timeline_days: int = Field(
        30,
        description="时间线（天）",
        ge=1,
        le=365
    )


class ContactExecutionRequest(BaseModel):
    """接触执行请求"""
    task_id: str = Field(..., description="任务ID")
    contact_plan_index: int = Field(..., description="接触计划索引", ge=0)


class ContactResultUpdate(BaseModel):
    """接触结果更新"""
    task_id: str = Field(..., description="任务ID")
    contact_record_index: int = Field(..., description="接触记录索引", ge=0)
    result_update: Dict[str, Any] = Field(
        ...,
        description="结果更新",
        example={
            "status": "completed",
            "customer_response": "客户表示感兴趣",
            "next_meeting_scheduled": "2024-02-01T10:00:00Z",
            "notes": "客户对产品功能很感兴趣，需要技术演示"
        }
    )


# 响应模型
class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    stage: str
    priority: str
    title: str
    description: str
    progress: float
    status: str
    due_date: str
    created_at: str
    updated_at: str
    results_summary: Dict[str, int]


class VisitPlanResponse(BaseModel):
    """拜访计划响应"""
    visit_id: str
    customer_profile: Dict[str, Any]
    objectives: List[str]
    agenda: List[Dict[str, Any]]
    preparation_checklist: List[str]
    materials_needed: List[str]
    key_questions: List[str]
    success_criteria: List[str]
    follow_up_actions: List[str]
    scheduled_time: Optional[str] = None
    duration_minutes: int
    location: str
    attendees: List[str]


class ContactRecordResponse(BaseModel):
    """接触记录响应"""
    contact_time: str
    method: str
    result: Dict[str, Any]
    next_steps: List[str]
    follow_up_date: str


# 全局工作流实例
_customer_discovery_workflow: Optional[CustomerDiscoveryWorkflow] = None
_lead_management_workflow: Optional[LeadManagementWorkflow] = None


async def get_customer_discovery_workflow() -> CustomerDiscoveryWorkflow:
    """获取客户发现工作流实例"""
    global _customer_discovery_workflow
    if _customer_discovery_workflow is None:
        _customer_discovery_workflow = await create_customer_discovery_workflow()
    return _customer_discovery_workflow


async def get_lead_management_workflow() -> LeadManagementWorkflow:
    """获取线索管理工作流实例"""
    global _lead_management_workflow
    if _lead_management_workflow is None:
        _lead_management_workflow = await create_lead_management_workflow()
    return _lead_management_workflow


@router.post("/customer-discovery/start", response_model=Dict[str, str])
async def start_customer_discovery(
    request: CustomerDiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_customer_discovery_workflow)
):
    """
    启动客户发现流程
    
    启动一个新的客户发现任务，包括市场研究、客户资格认证、
    接触策略制定和拜访计划生成。
    """
    try:
        task_id = await workflow.start_customer_discovery(
            target_criteria=request.target_criteria,
            discovery_goals=request.discovery_goals,
            timeline_days=request.timeline_days
        )
        
        return {
            "task_id": task_id,
            "message": "客户发现流程已启动",
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动客户发现流程失败: {str(e)}"
        )


@router.get("/customer-discovery/{task_id}/status", response_model=TaskStatusResponse)
async def get_discovery_task_status(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_customer_discovery_workflow)
):
    """
    获取客户发现任务状态
    
    返回指定任务的详细状态信息，包括当前阶段、进度和结果摘要。
    """
    try:
        status = await workflow.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 不存在"
            )
        
        return TaskStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.get("/customer-discovery/{task_id}/visit-plan/{customer_name}", response_model=VisitPlanResponse)
async def get_visit_plan(
    task_id: str,
    customer_name: str,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    获取客户拜访计划
    
    返回指定客户的详细拜访计划，包括目标、议程、准备清单等。
    """
    try:
        visit_plan = await workflow.get_visit_plan(task_id, customer_name)
        
        if not visit_plan:
            raise HTTPException(
                status_code=404,
                detail=f"未找到客户 {customer_name} 的拜访计划"
            )
        
        return VisitPlanResponse(**visit_plan)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取拜访计划失败: {str(e)}"
        )


@router.post("/customer-discovery/execute-contact", response_model=ContactRecordResponse)
async def execute_initial_contact(
    request: ContactExecutionRequest,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    执行初次客户接触
    
    根据接触策略执行客户的初次接触，记录接触结果和后续行动。
    """
    try:
        contact_record = await workflow.execute_initial_contact(
            task_id=request.task_id,
            contact_plan_index=request.contact_plan_index
        )
        
        return ContactRecordResponse(**contact_record)
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"执行客户接触失败: {str(e)}"
        )


@router.put("/customer-discovery/update-contact-result")
async def update_contact_result(
    request: ContactResultUpdate,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    更新接触结果
    
    更新客户接触的结果信息，包括客户反馈、后续行动等。
    """
    try:
        success = await workflow.update_contact_result(
            task_id=request.task_id,
            contact_record_index=request.contact_record_index,
            result_update=request.result_update
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="更新接触结果失败，请检查任务ID和记录索引"
            )
        
        return {
            "message": "接触结果已更新",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新接触结果失败: {str(e)}"
        )


@router.post("/customer-discovery/{task_id}/complete")
async def complete_discovery_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    完成客户发现任务
    
    标记客户发现任务为完成状态。
    """
    try:
        success = await workflow.complete_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"完成任务失败，任务 {task_id} 不存在"
            )
        
        return {
            "message": "客户发现任务已完成",
            "task_id": task_id,
            "completed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"完成任务失败: {str(e)}"
        )


@router.get("/customer-discovery/active-tasks")
async def get_active_discovery_tasks(
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    获取活跃的客户发现任务列表
    
    返回当前用户的所有活跃客户发现任务。
    """
    try:
        active_tasks = []
        
        for task_id, task in workflow.active_tasks.items():
            task_info = {
                "task_id": task_id,
                "title": task.title,
                "stage": task.stage.value,
                "priority": task.priority.value,
                "progress": task.progress,
                "status": task.status,
                "due_date": task.due_date.isoformat(),
                "created_at": task.created_at.isoformat()
            }
            active_tasks.append(task_info)
        
        # 按创建时间倒序排列
        active_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "active_tasks": active_tasks,
            "total_count": len(active_tasks)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取活跃任务失败: {str(e)}"
        )


@router.get("/customer-discovery/{task_id}/results")
async def get_discovery_results(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    获取客户发现结果
    
    返回客户发现任务的详细结果，包括潜在客户、接触记录等。
    """
    try:
        task = workflow.active_tasks.get(task_id)
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 不存在"
            )
        
        # 构建结果摘要
        results = {
            "task_info": {
                "task_id": task_id,
                "title": task.title,
                "stage": task.stage.value,
                "progress": task.progress,
                "status": task.status
            },
            "market_research": task.results.get("market_research", {}),
            "potential_customers": task.results.get("potential_customers", []),
            "qualified_customers": task.results.get("qualified_customers", []),
            "contact_plans": task.results.get("contact_plans", []),
            "contact_records": task.results.get("contact_records", [])
        }
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取发现结果失败: {str(e)}"
        )


# 工作流统计信息
@router.get("/stats")
async def get_workflow_stats(
    current_user: UserResponse = Depends(get_current_user),
    workflow: CustomerDiscoveryWorkflow = Depends(get_workflow)
):
    """
    获取工作流统计信息
    
    返回工作流的整体统计信息。
    """
    try:
        stats = {
            "total_tasks": len(workflow.active_tasks),
            "tasks_by_stage": {},
            "tasks_by_priority": {},
            "tasks_by_status": {},
            "average_progress": 0.0
        }
        
        if workflow.active_tasks:
            # 按阶段统计
            for task in workflow.active_tasks.values():
                stage = task.stage.value
                priority = task.priority.value
                status = task.status
                
                stats["tasks_by_stage"][stage] = stats["tasks_by_stage"].get(stage, 0) + 1
                stats["tasks_by_priority"][priority] = stats["tasks_by_priority"].get(priority, 0) + 1
                stats["tasks_by_status"][status] = stats["tasks_by_status"].get(status, 0) + 1
            
            # 计算平均进度
            total_progress = sum(task.progress for task in workflow.active_tasks.values())
            stats["average_progress"] = total_progress / len(workflow.active_tasks)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )


# 线索管理工作流端点

class NewLeadRequest(BaseModel):
    """新线索请求"""
    lead_data: Dict[str, Any] = Field(
        ...,
        description="线索数据",
        example={
            "company_name": "测试公司",
            "contact_name": "张三",
            "email": "zhang@test.com",
            "phone": "13800138000",
            "job_title": "技术总监",
            "industry": "制造业",
            "company_size": "中型企业",
            "annual_revenue": 5000000,
            "location": "北京"
        }
    )
    source: str = Field("website", description="线索来源")


class LeadStatusUpdateRequest(BaseModel):
    """线索状态更新请求"""
    task_id: str = Field(..., description="任务ID")
    new_status: LeadStatus = Field(..., description="新状态")
    notes: str = Field("", description="备注")
    next_action: Optional[str] = Field(None, description="下一步行动")


class LeadReassignmentRequest(BaseModel):
    """线索重新分配请求"""
    task_id: str = Field(..., description="任务ID")
    new_rep_id: str = Field(..., description="新销售代表ID")
    reason: str = Field("", description="重新分配原因")


@router.post("/lead-management/process-new-lead", response_model=Dict[str, str])
async def process_new_lead(
    request: NewLeadRequest,
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    处理新线索
    
    启动线索管理流程，包括评分、资格认证、分配和跟进计划。
    """
    try:
        task_id = await workflow.process_new_lead(
            lead_data=request.lead_data,
            source=request.source
        )
        
        return {
            "task_id": task_id,
            "message": "线索处理流程已启动",
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理新线索失败: {str(e)}"
        )


@router.get("/lead-management/{task_id}/status")
async def get_lead_task_status(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    获取线索任务状态
    
    返回线索处理任务的详细状态信息。
    """
    try:
        status = await workflow.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 不存在"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.put("/lead-management/update-status")
async def update_lead_status(
    request: LeadStatusUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    更新线索状态
    
    更新线索的处理状态和相关信息。
    """
    try:
        success = await workflow.update_lead_status(
            task_id=request.task_id,
            new_status=request.new_status,
            notes=request.notes,
            next_action=request.next_action
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="更新线索状态失败，请检查任务ID"
            )
        
        return {
            "message": "线索状态已更新",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新线索状态失败: {str(e)}"
        )


@router.put("/lead-management/reassign")
async def reassign_lead(
    request: LeadReassignmentRequest,
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    重新分配线索
    
    将线索重新分配给其他销售代表。
    """
    try:
        success = await workflow.reassign_lead(
            task_id=request.task_id,
            new_rep_id=request.new_rep_id,
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="重新分配线索失败，请检查任务ID和销售代表ID"
            )
        
        return {
            "message": "线索已重新分配",
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"重新分配线索失败: {str(e)}"
        )


@router.get("/lead-management/sales-rep/{rep_id}/workload")
async def get_sales_rep_workload(
    rep_id: str,
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    获取销售代表工作负载
    
    返回指定销售代表的工作负载和任务分配情况。
    """
    try:
        workload = await workflow.get_sales_rep_workload(rep_id)
        
        if not workload:
            raise HTTPException(
                status_code=404,
                detail=f"销售代表 {rep_id} 不存在"
            )
        
        return workload
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取工作负载失败: {str(e)}"
        )


@router.get("/lead-management/metrics")
async def get_lead_workflow_metrics(
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    获取线索工作流指标
    
    返回线索管理工作流的整体指标和统计信息。
    """
    try:
        metrics = await workflow.get_workflow_metrics()
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取工作流指标失败: {str(e)}"
        )


@router.get("/lead-management/active-tasks")
async def get_active_lead_tasks(
    current_user: UserResponse = Depends(get_current_user),
    workflow: LeadManagementWorkflow = Depends(get_lead_management_workflow)
):
    """
    获取活跃的线索任务列表
    
    返回当前所有活跃的线索处理任务。
    """
    try:
        active_tasks = []
        
        for task_id, task in workflow.active_tasks.items():
            task_info = {
                "task_id": task_id,
                "lead_id": task.lead_id,
                "title": task.title,
                "stage": task.stage.value,
                "priority": task.priority.value,
                "assigned_to": task.assigned_to,
                "progress": task.progress,
                "status": task.status,
                "due_date": task.due_date.isoformat(),
                "created_at": task.created_at.isoformat()
            }
            active_tasks.append(task_info)
        
        # 按创建时间倒序排列
        active_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "active_tasks": active_tasks,
            "total_count": len(active_tasks)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取活跃任务失败: {str(e)}"
        )