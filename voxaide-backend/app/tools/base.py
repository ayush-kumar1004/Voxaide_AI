from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.logging import logger

class AgentTool(ABC):
    """Abstract base class for all business actions and tools callable by the AI agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool (e.g. check_availability)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Clear description for the LLM explaining when and how to call this tool."""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON Schema defining input parameters and required fields."""
        pass

    @abstractmethod
    def execute(self, company_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the business tool.
        CRITICAL: company_id is ALWAYS passed to enforce tenant isolation.
        """
        pass

class ToolRegistry:
    """Registry that holds available tools and executes them safely."""

    def __init__(self):
        self._tools: Dict[str, AgentTool] = {}

    def register(self, tool: AgentTool):
        self._tools[tool.name] = tool
        logger.info(f"Registered agent tool: {tool.name}")

    def get(self, name: str) -> Optional[AgentTool]:
        return self._tools.get(name)

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return schema definitions formatted for LLM tool declaration."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema
            })
        return schemas

    def execute(self, name: str, company_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get(name)
        if not tool:
            logger.error("Tool execution failed: tool not found", tool_name=name, company_id=company_id)
            return {"success": False, "error": f"Tool '{name}' is not recognized or supported."}

        # Security: Never allow model-generated or client-supplied company_id to override authenticated context
        safe_kwargs = {k: v for k, v in (arguments or {}).items() if k != "company_id"}

        try:
            logger.info("Executing tool", tool_name=name, company_id=company_id, arguments=safe_kwargs)
            result = tool.execute(company_id=company_id, **safe_kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error("Tool execution exception", tool_name=name, company_id=company_id, error=str(e))
            return {"success": False, "error": str(e)}

# Global tool registry instance
tool_registry = ToolRegistry()
