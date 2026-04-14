from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from src.data.schemas import IncomingMessage
from src.services.routing import route_message
from src.services.qa import QAService
from src.services.handoff import create_handoff

router = APIRouter()
qa_service = QAService()


@router.post("/webhook/twilio", response_class=PlainTextResponse)
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(""),
    ProfileName: str = Form(None),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
) -> str:
    incoming = IncomingMessage(
        from_number=From,
        message_text=Body or "",
        profile_name=ProfileName,
        media_url=MediaUrl0,
        media_content_type=MediaContentType0,
    )

    decision = route_message(incoming.message_text)

    if decision.route == "handoff":
        create_handoff(
            phone_number=incoming.from_number,
            name=incoming.profile_name,
            message=incoming.message_text,
            language=None,
        )
        return (
            "Thank you. Your message has been noted and will be shared through the "
            "appropriate support channel."
        )

    answer = qa_service.answer_question(incoming.message_text)
    return answer