"""Fix the truncated title in cinematic-wedding-trailer-guide."""
import os
import json
from pathlib import Path

ROOT = Path(os.environ.get("WEDDINGAI_ROOT") or Path(__file__).resolve().parent.parent)
LANGS = ["en", "zh", "es", "fr", "de", "pt", "ja", "ru", "ar", "th"]

# EN key - exact value
EN_KEY = "blog.cinematic-wedding-trailer-guide.title_text.create_a_cinematic_wedding_trailer_what.89622728"
EN_NEW = "Create a Cinematic Wedding Trailer: What Videographers Won't Tell You"

# Check current EN
en = json.loads((ROOT / "i18n" / "en.json").read_text(encoding="utf-8"))
print(f"EN before: {en.get(EN_KEY)!r}")

# Update EN
en[EN_KEY] = EN_NEW
print(f"EN after:  {en[EN_KEY]!r}")
(ROOT / "i18n" / "en.json").write_text(
    json.dumps(en, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print("EN updated ✓")
