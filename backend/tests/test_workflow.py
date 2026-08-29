import asyncio

from app.core.config import settings
from app.core.models import ReviewDecision, TaskStatus
from app.services.database import FINAL_AUDIENCE_SIZE, initialise_database
from app.services.orchestrator import SQL_V1, SQL_V2, TaskManager
from app.services.tool_registry import execute_sql_sandbox, registry


def test_sql_sandbox_repairs_unknown_column():
    initialise_database(force=True)
    failed = execute_sql_sandbox(SQL_V1)
    assert failed["error_code"] == "UNKNOWN_COLUMN"
    assert failed["field"] == "pay_amount"
    assert failed["suggestion"] == "paid_amount"

    passed = execute_sql_sandbox(SQL_V2)
    assert passed["status"] == "success"
    assert passed["rows"] == FINAL_AUDIENCE_SIZE


def test_tool_registry_rejects_unknown_tools():
    try:
        registry.call("run_arbitrary_python")
    except PermissionError as error:
        assert "not registered" in str(error)
    else:
        raise AssertionError("Unknown tools must be rejected")


def test_normal_workflow_completes_with_structured_assets():
    async def scenario():
        previous_delay = settings.STEP_DELAY_SECONDS
        settings.STEP_DELAY_SECONDS = 0
        try:
            manager = TaskManager()
            task = manager.create("提升高流失高客单用户 30 天复购率 5%", "normal")
            task.status = TaskStatus.RUNNING
            await manager._run(task)
            return task
        finally:
            settings.STEP_DELAY_SECONDS = previous_delay

    task = asyncio.run(scenario())
    assert task.status == TaskStatus.COMPLETED
    assert task.metrics["audience_size"] == FINAL_AUDIENCE_SIZE
    assert task.metrics["sql_retries"] == 1
    assert task.metrics["data_quality"] == 96
    assert task.assets["copy_review"]["winner"] == "A"
    assert task.assets["tool_registration"]["status"] == "registered"
    assert task.assets["tool_receipts"][0]["tool"] == "exclude_recent_contacts"
    assert len(task.assets["copy_review"]["rounds"]) == 4
    assert "query/read_only_whitelist" in task.assets["knowledge_refs"]
    assert all(node.status == "completed" for node in task.nodes)


def test_high_risk_workflow_resumes_after_human_approval():
    async def scenario():
        previous_delay = settings.STEP_DELAY_SECONDS
        settings.STEP_DELAY_SECONDS = 0
        try:
            manager = TaskManager()
            task = manager.create("执行 55,000 人高价值用户召回并触发审核", "risk")
            task.status = TaskStatus.RUNNING
            runner = asyncio.create_task(manager._run(task))
            for _ in range(100):
                if task.status == TaskStatus.AWAITING_REVIEW:
                    break
                await asyncio.sleep(0)
            assert task.status == TaskStatus.AWAITING_REVIEW
            manager.review(task.id, ReviewDecision(action="approve", comment="同意先行灰度"))
            await runner
            return task
        finally:
            settings.STEP_DELAY_SECONDS = previous_delay

    task = asyncio.run(scenario())
    assert task.status == TaskStatus.COMPLETED
    assert task.review["action"] == "approve"
    assert any(event.event == "pipeline_resumed" for event in task.events)
