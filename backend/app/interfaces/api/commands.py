from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.application.commands.dto import CommandLogDto, CommandRequest
from app.application.commands.service import CommandService
from app.domain.commands.invoker import UnknownCommandError
from app.infrastructure.actuator_state_repository import ActuatorNotFoundError
from app.infrastructure.db import get_session


router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.post(
    "",
    response_model=CommandLogDto,
    responses={
        400: {"description": "Unknown command type; no log is written."},
        404: {"description": "Actuator not found."},
        409: {
            "model": CommandLogDto,
            "description": "Command rejected by the saved actuator state.",
        },
    },
)
def execute_command(
    body: CommandRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> CommandLogDto:
    """Execute a command. Success and execution failure both return HTTP 200."""
    service = CommandService(session)

    try:
        result = service.execute(body)
    except ActuatorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result.status == "rejected":
        response.status_code = 409

    return result


@router.get("", response_model=list[CommandLogDto])
def list_commands(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[CommandLogDto]:
    """Return command history, newest first."""
    return CommandService(session).list_recent(limit)