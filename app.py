from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from models import GenerateRequest, WorkflowOutput
from prompts import build_messages
from ai_client import generate_workflow
from parser import parse_and_validate

app = FastAPI(title="FlowMind", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/generate", response_model=WorkflowOutput)
async def generate(req: GenerateRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")

    messages = build_messages(req.prompt)
    try:
        raw = generate_workflow(
            prompt=messages[1]["content"],
            system=messages[0]["content"],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        return parse_and_validate(raw)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


app.mount("/", StaticFiles(directory="static", html=True), name="static")
