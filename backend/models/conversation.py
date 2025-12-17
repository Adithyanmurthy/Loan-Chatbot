"""
Conversation and agent-related models
Based on requirements: 1.4, 2.1, 3.1, 4.1
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class AgentType(str, Enum):
    """Enumeration for agent types"""
    MASTER = "master"
    SALES = "sales"
    VERIFICATION = "verification"
    UNDERWRITING = "underwriting"
    SANCTION = "sanction"
    SANCTION_LETTER = "sanction_letter"


class TaskType(str, Enum):
    """Enumeration for task types"""
    SALES = "sales"
    VERIFICATION = "verification"
    UNDERWRITING = "underwriting"
    DOCUMENT_GENERATION = "document_generation"
    GENERATE_SANCTION_LETTER = "generate_sanction_letter"
    CREATE_DOWNLOAD_LINK = "create_download_link"
    NOTIFY_CUSTOMER = "notify_customer"


class TaskStatus(str, Enum):
    """Enumeration for task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorSeverity(str, Enum):
    """Enumeration for error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorLog(BaseModel):
    """Model for error logging"""
    id: str = Field(..., description="Unique error identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    message: str = Field(..., min_length=1, description="Error message")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'ErrorLog':
        """Create model from dictionary"""
        return cls(**data)


class ConversationContext(BaseModel):
    """Model for conversation context and state"""
    session_id: str = Field(..., description="Unique session identifier")
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    current_agent: AgentType = Field(default=AgentType.MASTER, description="Currently active agent")
    conversation_stage: str = Field(..., min_length=1, description="Current conversation stage")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Data collected during conversation")
    pending_tasks: List[str] = Field(default_factory=list, description="List of pending task IDs")
    completed_tasks: List[str] = Field(default_factory=list, description="List of completed task IDs")
    errors: List[ErrorLog] = Field(default_factory=list, description="List of errors encountered")
    created_at: datetime = Field(default_factory=datetime.now, description="Context creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Context last update timestamp")

    @validator('conversation_stage')
    def validate_stage(cls, v):
        """Validate conversation stage"""
        valid_stages = [
            'initiation', 'information_collection', 'sales_negotiation',
            'verification', 'underwriting', 'document_upload',
            'sanction_generation', 'sanction_letter_generation', 
            'completion', 'error_handling'
        ]
        if v not in valid_stages:
            raise ValueError(f'Invalid conversation stage. Must be one of: {", ".join(valid_stages)}')
        return v

    def add_collected_data(self, key: str, value: Any):
        """Add data to collected information"""
        self.collected_data[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }

    def add_error(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Optional[Dict[str, Any]] = None):
        """Add an error to the context"""
        error = ErrorLog(
            id=f"err_{len(self.errors) + 1}_{datetime.now().timestamp()}",
            message=message,
            severity=severity,
            context=context
        )
        self.errors.append(error)

    def add_pending_task(self, task_id: str):
        """Add a task to pending list"""
        if task_id not in self.pending_tasks:
            self.pending_tasks.append(task_id)
        self.update_timestamp()

    def complete_task(self, task_id: str):
        """Move task from pending to completed"""
        if task_id in self.pending_tasks:
            self.pending_tasks.remove(task_id)
        if task_id not in self.completed_tasks:
            self.completed_tasks.append(task_id)
        self.update_timestamp()

    def switch_agent(self, new_agent: AgentType, new_stage: str):
        """Switch to a different agent and stage"""
        self.current_agent = new_agent
        self.conversation_stage = new_stage
        self.updated_at = datetime.now()
    
    def update_timestamp(self):
        """Update the last modified timestamp"""
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'ConversationContext':
        """Create model from dictionary"""
        return cls(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentTask(BaseModel):
    """Model for agent task management"""
    id: str = Field(..., description="Unique task identifier")
    type: TaskType = Field(..., description="Type of task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    input: Dict[str, Any] = Field(..., description="Task input parameters")
    output: Optional[Dict[str, Any]] = Field(None, description="Task output results")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")

    def start_task(self):
        """Mark task as in progress"""
        self.status = TaskStatus.IN_PROGRESS

    def complete_task(self, output: Dict[str, Any]):
        """Mark task as completed with output"""
        self.status = TaskStatus.COMPLETED
        self.output = output
        self.completed_at = datetime.now()
        self.error = None

    def fail_task(self, error_message: str):
        """Mark task as failed with error message"""
        self.status = TaskStatus.FAILED
        self.error = error_message
        self.completed_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentTask':
        """Create model from dictionary"""
        return cls(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatMessage(BaseModel):
    """Model for chat messages"""
    id: str = Field(..., description="Unique message identifier")
    content: str = Field(..., min_length=1, description="Message content")
    sender: str = Field(..., description="Message sender (user/agent)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    message_type: str = Field(default="text", description="Type of message")
    agent_type: Optional[AgentType] = Field(None, description="Type of agent if sender is agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

    @validator('sender')
    def validate_sender(cls, v):
        """Validate message sender"""
        valid_senders = ['user', 'agent']
        if v not in valid_senders:
            raise ValueError(f'Sender must be one of: {", ".join(valid_senders)}')
        return v

    @validator('message_type')
    def validate_message_type(cls, v):
        """Validate message type"""
        valid_types = ['text', 'file', 'system', 'download_link']
        if v not in valid_types:
            raise ValueError(f'Message type must be one of: {", ".join(valid_types)}')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return self.dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'ChatMessage':
        """Create model from dictionary"""
        return cls(**data)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }