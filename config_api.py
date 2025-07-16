import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config_manager import (AgentConfig, ModelConfig, PromptTemplate,
                            ToolConfig, WorkflowConfig, config_manager)

logger = logging.getLogger(__name__)


# Pydantic models for API requests
class AgentConfigRequest(BaseModel):
    role: str = Field(..., description="Agent role name")
    goal: str = Field(..., description="Agent goal description")
    backstory: str = Field(..., description="Agent backstory")
    verbose: bool = Field(True, description="Enable verbose logging")
    memory: bool = Field(True, description="Enable agent memory")
    max_iter: int = Field(3, description="Maximum iterations")
    allow_delegation: bool = Field(False, description="Allow task delegation")
    temperature: float = Field(0.3, description="LLM temperature")
    max_tokens: int = Field(2048, description="Maximum tokens")


class PromptTemplateRequest(BaseModel):
    name: str = Field(..., description="Prompt template name")
    description: str = Field(..., description="Prompt description")
    template: str = Field(..., description="Prompt template content")
    variables: List[str] = Field(..., description="Template variables")
    category: str = Field(..., description="Prompt category")
    channel: Optional[str] = Field(
        None, description="Channel (linkedin/email)")


class WorkflowConfigRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps")
    settings: Dict[str, Any] = Field(..., description="Workflow settings")


