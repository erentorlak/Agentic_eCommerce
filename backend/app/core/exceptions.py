"""
Custom Exception Classes for Migration System

Following best practices for error handling:
- Specific exception types for different error categories
- Proper error codes and messages
- Context preservation for debugging
- HTTP status code mapping
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status


class BaseCustomException(Exception):
    """Base exception class for all custom exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "type": self.__class__.__name__
        }


class ValidationError(BaseCustomException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        context = {}
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationError(BaseCustomException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(BaseCustomException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, message: str = "Insufficient permissions", required_permission: str = None):
        context = {}
        if required_permission:
            context["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            context=context,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundError(BaseCustomException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"{resource_type} with identifier '{identifier}' not found",
            error_code="RESOURCE_NOT_FOUND",
            context={"resource_type": resource_type, "identifier": identifier},
            status_code=status.HTTP_404_NOT_FOUND
        )


class ResourceConflictError(BaseCustomException):
    """Raised when a resource already exists or conflicts with existing data"""
    
    def __init__(self, resource_type: str, identifier: str, conflict_reason: str = None):
        context = {
            "resource_type": resource_type,
            "identifier": identifier
        }
        if conflict_reason:
            context["conflict_reason"] = conflict_reason
        
        super().__init__(
            message=f"{resource_type} '{identifier}' already exists or conflicts with existing data",
            error_code="RESOURCE_CONFLICT",
            context=context,
            status_code=status.HTTP_409_CONFLICT
        )


class DatabaseError(BaseCustomException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        context = {}
        if operation:
            context["operation"] = operation
        if table:
            context["table"] = table
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            context=context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExternalServiceError(BaseCustomException):
    """Raised when external service calls fail"""
    
    def __init__(self, service_name: str, message: str, status_code: int = None):
        context = {"service_name": service_name}
        if status_code:
            context["external_status_code"] = status_code
        
        super().__init__(
            message=f"External service '{service_name}' error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            context=context,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class AIServiceError(ExternalServiceError):
    """Raised when AI service calls fail"""
    
    def __init__(self, message: str, model: str = None, tokens_used: int = None):
        context = {}
        if model:
            context["model"] = model
        if tokens_used:
            context["tokens_used"] = tokens_used
        
        super().__init__(
            service_name="AI Service",
            message=message
        )
        self.context.update(context)


class RateLimitError(BaseCustomException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, limit: int, window: str, retry_after: int = None):
        context = {
            "limit": limit,
            "window": window
        }
        if retry_after:
            context["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            error_code="RATE_LIMIT_EXCEEDED",
            context=context,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class BusinessLogicError(BaseCustomException):
    """Raised when business rules are violated"""
    
    def __init__(self, message: str, rule: str = None):
        context = {}
        if rule:
            context["violated_rule"] = rule
        
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            context=context,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class MigrationError(BaseCustomException):
    """Raised when migration-specific operations fail"""
    
    def __init__(self, message: str, migration_id: str = None, stage: str = None):
        context = {}
        if migration_id:
            context["migration_id"] = migration_id
        if stage:
            context["stage"] = stage
        
        super().__init__(
            message=message,
            error_code="MIGRATION_ERROR",
            context=context,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ConfigurationError(BaseCustomException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str, config_key: str = None):
        context = {}
        if config_key:
            context["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class WorkflowError(BaseCustomException):
    """Raised when LangGraph workflow operations fail"""
    
    def __init__(self, message: str, workflow_id: str = None, current_stage: str = None):
        context = {}
        if workflow_id:
            context["workflow_id"] = workflow_id
        if current_stage:
            context["current_stage"] = current_stage
        
        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            context=context,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Exception mapping for HTTP responses
EXCEPTION_STATUS_MAP = {
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
    ResourceConflictError: status.HTTP_409_CONFLICT,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    AIServiceError: status.HTTP_502_BAD_GATEWAY,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    BusinessLogicError: status.HTTP_400_BAD_REQUEST,
    MigrationError: status.HTTP_400_BAD_REQUEST,
    ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    WorkflowError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def create_http_exception(exception: BaseCustomException) -> HTTPException:
    """Convert custom exception to FastAPI HTTPException"""
    return HTTPException(
        status_code=exception.status_code,
        detail=exception.to_dict()
    )