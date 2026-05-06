"""Reset the demo service back to the intentional buggy state."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "app" / "web_service.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "return 0.0 if request.count == 0 else request.total / request.count",
    "return request.total / request.count",
)
path.write_text(text, encoding="utf-8")
print("Reset demo bug in app/web_service.py")