class ToolConfigRequest(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    enabled: bool = Field(True, description="Tool enabled status")
    provider: str = Field(..., description="Tool provider")
    config: Dict[str, Any] = Field(..., description="Tool configuration")


class TestRequest(BaseModel):
    input_data: Dict[str, Any] = Field(..., description="Test input data")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context")


class RollbackRequest(BaseModel):
    version: int = Field(..., description="Version to rollback to")


# Create FastAPI app for configuration management
config_app = FastAPI(
    title="CrewAI Configuration Manager",
    description="API for managing CrewAI agents, prompts, workflows, and tools",
    version="1.0.0",
)

# Add CORS middleware
config_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Agent configuration endpoints
@config_app.get("/agents", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all agent configurations"""
    try:
        agents = config_manager.list_agents()
        return [
            {
                **agent.__dict__,
                "created_at": agent.created_at,
                "updated_at": agent.updated_at,
            }
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent configuration"""
    try:
        agent = config_manager.load_agent_config(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent.__dict__
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/agents/{agent_id}")
async def create_or_update_agent(agent_id: str, request: AgentConfigRequest):
    """Create or update agent configuration"""
    try:
        agent = AgentConfig(
            id=agent_id,
            role=request.role,
            goal=request.goal,
            backstory=request.backstory,
            verbose=request.verbose,
            memory=request.memory,
            max_iter=request.max_iter,
            allow_delegation=request.allow_delegation,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Check if agent exists to set version
        existing_agent = config_manager.load_agent_config(agent_id)
        if existing_agent:
            agent.version = existing_agent.version + 1
            agent.created_at = existing_agent.created_at

        config_manager.save_agent_config(agent)
        return {
            "message": "Agent configuration saved successfully",
            "agent": agent.__dict__,
        }
    except Exception as e:
        logger.error(f"Error creating/updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete agent configuration"""
    try:
        success = config_manager.delete_agent_config(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": "Agent configuration deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Prompt template endpoints
@config_app.get("/prompts", response_model=List[Dict[str, Any]])
async def list_prompts():
    """List all prompt templates"""
    try:
        prompts = config_manager.list_prompts()
        return [prompt.__dict__ for prompt in prompts]
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """Get specific prompt template"""
    try:
        prompt = config_manager.load_prompt_template(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return prompt.__dict__
    except Exception as e:
        logger.error(f"Error getting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/prompts/{prompt_id}")
async def create_or_update_prompt(
        prompt_id: str,
        request: PromptTemplateRequest):
    """Create or update prompt template"""
    try:
        prompt = PromptTemplate(
            id=prompt_id,
            name=request.name,
            description=request.description,
            template=request.template,
            variables=request.variables,
            category=request.category,
            channel=request.channel,
        )

        # Check if prompt exists to set version
        existing_prompt = config_manager.load_prompt_template(prompt_id)
        if existing_prompt:
            prompt.version = existing_prompt.version + 1
            prompt.created_at = existing_prompt.created_at

        config_manager.save_prompt_template(prompt)
        return {
            "message": "Prompt template saved successfully",
            "prompt": prompt.__dict__,
        }
    except Exception as e:
        logger.error(f"Error creating/updating prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Delete prompt template"""
    try:
        success = config_manager.delete_prompt_template(prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt not found")
        return {"message": "Prompt template deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Workflow configuration endpoints
@config_app.get("/workflows", response_model=List[Dict[str, Any]])
async def list_workflows():
    """List all workflow configurations"""
    try:
        workflows = config_manager.list_workflows()
        return [workflow.__dict__ for workflow in workflows]
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow configuration"""
    try:
        workflow = config_manager.load_workflow_config(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow.__dict__
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/workflows/{workflow_id}")
async def create_or_update_workflow(
        workflow_id: str,
        request: WorkflowConfigRequest):
    """Create or update workflow configuration"""
    try:
        workflow = WorkflowConfig(
            id=workflow_id,
            name=request.name,
            description=request.description,
            steps=request.steps,
            settings=request.settings,
        )

        # Check if workflow exists to set version
        existing_workflow = config_manager.load_workflow_config(workflow_id)
        if existing_workflow:
            workflow.version = existing_workflow.version + 1
            workflow.created_at = existing_workflow.created_at

        config_manager.save_workflow_config(workflow)
        return {
            "message": "Workflow configuration saved successfully",
            "workflow": workflow.__dict__,
        }
    except Exception as e:
        logger.error(f"Error creating/updating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete workflow configuration"""
    try:
        success = config_manager.delete_workflow_config(workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return {"message": "Workflow configuration deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Tool configuration endpoints
@config_app.get("/tools", response_model=List[Dict[str, Any]])
async def list_tools():
    """List all tool configurations"""
    try:
        tools = config_manager.list_tools()
        return [tool.__dict__ for tool in tools]
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get specific tool configuration"""
    try:
        tool = config_manager.load_tool_config(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool.__dict__
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/tools/{tool_id}")
async def create_or_update_tool(tool_id: str, request: ToolConfigRequest):
    """Create or update tool configuration"""
    try:
        tool = ToolConfig(
            id=tool_id,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
            provider=request.provider,
            config=request.config,
        )

        # Check if tool exists to set version
        existing_tool = config_manager.load_tool_config(tool_id)
        if existing_tool:
            tool.version = existing_tool.version + 1
            tool.created_at = existing_tool.created_at

        config_manager.save_tool_config(tool)
        return {
            "message": "Tool configuration saved successfully",
            "tool": tool.__dict__,
        }
    except Exception as e:
        logger.error(f"Error creating/updating tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete tool configuration"""
    try:
        success = config_manager.delete_tool_config(tool_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")
        return {"message": "Tool configuration deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility endpoints
@config_app.post("/backup")
async def backup_configurations(backup_name: str = "backup"):
    """Backup all configurations"""
    try:
        backup_path = (
            f"backups/{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        config_manager.backup_configs(backup_path)
        return {
            "message": "Configurations backed up successfully",
            "backup_path": backup_path,
        }
    except Exception as e:
        logger.error(f"Error backing up configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/restore")
async def restore_configurations(backup_path: str):
    """Restore configurations from backup"""
    try:
        config_manager.restore_configs(backup_path)
        return {"message": "Configurations restored successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        logger.error(f"Error restoring configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Version control endpoints
@config_app.get("/version-history/{entity_type}/{entity_id}")
async def get_version_history(entity_type: str, entity_id: str):
    """Get version history for an entity"""
    try:
        history = config_manager.get_version_history(entity_type, entity_id)
        return [history_item.__dict__ for history_item in history]
    except Exception as e:
        logger.error(f"Error getting version history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/rollback/{entity_type}/{entity_id}")
async def rollback_entity(
        entity_type: str,
        entity_id: str,
        request: RollbackRequest):
    """Rollback an entity to a specific version"""
    try:
        success = config_manager.rollback_to_version(
            entity_type, entity_id, request.version
        )
        if not success:
            raise HTTPException(status_code=404, detail="Version not found")
        return {
            "message": f"Successfully rolled back {entity_type} {entity_id} to version {request.version}"
        }
    except Exception as e:
        logger.error(f"Error rolling back {entity_type} {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Testing endpoints
@config_app.post("/test/agent/{agent_id}")
async def test_agent(agent_id: str, request: TestRequest):
    """Test an individual agent"""
    try:
        from crewai import Agent, Task

        from agents import llm

        # Load agent configuration
        agent_config = config_manager.load_agent_config(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Create agent instance
        agent = Agent(
            role=agent_config.role,
            goal=agent_config.goal,
            backstory=agent_config.backstory,
            llm=llm,
            verbose=agent_config.verbose,
            memory=agent_config.memory,
            max_iter=agent_config.max_iter,
            allow_delegation=agent_config.allow_delegation,
        )

        # Create test task
        task_description = request.input_data.get(
            "task_description", "Test task")
        task = Task(
            description=task_description,
            agent=agent,
            expected_output="Test output")

        # Execute task and measure time
        start_time = time.time()
        try:
            result = task.execute()
            execution_time = time.time() - start_time
            status = "success"
            error_message = ""
        except Exception as e:
            execution_time = time.time() - start_time
            status = "error"
            error_message = str(e)
            result = f"Error: {str(e)}"

        # Save test result
        config_manager.save_test_result(
            "agent",
            agent_id,
            json.dumps(request.input_data),
            result,
            execution_time,
            status,
            error_message,
        )

        return {
            "agent_id": agent_id,
            "result": result,
            "execution_time": execution_time,
            "status": status,
            "error_message": error_message,
        }
    except Exception as e:
        logger.error(f"Error testing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.post("/test/prompt/{prompt_id}")
async def test_prompt_template(prompt_id: str, request: TestRequest):
    """Test a prompt template"""
    try:
        # Load prompt template
        prompt_template = config_manager.load_prompt_template(prompt_id)
        if not prompt_template:
            raise HTTPException(
                status_code=404,
                detail="Prompt template not found")

        start_time = time.time()
        try:
            # Render prompt with variables
            rendered_prompt = prompt_template.template
            variables = request.input_data.get("variables", {})

            for var_name, var_value in variables.items():
                rendered_prompt = rendered_prompt.replace(
                    f"{{{var_name}}}", str(var_value)
                )

            execution_time = time.time() - start_time
            status = "success"
            error_message = ""

            result = {
                "rendered_prompt": rendered_prompt,
                "variables_used": list(variables.keys()),
                "template_length": len(prompt_template.template),
                "rendered_length": len(rendered_prompt),
            }
        except Exception as e:
            execution_time = time.time() - start_time
            status = "error"
            error_message = str(e)
            result = f"Error: {str(e)}"

        # Save test result
        config_manager.save_test_result(
            "prompt",
            prompt_id,
            json.dumps(request.input_data),
            json.dumps(result),
            execution_time,
            status,
            error_message,
        )

        return {
            "prompt_id": prompt_id,
            "result": result,
            "execution_time": execution_time,
            "status": status,
            "error_message": error_message,
        }
    except Exception as e:
        logger.error(f"Error testing prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.get("/test-results/{entity_type}/{entity_id}")
async def get_test_results(entity_type: str, entity_id: str, limit: int = 10):
    """Get test results for an entity"""
    try:
        results = config_manager.get_test_results(
            entity_type, entity_id, limit)
        return results
    except Exception as e:
        logger.error(f"Error getting test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Test prompt endpoint
@config_app.post("/test-prompt")
async def test_prompt(request: Dict[str, Any]):
    """Test a prompt template with sample data"""
    try:
        prompt_template = request.get("template", "")
        variables = request.get("variables", {})

        # Simple template rendering
        rendered_prompt = prompt_template
        for var_name, var_value in variables.items():
            rendered_prompt = rendered_prompt.replace(
                f"{{{var_name}}}", str(var_value))

        return {
            "rendered_prompt": rendered_prompt,
            "variables_used": list(variables.keys()),
            "template_length": len(prompt_template),
            "rendered_length": len(rendered_prompt),
        }
    except Exception as e:
        logger.error(f"Error testing prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- MODEL MANAGEMENT ENDPOINTS ---


@config_app.get("/models", response_model=List[Dict[str, Any]])
def list_models():
    """List all available models"""
    models = config_manager.list_models()
    return [asdict(m) for m in models]


@config_app.post("/models", response_model=Dict[str, Any])
def add_model(model: Dict[str, Any]):
    """Add/register a new model"""
    model_obj = ModelConfig(**model)
    config_manager.save_model_config(
        model_obj, change_description="Added new model")
    return asdict(model_obj)


@config_app.delete("/models/{model_id}")
def delete_model(model_id: str):
    """Delete a model by ID"""
    success = config_manager.delete_model_config(model_id)
    return {"success": success}


@config_app.put("/agents/{agent_id}/model")
def assign_model_to_agent(agent_id: str, model_id: str):
    """Assign a model to an agent"""
    agent = config_manager.load_agent_config(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.model_id = model_id
    config_manager.save_agent_config(
        agent, change_description=f"Assigned model {model_id}"
    )
    return asdict(agent)


@config_app.get("/model-assignments", response_model=List[Dict[str, Any]])
def get_model_assignments():
    """Get all agents and their assigned models"""
    agents = config_manager.list_agents()
    models = {m.id: m for m in config_manager.list_models()}
    assignments = []
    for agent in agents:
        model = models.get(agent.model_id)
        assignments.append(
            {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "model_id": agent.model_id,
                "model_name": model.name if model else "(not found)",
                "model_provider": model.provider if model else None,
            }
        )
    return assignments


# Export the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(config_app, host="0.0.0.0", port=8001)
