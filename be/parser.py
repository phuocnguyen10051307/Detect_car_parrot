import re
import unicodedata
from pathlib import Path

import cv2
import numpy as np


PLATE_PATTERNS = (
    r"\d{2}[A-Z]-\d{3}\.\d{2}",
    r"\d{2}[A-Z]-\d{4,5}",
)

ENGINE_KEYWORDS = ("engine", "so may", "somay", "s6 may")
FRAME_KEYWORDS = ("chassis", "so khung", "s6 khung", "sokhung")
OLD_DOCUMENT_KEYWORDS = (
    "date of expiry",
    "gia tri den ngay",
    "co gia tri den ngay",
    "dang ky lan dau",
    "first registration",
)
NEW_DOCUMENT_KEYWORDS = (
    "chung nhan dang ky xe",
    "giay chung nhan dang ky xe",
    "ngay cap",
    "cap ngay",
    "co hieu luc den",
    "so seri",
    "serial",
)
OLD_ISSUE_EXCLUDE_KEYWORDS = ("date of expiry", "gia tri den ngay", "co gia tri den ngay")
FIRST_REG_KEYWORDS = ("dang ky lan dau", "first registration")
NEW_ISSUE_KEYWORDS = ("ngay cap", "cap ngay", "issued date", "date of issue")


def strip_accents(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_text(text):
    text = strip_accents(text or "")
    text = (
        text.lower()
        .replace("Â°", " ")
        .replace("Âº", " ")
        .replace("Ã‚Â°", " ")
        .replace("Ã‚Âº", " ")
        .replace("'", " ")
    )
    text = re.sub(r"[^a-z0-9:/.\- ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_code(text):
    text = text.strip().upper()
    return re.sub(r"[^A-Z0-9]", "", text)


def looks_like_vehicle_code(text, min_length):
    return len(text) >= min_length and any(char.isdigit() for char in text)


def count_keyword_hits(lines, keywords):
    normalized_lines = [normalize_text(line) for line in lines]
    score = 0
    for line in normalized_lines:
        for keyword in keywords:
            if keyword in line:
                score += 1
    return score


def detect_document_type(lines):
    old_score = count_keyword_hits(lines, OLD_DOCUMENT_KEYWORDS)
    new_score = count_keyword_hits(lines, NEW_DOCUMENT_KEYWORDS)

    if old_score > new_score and old_score > 0:
        document_type = "old"
    elif new_score > old_score and new_score > 0:
        document_type = "new"
    else:
        document_type = "unknown"

    return {"document_type": document_type}


def detect_card_color(image_path):
    image = cv2.imread(str(Path(image_path)))
    if image is None:
        return "unknown"

    height, width = image.shape[:2]
    y1, y2 = int(height * 0.18), int(height * 0.82)
    x1, x2 = int(width * 0.12), int(width * 0.88)
    crop = image[y1:y2, x1:x2]

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape(-1, 3)
    colorful = pixels[(pixels[:, 1] > 25) & (pixels[:, 2] > 60)]
    if len(colorful) == 0:
        return "unknown"

    hue = float(np.median(colorful[:, 0]))
    if 15 <= hue <= 45:
        return "yellow_new"
    if 70 <= hue <= 120:
        return "blue_old"
    return "unknown"


def extract_plate(lines):
    for line in lines:
        uppercase_line = line.upper()
        for pattern in PLATE_PATTERNS:
            match = re.search(pattern, uppercase_line)
            if match:
                return match.group()
    return None


def extract_code_after_keywords(lines, keywords, min_length):
    for i, line in enumerate(lines):
        normalized_line = normalize_text(line)
        if not any(keyword in normalized_line for keyword in keywords):
            continue

        same_line_tokens = re.findall(r"[A-Z0-9]{%d,20}" % min_length, line.upper())
        same_line_tokens = [
            token for token in same_line_tokens
            if looks_like_vehicle_code(token, min_length)
        ]
        if same_line_tokens:
            return same_line_tokens[-1]

        for candidate_line in lines[i + 1:i + 4]:
            candidate = clean_code(candidate_line)
            if looks_like_vehicle_code(candidate, min_length):
                return candidate

    return None


def extract_engine(lines, card_type=None):
    return extract_code_after_keywords(lines, ENGINE_KEYWORDS, min_length=8)


def extract_frame(lines, card_type=None):
    return extract_code_after_keywords(lines, FRAME_KEYWORDS, min_length=5)


def extract_slash_date(text):
    match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    if match:
        return match.group(1)
    return None


def extract_textual_date(text):
    normalized = normalize_text(text)
    match = re.search(r"ngay\s*(\d{1,2})\s*thang\s*(\d{1,2})\s*nam\s*(\d{4})", normalized)
    if not match:
        match = re.search(r"(\d{1,2})\s*thang\s*(\d{1,2})\s*nam\s*(\d{4})", normalized)
    if not match:
        return None

    day, month, year = match.groups()
    return f"{int(day):02d}/{int(month):02d}/{year}"


def extract_date_from_window(lines, start_index):
    window = " ".join(lines[start_index:start_index + 3])
    return extract_slash_date(window) or extract_textual_date(window)


def extract_issue_date_for_new(lines):
    for i, line in enumerate(lines):
        normalized_line = normalize_text(line)
        if any(keyword in normalized_line for keyword in NEW_ISSUE_KEYWORDS):
            date_value = extract_date_from_window(lines, i)
            if date_value:
                return date_value
    return None


def extract_issue_date_for_old(lines):
    for i, line in enumerate(lines):
        normalized_line = normalize_text(line)
        if any(keyword in normalized_line for keyword in FIRST_REG_KEYWORDS):
            continue
        if any(keyword in normalized_line for keyword in OLD_ISSUE_EXCLUDE_KEYWORDS):
            continue

        date_value = extract_textual_date(" ".join(lines[i:i + 3]))
        if date_value:
            return date_value

    for i, line in enumerate(lines):
        normalized_line = normalize_text(line)
        if any(keyword in normalized_line for keyword in FIRST_REG_KEYWORDS + OLD_ISSUE_EXCLUDE_KEYWORDS):
            continue
        date_value = extract_slash_date(" ".join(lines[i:i + 3]))
        if date_value:
            return date_value

    return None


def extract_issue_date(lines, card_type=None):
    document_type = detect_document_type(lines)["document_type"]

    if document_type == "new":
        date_value = extract_issue_date_for_new(lines)
        if date_value:
            return date_value

    if document_type == "old":
        date_value = extract_issue_date_for_old(lines)
        if date_value:
            return date_value

    date_value = extract_issue_date_for_new(lines)
    if date_value:
        return date_value

    date_value = extract_issue_date_for_old(lines)
    if date_value:
        return date_value

    for line in lines:
        date_value = extract_slash_date(line)
        if date_value:
            return date_value

    return None
