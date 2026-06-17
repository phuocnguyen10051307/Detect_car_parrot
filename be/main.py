from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from pydantic import BaseModel

from parser import (
    detect_card_color,
    detect_document_type,
    extract_engine,
    extract_frame,
    extract_issue_date,
    extract_plate,
)


class OCRUrlRequest(BaseModel):
    image_url: str


app = FastAPI(title="Vehicle OCR Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ocr = PaddleOCR(lang="vi", use_angle_cls=True)


def save_bytes_to_temp(data, suffix):
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(data)
    return temp_path


def extract_vehicle_info(image_path, image_url=None):
    card_type = detect_card_color(image_path)
    result = ocr.ocr(str(image_path))
    if not result or not result[0]:
        raise HTTPException(status_code=400, detail="No text detected in image")

    lines = [line[1][0] for line in result[0]]
    document_type = detect_document_type(lines)["document_type"]

    return {
        "document_type": document_type,
        "card_color": card_type,
        "image_url": image_url,
        "plate": extract_plate(lines),
        "engine": extract_engine(lines, card_type),
        "frame": extract_frame(lines, card_type),
        "issue_date": extract_issue_date(lines, card_type),
    }


def download_image(image_url):
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        raise HTTPException(status_code=400, detail=f"Cannot download image: {error}") from error

    content_type = response.headers.get("content-type", "")
    if "image" not in content_type:
        raise HTTPException(status_code=400, detail="URL does not point to an image")

    suffix = Path(image_url.split("?")[0]).suffix or ".jpg"
    return save_bytes_to_temp(response.content, suffix)


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/ocr")
async def run_ocr(file: UploadFile = File(...)):
    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    temp_path = save_bytes_to_temp(await file.read(), suffix)

    try:
        return extract_vehicle_info(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post("/ocr/url")
def run_ocr_by_url(payload: OCRUrlRequest):
    temp_path = download_image(payload.image_url)

    try:
        return extract_vehicle_info(temp_path, image_url=payload.image_url)
    finally:
        if temp_path.exists():
            temp_path.unlink()
