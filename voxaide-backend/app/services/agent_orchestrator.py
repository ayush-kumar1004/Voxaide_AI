import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from app.providers.base import LLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.services.company_service import company_service, CompanyService
from app.services.conversation_service import conversation_service, ConversationService
from app.services.knowledge_service import knowledge_service, KnowledgeService
from app.tools.base import tool_registry, ToolRegistry
import app.tools.appointment_tools  # noqa: F401 - registers appointment tools
import app.tools.escalation_tool   # noqa: F401 - registers escalation tool
from app.prompts.system_prompts import build_system_prompt
from app.core.logging import logger

@dataclass
class AgentRequest:
    company_id: str
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: str = "web_text"  # web_text, web_voice, phone
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResponse:
    text: str
    conversation_id: str
    intent: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    should_escalate: bool = False
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "conversation_id": self.conversation_id,
            "intent": self.intent,
            "tool_calls": self.tool_calls,
            "sources": self.sources,
            "should_escalate": self.should_escalate,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata
        }

class AgentOrchestrator:
    """
    Central, channel-agnostic Agent Orchestrator.
    Decoupled from all audio codecs, Twilio, and telephony protocols.
    Processes structured conversational requests and returns structured responses.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        company_svc: Optional[CompanyService] = None,
        conversation_svc: Optional[ConversationService] = None,
        knowledge_svc: Optional[KnowledgeService] = None,
        tools: Optional[ToolRegistry] = None
    ):
        self.llm = llm_provider or GeminiProvider()
        self.company_svc = company_svc or company_service
        self.conversation_svc = conversation_svc or conversation_service
        self.knowledge_svc = knowledge_svc or knowledge_service
        self.tools = tools or tool_registry

    def process(self, request: AgentRequest) -> AgentResponse:
        start_time = time.time()
        logger.info(
            "Agent request received",
            company_id=request.company_id,
            channel=request.channel,
            conversation_id=request.conversation_id
        )

        # 1. Resolve Company Context
        company = self.company_svc.get_company(request.company_id)
        if not company:
            logger.error("Company context could not be resolved", company_id=request.company_id)
            return AgentResponse(
                text="Configuration error: requested company is not found or inactive.",
                conversation_id=request.conversation_id or "",
                latency_ms=round((time.time() - start_time) * 1000, 2)
            )

        # 2. Load dynamic company agent configuration
        agent_config = self.company_svc.get_agent_config(request.company_id)

        # 3. Resolve or initialize conversation session
        conversation = self.conversation_svc.get_or_create_conversation(
            company_id=request.company_id,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            channel=request.channel
        )

        # 4. Fetch recent conversation turn history
        history = self.conversation_svc.get_recent_messages(
            conversation_id=conversation.id,
            company_id=request.company_id,
            limit=agent_config.max_context_turns
        )

        # 5. Record user turn
        self.conversation_svc.add_message(
            conversation_id=conversation.id,
            company_id=request.company_id,
            role="user",
            content=request.message,
            metadata=request.metadata
        )

        # 6. Query Knowledge Base (RAG) with strict company_id isolation
        retrieved_knowledge = self.knowledge_svc.search(
            company_id=request.company_id,
            query=request.message,
            top_k=4
        )

        sources = [
            {
                "document_id": chunk.get("document_id", ""),
                "document_name": chunk.get("document_name", chunk.get("source", "Document")),
                "chunk_id": chunk.get("chunk_id", chunk.get("id", "")),
                "relevance_score": chunk.get("relevance_score", 1.0)
            }
            for chunk in retrieved_knowledge
        ]


        # 7. Construct dynamic system prompt with Prompt Injection Defense
        system_prompt = build_system_prompt(
            company=company,
            agent_config=agent_config,
            retrieved_knowledge=retrieved_knowledge
        )

        # 8. Available tool schemas
        tool_schemas = self.tools.get_schemas()

        # 9. Invoke LLM Provider
        executed_tools = []
        should_escalate = False
        try:
            llm_response = self.llm.generate(
                prompt=request.message,
                system_instruction=system_prompt,
                tools=tool_schemas if tool_schemas else None,
                history=history,
                temperature=0.3
            )
            reply_text = llm_response.content

            # 10. Execute tools if requested by LLM
            if llm_response.tool_calls:
                for call in llm_response.tool_calls:
                    tool_result = self.tools.execute(
                        name=call.name,
                        company_id=request.company_id,
                        arguments=call.arguments
                    )
                    executed_tools.append({
                        "name": call.name,
                        "arguments": call.arguments,
                        "result": tool_result
                    })
                    if call.name == "escalate_to_human":
                        should_escalate = True

                    # Anti-Hallucination Guard: If a tool failed, synthesize failure explanation
                    if not tool_result.get("success", False):
                        err_msg = tool_result.get("error", "The requested action could not be completed.")
                        if call.name == "book_appointment":
                            reply_text = f"I apologize, but I could not book your appointment: {err_msg} Would you like to select an alternative time?"
                        elif call.name == "reschedule_appointment":
                            reply_text = f"I could not reschedule your appointment: {err_msg}"
                        elif call.name == "cancel_appointment":
                            reply_text = f"I could not cancel the appointment: {err_msg}"
                        else:
                            reply_text = f"Action could not be completed: {err_msg}"
                    else:
                        # Tool succeeded: if reply_text is empty, use tool confirmation message
                        tool_msg = tool_result.get("result", {}).get("message")
                        if not reply_text and tool_msg:
                            reply_text = tool_msg

            # Strict Anti-Fabrication Check for Booking:
            # If the model claims an appointment was booked, but no booking tool succeeded, correct it
            booking_claim_keywords = ["has been booked", "successfully booked", "have booked your appointment", "confirmed your appointment", "appointment is booked"]
            claims_booking = any(kw in reply_text.lower() for kw in booking_claim_keywords)
            has_successful_booking = any(
                t.get("name") == "book_appointment" and t.get("result", {}).get("success") is True
                for t in executed_tools
            )

            if claims_booking and not has_successful_booking:
                logger.warning("Model fabricated booking without successful book_appointment tool execution. Intercepting response.", company_id=request.company_id)
                failed_booking = next((t for t in executed_tools if t.get("name") == "book_appointment"), None)
                if failed_booking:
                    err = failed_booking.get("result", {}).get("error", "The requested slot is unavailable.")
                    reply_text = f"I apologize, but your appointment could not be booked: {err} Would you like to try another date or time?"
                else:
                    reply_text = "To confirm your appointment, please provide your name, phone number, and preferred date and time so I can book it for you."

        except Exception as e:
            logger.error("LLM generation failed in orchestrator", error=str(e), company_id=request.company_id)
            reply_text = agent_config.escalation_message or (
                "I apologize, but I am having trouble processing your request right now. "
                "Let me connect you with a team member."
            )
            should_escalate = True

        # 11. Record assistant response to memory
        self.conversation_svc.add_message(
            conversation_id=conversation.id,
            company_id=request.company_id,
            role="assistant",
            content=reply_text,
            metadata={"tool_calls": executed_tools, "sources": sources}
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            "Agent response generated",
            company_id=request.company_id,
            conversation_id=conversation.id,
            latency_ms=latency_ms,
            tools_used=len(executed_tools)
        )

        return AgentResponse(
            text=reply_text,
            conversation_id=conversation.id,
            tool_calls=executed_tools,
            sources=sources,
            should_escalate=should_escalate,
            latency_ms=latency_ms
        )

# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()
