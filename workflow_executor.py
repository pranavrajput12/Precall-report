"""
Enhanced workflow executor with configuration management and individual agent testing
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict

from crewai import Agent, Task
from langchain_openai import AzureChatOpenAI

from config_manager import config_manager
from main import safe_exec_python

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Enhanced workflow executor with configuration management"""

    def __init__(self):
        self.config_manager = config_manager
        self.agent_cache = {}
        self.prompt_cache = {}

    def _get_llm_for_agent(self, agent_config):
        """Instantiate the LLM for the agent based on its model_id"""
        model_id = getattr(agent_config, "model_id", "default")
        model_config = (self.config_manager.load_model_config(
            model_id) if model_id else None)
        if model_config and model_config.provider == "azure_openai":
            # Example for AzureChatOpenAI, extend for other providers
            return AzureChatOpenAI(
                openai_api_key=model_config.config.get("openai_api_key"),
                azure_endpoint=model_config.config.get("azure_endpoint"),
                deployment_name=model_config.config.get("deployment_name"),
                openai_api_version=model_config.config.get("openai_api_version"),
                temperature=model_config.config.get("temperature", 0.3),
                max_tokens=model_config.config.get("max_tokens", 2048),
                streaming=model_config.config.get("streaming", True),
                model_kwargs=model_config.config.get("model_kwargs", {}),
            )
        # Fallback to global llm
        from agents import llm

        return llm

    def _get_agent_from_config(self, agent_id: str) -> Agent:
        """Get agent instance from configuration"""
        if agent_id in self.agent_cache:
            return self.agent_cache[agent_id]

        agent_config = self.config_manager.load_agent_config(agent_id)
        if not agent_config:
            raise ValueError(f"Agent configuration not found: {agent_id}")

        llm_instance = self._get_llm_for_agent(agent_config)
        agent = Agent(
            role=agent_config.role,
            goal=agent_config.goal,
            backstory=agent_config.backstory,
            llm=llm_instance,
            verbose=agent_config.verbose,
            memory=agent_config.memory,
            max_iter=agent_config.max_iter,
            allow_delegation=agent_config.allow_delegation,
        )

        self.agent_cache[agent_id] = agent
        return agent

    def _get_prompt_template(self, prompt_id: str) -> str:
        """Get prompt template from configuration"""
        if prompt_id in self.prompt_cache:
            return self.prompt_cache[prompt_id]

        prompt_config = self.config_manager.load_prompt_template(prompt_id)
        if not prompt_config:
            raise ValueError(f"Prompt template not found: {prompt_id}")

        self.prompt_cache[prompt_id] = prompt_config.template
        return prompt_config.template

    def _render_prompt(self, prompt_template: str,
                       variables: Dict[str, Any]) -> str:
        """Render prompt template with variables"""
        rendered = prompt_template
        for var_name, var_value in variables.items():
            rendered = rendered.replace(f"{{{var_name}}}", str(var_value))
        return rendered

    async def test_agent(
        self, agent_id: str, test_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test an individual agent with given input"""
        start_time = time.time()

        try:
            # Get agent from configuration
            agent = self._get_agent_from_config(agent_id)

            # Create test task
            task_description = test_input.get("task_description", "Test task")
            expected_output = test_input.get("expected_output", "Test output")

            # Get prompt template if specified
            prompt_id = test_input.get("prompt_id")
            if prompt_id:
                prompt_template = self._get_prompt_template(prompt_id)
                variables = test_input.get("variables", {})
                task_description = self._render_prompt(
                    prompt_template, variables)

            task = Task(
                description=task_description,
                agent=agent,
                expected_output=expected_output,
            )

            # Execute task
            result = await asyncio.to_thread(task.execute)
            execution_time = time.time() - start_time

            # Save test result
            self.config_manager.save_test_result(
                "agent",
                agent_id,
                json.dumps(test_input),
                result,
                execution_time,
                "success",
                "",
            )

            return {
                "agent_id": agent_id,
                "result": result,
                "execution_time": execution_time,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Save test result
            self.config_manager.save_test_result(
                "agent",
                agent_id,
                json.dumps(test_input),
                f"Error: {error_message}",
                execution_time,
                "error",
                error_message,
            )

            return {
                "agent_id": agent_id,
                "result": f"Error: {error_message}",
                "execution_time": execution_time,
                "status": "error",
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }

    async def test_prompt(
        self, prompt_id: str, test_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a prompt template with given variables"""
        start_time = time.time()

        try:
            # Get prompt template
            prompt_template = self._get_prompt_template(prompt_id)
            variables = test_input.get("variables", {})

            # Render prompt
            rendered_prompt = self._render_prompt(prompt_template, variables)
            execution_time = time.time() - start_time

            result = {
                "rendered_prompt": rendered_prompt,
                "variables_used": list(variables.keys()),
                "template_length": len(prompt_template),
                "rendered_length": len(rendered_prompt),
            }

            # Save test result
            self.config_manager.save_test_result(
                "prompt",
                prompt_id,
                json.dumps(test_input),
                json.dumps(result),
                execution_time,
                "success",
                "",
            )

            return {
                "prompt_id": prompt_id,
                "result": result,
                "execution_time": execution_time,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Save test result
            self.config_manager.save_test_result(
                "prompt",
                prompt_id,
                json.dumps(test_input),
                f"Error: {error_message}",
                execution_time,
                "error",
                error_message,
            )

            return {
                "prompt_id": prompt_id,
                "result": f"Error: {error_message}",
                "execution_time": execution_time,
                "status": "error",
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }

    async def run_workflow_step(
        self, workflow_id: str, step_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single workflow step"""
        start_time = time.time()

        try:
            # Load workflow configuration
            workflow_config = self.config_manager.load_workflow_config(
                workflow_id)
            if not workflow_config:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Find the step
            step = None
            for s in workflow_config.steps:
                if s["id"] == step_id:
                    step = s
                    break

            if not step:
                raise ValueError(f"Step not found: {step_id}")

            # Execute step based on type
            if step.get("type") == "python":
                code = step.get("code", "")
                result = await asyncio.to_thread(safe_exec_python, code, input_data)
            elif step.get("agent_id"):
                agent = self._get_agent_from_config(step["agent_id"])

                # Get prompt template if specified
                prompt_template = ""
                if step.get("prompt_id"):
                    prompt_template = self._get_prompt_template(
                        step["prompt_id"])
                    prompt_template = self._render_prompt(
                        prompt_template, input_data)

                task = Task(
                    description=prompt_template or step.get("description", ""),
                    agent=agent,
                    expected_output=step.get("expected_output", "Step output"),
                )

                result = await asyncio.to_thread(task.execute)
            else:
                # Handle non-agent steps
                result = f"Executed step: {step['name']}"

            execution_time = time.time() - start_time

            # Save execution history
            self.config_manager.save_execution_history(
                workflow_id,
                step.get("agent_id", ""),
                step.get("prompt_id", ""),
                json.dumps(input_data),
                result,
                execution_time,
                "success",
                "",
            )

            return {
                "workflow_id": workflow_id,
                "step_id": step_id,
                "result": result,
                "execution_time": execution_time,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Save execution history
            self.config_manager.save_execution_history(
                workflow_id,
                step.get("agent_id", "") if "step" in locals() else "",
                step.get("prompt_id", "") if "step" in locals() else "",
                json.dumps(input_data),
                f"Error: {error_message}",
                execution_time,
                "error",
                error_message,
            )

            return {
                "workflow_id": workflow_id,
                "step_id": step_id,
                "result": f"Error: {error_message}",
                "execution_time": execution_time,
                "status": "error",
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }

    async def run_full_workflow(
        self, workflow_id: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a complete workflow using current configurations"""
        start_time = time.time()

        try:
            # Load workflow configuration
            workflow_config = self.config_manager.load_workflow_config(
                workflow_id)
            if not workflow_config:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # Sort steps by order
            steps = sorted(
                workflow_config.steps,
                key=lambda x: x.get(
                    "order",
                    0))

            # Execute steps sequentially
            results = {}
            context = input_data.copy()

            for step in steps:
                if not step.get("enabled", True):
                    continue

                step_result = await self.run_workflow_step(
                    workflow_id, step["id"], context
                )
                results[step["id"]] = step_result

                # Add step result to context for next steps
                context[f"{step['id']}_result"] = step_result["result"]

            execution_time = time.time() - start_time

            return {
                "workflow_id": workflow_id,
                "results": results,
                "execution_time": execution_time,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            return {
                "workflow_id": workflow_id,
                "results": {},
                "execution_time": execution_time,
                "status": "error",
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }

    def clear_cache(self):
        """Clear agent and prompt caches"""
        self.agent_cache.clear()
        self.prompt_cache.clear()


# Global executor instance
workflow_executor = WorkflowExecutor()
