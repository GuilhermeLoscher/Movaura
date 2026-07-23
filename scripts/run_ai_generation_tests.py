from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage

from core.ai_generation.models import GenerationError
from core.ai_generation.prompting import enhance_prompt
from core.ai_generation.providers import MockImageGenerationProvider
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage
from core.ai_generation.models import GenerationRequest


def make_request(simulate_error: str = "", quantity: int = 2) -> GenerationRequest:
    prompt = "cidade futurista com neon azul e area limpa para icones"
    return GenerationRequest(
        prompt=prompt,
        enhanced_prompt=enhance_prompt(prompt, "cinematic"),
        negative_prompt="texto, marca d'agua",
        style_id="cinematic",
        style_name="Cinematico",
        resolution=(640, 360),
        quantity=quantity,
        quality="fast",
        seed=1234,
        simulate_error=simulate_error,
    )


def main() -> int:
    app = QApplication.instance() or QApplication([])
    temp = Path(tempfile.mkdtemp(prefix="movaura-ai-test-"))
    try:
        provider = MockImageGenerationProvider()
        storage = GenerationStorage(temp / "storage")
        history = GenerationHistoryStore(temp / "history.json")
        request = make_request()
        progress_events: list[tuple[int, str]] = []
        result = provider.generate(
            request,
            storage.job_dir(),
            lambda value, message: progress_events.append((value, message)),
            lambda: False,
        )
        final_result = storage.post_process(result)
        assert len(final_result.images) == 2, "mock provider should return two images"
        assert progress_events, "progress events were not emitted"
        for image in final_result.images:
            loaded = QImage(str(image.path))
            assert not loaded.isNull(), f"invalid image: {image.path}"
            assert loaded.width() == 640 and loaded.height() == 360, "post-process resolution mismatch"
        history.add_result(final_result)
        assert len(history.items()) == 1, "history was not persisted"

        try:
            provider.generate(make_request("rate_limit", 1), storage.job_dir(), lambda *_: None, lambda: False)
        except GenerationError as exc:
            assert exc.code.value == "rate_limit", "wrong simulated error code"
        else:
            raise AssertionError("simulated provider error did not fail")

        try:
            provider.generate(make_request("", 1), storage.job_dir(), lambda *_: None, lambda: True)
        except GenerationError as exc:
            assert exc.code.value == "cancelled", "cancel did not produce cancelled code"
        else:
            raise AssertionError("cancelled generation did not fail")

        print("ai_generation_tests=ok")
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
