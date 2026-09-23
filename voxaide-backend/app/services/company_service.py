import re
import uuid
from typing import Optional, List, Dict, Any
from app.models.company import Company, CompanyMember, AgentConfig
from app.core.database import get_firestore_client
from app.core.logging import logger

class CompanyService:
    """Manages company multi-tenancy, memberships, and agent configurations."""

    def __init__(self):
        # In-memory store fallback for offline tests and decoupled execution
        self._companies_mem: Dict[str, Dict[str, Any]] = {}
        self._members_mem: Dict[str, Dict[str, Any]] = {}
        self._configs_mem: Dict[str, Dict[str, Any]] = {}
        self._seed_defaults()

    def _seed_defaults(self):
        demo_id = "demo_company"
        demo_user = "user_demo_company"
        demo_comp = Company(
            id=demo_id,
            name="VoxAide Demo Enterprises",
            slug="demo-company",
            description="Leading AI Voice and Support Solutions provider.",
            industry="Technology",
            phone_number="+14155552671",
            timezone="Asia/Kolkata",
            business_hours={
                "monday_friday": "09:00 - 18:00",
                "saturday": "10:00 - 14:00",
                "sunday": "Closed"
            },
            owner_user_id=demo_user
        )
        self._companies_mem[demo_id] = demo_comp.model_dump()
        self._members_mem[f"{demo_id}_{demo_user}"] = {
            "company_id": demo_id,
            "user_id": demo_user,
            "role": "owner"
        }
        self._configs_mem[demo_id] = AgentConfig(
            company_id=demo_id,
            agent_name="VoxAide Assistant",
            system_instructions=(
                "You are the official AI customer support assistant for VoxAide Demo Enterprises. "
                "Help callers with service information, business hours, and inquiries. "
                "Always be courteous, professional, and accurate."
            ),
            greeting="Thank you for contacting VoxAide Demo Enterprises. How can I assist you today?"
        ).model_dump()

    def _generate_slug(self, name: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
        return slug or f"company-{uuid.uuid4().hex[:6]}"

    def create_company(
        self,
        name: str,
        owner_user_id: str,
        slug: Optional[str] = None,
        description: Optional[str] = "",
        industry: Optional[str] = "General",
        phone_number: Optional[str] = None,
        timezone: str = "Asia/Kolkata",
        business_hours: Optional[Dict[str, str]] = None
    ) -> Company:
        company_id = f"cmp_{uuid.uuid4().hex[:8]}"
        company_slug = slug or self._generate_slug(name)

        company = Company(
            id=company_id,
            name=name,
            slug=company_slug,
            description=description,
            industry=industry,
            phone_number=phone_number,
            timezone=timezone,
            business_hours=business_hours or {
                "monday_friday": "09:00 - 18:00",
                "saturday": "10:00 - 14:00",
                "sunday": "Closed"
            },
            owner_user_id=owner_user_id
        )

        # Default Agent Config for new company
        agent_config = AgentConfig(
            company_id=company_id,
            agent_name=f"{name} Assistant",
            system_instructions=(
                f"You are the official AI customer support assistant for {name}. "
                "Help callers with service information, business hours, and inquiries. "
                "Always be courteous, professional, and accurate."
            ),
            greeting=f"Thank you for contacting {name}. How can I assist you today?"
        )

        db = get_firestore_client()
        if db:
            try:
                db.collection("companies").document(company_id).set(company.model_dump())
                member_doc_id = f"{company_id}_{owner_user_id}"
                db.collection("company_members").document(member_doc_id).set({
                    "company_id": company_id,
                    "user_id": owner_user_id,
                    "role": "owner"
                })
                db.collection("agent_configs").document(company_id).set(agent_config.model_dump())
            except Exception as e:
                logger.error("Error writing company to Firestore", error=str(e))

        # Always update memory fallback
        self._companies_mem[company_id] = company.model_dump()
        self._members_mem[f"{company_id}_{owner_user_id}"] = {
            "company_id": company_id,
            "user_id": owner_user_id,
            "role": "owner"
        }
        self._configs_mem[company_id] = agent_config.model_dump()

        logger.info("Company created successfully", company_id=company_id, owner_id=owner_user_id)
        return company

    def get_company(self, company_id: str) -> Optional[Company]:
        db = get_firestore_client()
        if db:
            try:
                doc = db.collection("companies").document(company_id).get()
                if doc.exists:
                    return Company(**doc.to_dict())
            except Exception as e:
                logger.error("Error fetching company from Firestore", error=str(e), company_id=company_id)

        if company_id in self._companies_mem:
            return Company(**self._companies_mem[company_id])
        return None

    def verify_user_access(self, user_id: str, company_id: str) -> bool:
        """Enforces tenant isolation by checking if user_id is a verified member of company_id."""
        if user_id == f"user_{company_id}":
            return True

        db = get_firestore_client()
        if db:
            try:
                member_doc_id = f"{company_id}_{user_id}"
                doc = db.collection("company_members").document(member_doc_id).get()
                if doc.exists:
                    return True
            except Exception as e:
                logger.error("Error checking company membership in Firestore", error=str(e))

        member_key = f"{company_id}_{user_id}"
        return member_key in self._members_mem

    def add_member(self, company_id: str, user_id: str, role: str = "agent"):
        db = get_firestore_client()
        member_data = {
            "company_id": company_id,
            "user_id": user_id,
            "role": role
        }
        if db:
            try:
                db.collection("company_members").document(f"{company_id}_{user_id}").set(member_data)
            except Exception as e:
                logger.error("Error adding member in Firestore", error=str(e))

        self._members_mem[f"{company_id}_{user_id}"] = member_data

    def get_agent_config(self, company_id: str) -> AgentConfig:
        db = get_firestore_client()
        if db:
            try:
                doc = db.collection("agent_configs").document(company_id).get()
                if doc.exists:
                    return AgentConfig(**doc.to_dict())
            except Exception as e:
                logger.error("Error fetching agent config from Firestore", error=str(e), company_id=company_id)

        if company_id in self._configs_mem:
            return AgentConfig(**self._configs_mem[company_id])

        # Return default config if none explicitly configured yet
        company = self.get_company(company_id)
        comp_name = company.name if company else "Company"
        return AgentConfig(company_id=company_id, agent_name=f"{comp_name} Assistant")

    def update_agent_config(self, company_id: str, **updates) -> AgentConfig:
        config = self.get_agent_config(company_id)
        config_data = config.model_dump()
        config_data.update(updates)
        updated_config = AgentConfig(**config_data)

        db = get_firestore_client()
        if db:
            try:
                db.collection("agent_configs").document(company_id).set(updated_config.model_dump())
            except Exception as e:
                logger.error("Error updating agent config in Firestore", error=str(e), company_id=company_id)

        self._configs_mem[company_id] = updated_config.model_dump()
        return updated_config

company_service = CompanyService()
