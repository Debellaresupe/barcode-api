from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from PIL import Image
from urllib.parse import unquote
import io
import os
import re
import subprocess
import tempfile

app = FastAPI(title="Barcode API")

GS = "\x1d"
MAX_DATA_LEN = 4096


@app.get("/health")
def health():
    return {"ok": True}


def resize_png(png_bytes: bytes, w: int, h: int) -> bytes:
    with Image.open(io.BytesIO(png_bytes)) as img:
        img = img.resize((w, h), Image.Resampling.NEAREST)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()


def make_png(
    zint_type: str,
    data: str,
    extra_args: list[str] | None = None,
) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        output_path = os.path.join(td, "barcode.png")

        cmd = ["zint", "-b", zint_type]

        if extra_args:
            cmd.extend(extra_args)

        cmd.extend(["-d", data, "-o", output_path])

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if proc.returncode != 0:
            raise HTTPException(
                status_code=422,
                detail=(proc.stderr or proc.stdout or "zint failed").strip(),
            )

        with open(output_path, "rb") as f:
            return f.read()


def decode_input(raw: str) -> str:
    decoded = unquote(raw)

    return (
        decoded
        .replace("\\u001D", GS)
        .replace("\\u001d", GS)
        .replace("\\x1D", GS)
        .replace("\\x1d", GS)
        .replace("%1D", GS)
        .replace("%1d", GS)
        .replace("<GS>", GS)
    )


def normalize_mark(raw: str) -> str:
    raw = decode_input(raw)

    # TEC-IT-like FNC1 prefix, e.g. \F010460...
    if raw.startswith("\\F"):
        raw = raw[2:]

    if not raw.startswith("01") or len(raw) < 16:
        raise HTTPException(400, "GS1 mark must start with 01 + GTIN14")

    gtin = raw[2:16]
    rest = raw[16:]

    if not gtin.isdigit():
        raise HTTPException(400, "GTIN after AI 01 must be 14 digits")

    if not rest.startswith("21"):
        raise HTTPException(400, "Expected AI 21 after GTIN")

    rest = rest[2:]
    parts = rest.split(GS)

    if len(parts) < 2:
        raise HTTPException(400, "Expected GS separator after AI 21 serial")

    serial = parts[0]

    if not serial:
        raise HTTPException(400, "AI 21 serial is empty")

    result = f"[01]{gtin}[21]{serial}"

    supported_ais = ("240", "91", "92", "93")

    for part in parts[1:]:
        if not part:
            continue

        matched_ai = None

        for ai in supported_ais:
            if part.startswith(ai):
                matched_ai = ai
                value = part[len(ai):]
                break

        if matched_ai is None:
            raise HTTPException(400, f"Unsupported AI after GS: {part[:4]}")

        if not value:
            raise HTTPException(400, f"AI {matched_ai} value is empty")

        result += f"[{matched_ai}]{value}"

    return result


@app.get("/barcode.png")
def barcode_png(
    type: str = Query(..., description="ean13, ean8, qr, gs1-dm"),
    data: str = Query(..., description="Barcode data"),
    w: int = Query(150, ge=50, le=1000),
    h: int = Query(150, ge=50, le=1000),
):
    barcode_type = type.lower()

    if not data:
        raise HTTPException(400, "data is required")

    if len(data) > MAX_DATA_LEN:
        raise HTTPException(400, "data is too long")

    if barcode_type == "ean13":
        if not re.fullmatch(r"\d{13}", data):
            raise HTTPException(400, "EAN-13 must be exactly 13 digits")

        png = make_png("EANX", data)

    elif barcode_type == "ean8":
        if not re.fullmatch(r"\d{8}", data):
            raise HTTPException(400, "EAN-8 must be exactly 8 digits")

        png = make_png("6", data)

    elif barcode_type == "qr":
        png = make_png(
            "QRCODE",
            data,
            extra_args=[
                "--scale=8",
                "--border=4",
                "--notext",
            ],
        )

    elif barcode_type in ("gs1-dm", "datamatrix-gs1"):
        zint_data = normalize_mark(data)

        png = make_png(
            "DATAMATRIX",
            zint_data,
            extra_args=[
                "--gs1",
                "--gssep",
                "--square",
                "--notext",
                "--scale=8",
                "--border=10",
            ],
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported type. Use: ean13, ean8, qr, gs1-dm",
        )

    png = resize_png(png, w, h)

    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public,max-age=86400"},
    )