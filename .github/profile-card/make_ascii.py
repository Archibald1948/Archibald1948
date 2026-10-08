"""avatar.jpg를 반블록 문자(▀▄█) 아트로 변환해 ascii_art.json에 저장한다.

아바타가 바뀔 때만 로컬에서 한 번 실행한다. (Pillow 필요: pip install pillow)
한 글자 칸이 위·아래 두 픽셀을 표현하므로 행 수는 픽셀 높이의 절반이 된다.
가장자리와 이어진 흰 배경은 투명 처리해 카드 배경과 자연스럽게 섞이게 한다.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SRC = HERE / "avatar.jpg"
OUT = HERE / "ascii_art.json"

COLS = 56  # 가로 픽셀(= 글자) 수
COLORS = 20  # 팔레트 색 수 (적을수록 SVG가 가볍지만 노란 </> 같은 작은 포인트 색이 사라진다)
BG_THRESHOLD = 236  # 이 값 이상인 밝은 픽셀을 배경 후보로 본다
CROP_PAD = 0.04


def transparent_mask(img: Image.Image) -> Image.Image:
    """가장자리에서 flood fill로 닿는 밝은 배경 영역을 0, 나머지를 255로 표시한 마스크."""
    gray = img.convert("L").point(lambda v: 255 if v >= BG_THRESHOLD else 0)
    w, h = gray.size
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if gray.getpixel((x, y)) == 255:
            ImageDraw.floodfill(gray, (x, y), 128)
    return gray.point(lambda v: 0 if v == 128 else 255)


def main() -> None:
    img = Image.open(SRC).convert("RGB")
    mask = transparent_mask(img)

    # 배경을 제외한 영역 기준으로 정사각형에 가깝게 잘라낸다.
    left, top, right, bottom = mask.getbbox()
    pad = int(max(right - left, bottom - top) * CROP_PAD)
    box = (max(left - pad, 0), max(top - pad, 0), min(right + pad, img.width), min(bottom + pad, img.height))
    img, mask = img.crop(box), mask.crop(box)

    rows_px = round(COLS * img.height / img.width / 2) * 2
    img = img.resize((COLS, rows_px), Image.LANCZOS)
    mask = mask.resize((COLS, rows_px), Image.LANCZOS)
    img = img.quantize(colors=COLORS, method=Image.MEDIANCUT).convert("RGB")

    pixels: list[list[str | None]] = []
    for y in range(rows_px):
        row = []
        for x in range(COLS):
            if mask.getpixel((x, y)) < 128:
                row.append(None)
            else:
                r, g, b = img.getpixel((x, y))
                row.append(f"#{r:02x}{g:02x}{b:02x}")
        pixels.append(row)

    OUT.write_text(json.dumps({"cols": COLS, "rows": rows_px // 2, "pixels": pixels}) + "\n")
    print(f"saved {OUT.name}: {COLS}x{rows_px // 2} cells")


if __name__ == "__main__":
    main()
