from enum import Enum
import re

class ProjectPhase(Enum):
    DISCOVERY = "discovery"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"

class StakeholderType(Enum):
    CLIENT = "client"
    INTERNAL = "internal"
    VENDOR = "vendor"

class ContentType(Enum):
    DECISION = "decision"
    BLOCKER = "blocker"
    UPDATE = "update"
    QUESTION = "question"

class UrgencyLevel(Enum):
    IMMEDIATE = "immediate"
    THIS_WEEK = "this-week"
    NEXT_SPRINT = "next-sprint"
    BACKLOG = "backlog"

# Simple keyword-based tagging logic
def tag_email_content(content: str) -> dict:
    content_lower = content.lower()
    # Project phase
    if re.search(r"discovery|explore|research", content_lower):
        project_phase = ProjectPhase.DISCOVERY.value
    elif re.search(r"design|prototype|mockup", content_lower):
        project_phase = ProjectPhase.DESIGN.value
    elif re.search(r"implement|build|develop|code|deploy", content_lower):
        project_phase = ProjectPhase.IMPLEMENTATION.value
    elif re.search(r"review|retrospective|qa|test", content_lower):
        project_phase = ProjectPhase.REVIEW.value
    else:
        project_phase = None

    # Stakeholder type
    if re.search(r"client|customer|stakeholder", content_lower):
        stakeholder_type = StakeholderType.CLIENT.value
    elif re.search(r"team|internal|colleague|engineer|dev", content_lower):
        stakeholder_type = StakeholderType.INTERNAL.value
    elif re.search(r"vendor|partner|supplier", content_lower):
        stakeholder_type = StakeholderType.VENDOR.value
    else:
        stakeholder_type = None

    # Content type
    if re.search(r"decision|approved|agreed|chose|selected", content_lower):
        content_type = ContentType.DECISION.value
    elif re.search(r"blocker|issue|problem|risk|delay", content_lower):
        content_type = ContentType.BLOCKER.value
    elif re.search(r"update|progress|status|report", content_lower):
        content_type = ContentType.UPDATE.value
    elif re.search(r"question|ask|clarify|unclear", content_lower):
        content_type = ContentType.QUESTION.value
    else:
        content_type = None

    # Urgency level
    if re.search(r"asap|urgent|immediately|now", content_lower):
        urgency_level = UrgencyLevel.IMMEDIATE.value
    elif re.search(r"this week|by friday|end of week", content_lower):
        urgency_level = UrgencyLevel.THIS_WEEK.value
    elif re.search(r"next sprint|next week|upcoming", content_lower):
        urgency_level = UrgencyLevel.NEXT_SPRINT.value
    elif re.search(r"backlog|someday|future", content_lower):
        urgency_level = UrgencyLevel.BACKLOG.value
    else:
        urgency_level = None

    return {
        "project_phase": project_phase,
        "stakeholder_type": stakeholder_type,
        "content_type": content_type,
        "urgency_level": urgency_level
    } 