"""
Google Agent Space implementation.
Demonstrates collaborative agent environments and multi-agent workflows.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from google.cloud import aiplatform
from config.auth import auth
from config.settings import settings


class AgentSpace:
    """
    Google Agent Space implementation for collaborative agent environments.
    """
    
    def __init__(self, space_id: str, name: str = "Collaborative Agent Space"):
        self.space_id = space_id
        self.name = name
        self.logger = logging.getLogger(f"agent_space.{space_id}")
        self.vertex_ai = auth.get_vertex_ai_client()
        
        # Agent registry
        self.agents: Dict[str, 'SpaceAgent'] = {}
        
        # Shared resources
        self.shared_memory: Dict[str, Any] = {}
        self.workflows: Dict[str, 'Workflow'] = {}
        
        # Communication channels
        self.message_queue: List[Dict[str, Any]] = []
        
        self.logger.info(f"Agent Space '{name}' initialized with ID: {space_id}")
    
    def register_agent(self, agent: 'SpaceAgent') -> bool:
        """Register an agent in the space."""
        try:
            if agent.agent_id in self.agents:
                self.logger.warning(f"Agent {agent.agent_id} already registered")
                return False
            
            self.agents[agent.agent_id] = agent
            agent.space = self
            self.logger.info(f"Agent {agent.agent_id} registered in space {self.space_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the space."""
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.space = None
                del self.agents[agent_id]
                self.logger.info(f"Agent {agent_id} unregistered from space {self.space_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error unregistering agent: {e}")
            return False
    
    async def broadcast_message(self, sender_id: str, message: str, message_type: str = "general") -> None:
        """Broadcast a message to all agents in the space."""
        try:
            message_data = {
                "sender_id": sender_id,
                "message": message,
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "space_id": self.space_id
            }
            
            self.message_queue.append(message_data)
            
            # Notify all agents
            for agent_id, agent in self.agents.items():
                if agent_id != sender_id:
                    await agent.receive_message(message_data)
            
            self.logger.info(f"Message broadcasted from {sender_id} to {len(self.agents) - 1} agents")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting message: {e}")
    
    async def send_direct_message(self, sender_id: str, recipient_id: str, message: str) -> bool:
        """Send a direct message to a specific agent."""
        try:
            if recipient_id not in self.agents:
                self.logger.warning(f"Recipient agent {recipient_id} not found")
                return False
            
            message_data = {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message": message,
                "message_type": "direct",
                "timestamp": datetime.now().isoformat(),
                "space_id": self.space_id
            }
            
            await self.agents[recipient_id].receive_message(message_data)
            self.logger.info(f"Direct message sent from {sender_id} to {recipient_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending direct message: {e}")
            return False
    
    def set_shared_memory(self, key: str, value: Any) -> None:
        """Set a value in shared memory."""
        self.shared_memory[key] = value
        self.logger.info(f"Shared memory updated: {key} = {value}")
    
    def get_shared_memory(self, key: str) -> Any:
        """Get a value from shared memory."""
        return self.shared_memory.get(key)
    
    def create_workflow(self, workflow_id: str, name: str, steps: List[Dict[str, Any]]) -> 'Workflow':
        """Create a new workflow in the agent space."""
        try:
            workflow = Workflow(workflow_id, name, steps, self)
            self.workflows[workflow_id] = workflow
            self.logger.info(f"Workflow '{name}' created with ID: {workflow_id}")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Error creating workflow: {e}")
            raise
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow."""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = self.workflows[workflow_id]
            result = await workflow.execute(input_data or {})
            
            self.logger.info(f"Workflow {workflow_id} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            raise
    
    def get_space_status(self) -> Dict[str, Any]:
        """Get the current status of the agent space."""
        return {
            "space_id": self.space_id,
            "name": self.name,
            "agent_count": len(self.agents),
            "registered_agents": list(self.agents.keys()),
            "workflow_count": len(self.workflows),
            "shared_memory_keys": list(self.shared_memory.keys()),
            "pending_messages": len(self.message_queue)
        }


class SpaceAgent:
    """
    An agent that can participate in an Agent Space.
    """
    
    def __init__(self, agent_id: str, name: str, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities or []
        self.space: Optional[AgentSpace] = None
        self.logger = logging.getLogger(f"space_agent.{agent_id}")
        
        # Agent state
        self.local_memory: Dict[str, Any] = {}
        self.message_history: List[Dict[str, Any]] = []
        
        self.logger.info(f"Space Agent '{name}' initialized with ID: {agent_id}")
    
    async def join_space(self, space: AgentSpace) -> bool:
        """Join an agent space."""
        return space.register_agent(self)
    
    async def leave_space(self) -> bool:
        """Leave the current agent space."""
        if self.space:
            return self.space.unregister_agent(self.agent_id)
        return False
    
    async def send_message(self, message: str, message_type: str = "general") -> None:
        """Send a message to the agent space."""
        if self.space:
            await self.space.broadcast_message(self.agent_id, message, message_type)
        else:
            self.logger.warning("Agent not in a space, cannot send message")
    
    async def send_direct_message(self, recipient_id: str, message: str) -> bool:
        """Send a direct message to another agent."""
        if self.space:
            return await self.space.send_direct_message(self.agent_id, recipient_id, message)
        else:
            self.logger.warning("Agent not in a space, cannot send direct message")
            return False
    
    async def receive_message(self, message_data: Dict[str, Any]) -> None:
        """Receive a message from the agent space."""
        self.message_history.append(message_data)
        self.logger.info(f"Received message from {message_data['sender_id']}: {message_data['message'][:50]}...")
        
        # Process the message based on type
        await self.process_message(message_data)
    
    async def process_message(self, message_data: Dict[str, Any]) -> None:
        """Process a received message. Override in subclasses."""
        # Default implementation - just log the message
        self.logger.info(f"Processing message: {message_data['message_type']}")
    
    def set_local_memory(self, key: str, value: Any) -> None:
        """Set a value in local memory."""
        self.local_memory[key] = value
    
    def get_local_memory(self, key: str) -> Any:
        """Get a value from local memory."""
        return self.local_memory.get(key)
    
    async def perform_task(self, task: str, context: Dict[str, Any] = None) -> Any:
        """Perform a task. Override in subclasses."""
        self.logger.info(f"Performing task: {task}")
        return {"status": "completed", "task": task}


class Workflow:
    """
    A workflow that can be executed in an agent space.
    """
    
    def __init__(self, workflow_id: str, name: str, steps: List[Dict[str, Any]], space: AgentSpace):
        self.workflow_id = workflow_id
        self.name = name
        self.steps = steps
        self.space = space
        self.logger = logging.getLogger(f"workflow.{workflow_id}")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow."""
        try:
            self.logger.info(f"Starting workflow execution: {self.name}")
            
            current_data = input_data.copy()
            results = []
            
            for i, step in enumerate(self.steps):
                step_id = step.get("id", f"step_{i}")
                step_type = step.get("type", "agent_task")
                
                self.logger.info(f"Executing step {i + 1}/{len(self.steps)}: {step_id}")
                
                if step_type == "agent_task":
                    result = await self._execute_agent_task(step, current_data)
                elif step_type == "condition":
                    result = await self._execute_condition(step, current_data)
                elif step_type == "data_transform":
                    result = await self._execute_data_transform(step, current_data)
                else:
                    result = {"error": f"Unknown step type: {step_type}"}
                
                results.append({
                    "step_id": step_id,
                    "step_type": step_type,
                    "result": result
                })
                
                # Update current data with step result
                current_data.update(result)
            
            final_result = {
                "workflow_id": self.workflow_id,
                "workflow_name": self.name,
                "status": "completed",
                "steps_executed": len(results),
                "final_data": current_data,
                "step_results": results
            }
            
            self.logger.info(f"Workflow execution completed: {self.name}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            return {
                "workflow_id": self.workflow_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _execute_agent_task(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent task step."""
        agent_id = step.get("agent_id")
        task = step.get("task")
        
        if agent_id not in self.space.agents:
            return {"error": f"Agent {agent_id} not found"}
        
        agent = self.space.agents[agent_id]
        result = await agent.perform_task(task, data)
        
        return {"agent_result": result}
    
    async def _execute_condition(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a condition step."""
        condition = step.get("condition")
        condition_func = eval(condition)  # In production, use a safer evaluation method
        
        result = condition_func(data)
        
        return {"condition_result": result}
    
    async def _execute_data_transform(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data transformation step."""
        transform = step.get("transform")
        transform_func = eval(transform)  # In production, use a safer evaluation method
        
        result = transform_func(data)
        
        return {"transform_result": result}


# Example usage
async def main():
    """Example usage of Agent Space."""
    # Create an agent space
    space = AgentSpace("example-space", "Example Collaborative Space")
    
    # Create agents
    agent1 = SpaceAgent("agent1", "Research Agent", ["research", "analysis"])
    agent2 = SpaceAgent("agent2", "Writing Agent", ["writing", "summarization"])
    agent3 = SpaceAgent("agent3", "Review Agent", ["review", "validation"])
    
    # Join agents to the space
    await agent1.join_space(space)
    await agent2.join_space(space)
    await agent3.join_space(space)
    
    # Create a workflow
    workflow_steps = [
        {
            "id": "research",
            "type": "agent_task",
            "agent_id": "agent1",
            "task": "Research topic: AI trends"
        },
        {
            "id": "write",
            "type": "agent_task",
            "agent_id": "agent2",
            "task": "Write summary of research"
        },
        {
            "id": "review",
            "type": "agent_task",
            "agent_id": "agent3",
            "task": "Review and validate content"
        }
    ]
    
    workflow = space.create_workflow("research-workflow", "Research and Writing Workflow", workflow_steps)
    
    # Execute the workflow
    result = await space.execute_workflow("research-workflow", {"topic": "AI trends 2024"})
    print(f"Workflow result: {result}")
    
    # Get space status
    status = space.get_space_status()
    print(f"Space status: {status}")


if __name__ == "__main__":
    asyncio.run(main()) 