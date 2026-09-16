from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

class DomainException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundException(DomainException):
    pass

class BusinessRuleException(DomainException):
    pass

async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message}
    )

async def business_rule_handler(request: Request, exc: BusinessRuleException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message}
    )

async def generic_domain_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message}
    )

def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(NotFoundException, not_found_handler)
    app.add_exception_handler(BusinessRuleException, business_rule_handler)
    app.add_exception_handler(DomainException, generic_domain_handler)