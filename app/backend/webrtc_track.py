import asyncio
import io
import logging
from typing import Optional

import av
import numpy as np
from PIL import Image
from aiortc import VideoStreamTrack

logger = logging.getLogger(__name__)

# Fallback preto em yuv420p (sem usar cv2 nem codec av)
_H, _W = 480, 640
_BLACK_YUV = np.zeros((_H * 3 // 2, _W), dtype=np.uint8)
_BLACK_YUV[_H:] = 128  # planos U e V neutros

_decode_ok_count = 0
_decode_fail_count = 0


def _jpeg_to_yuv420(jpeg_bytes: bytes) -> Optional[np.ndarray]:
    """Decodifica JPEG via Pillow (libjpeg puro, sem libav) e converte para yuv420p."""
    global _decode_ok_count, _decode_fail_count
    try:
        img = Image.open(io.BytesIO(jpeg_bytes))
        rgb = np.array(img.convert("RGB"), dtype=np.uint8)

        # rgb24 → yuv420p via swscale do av (não usa libavdevice nem libavcodec)
        frame = av.VideoFrame.from_ndarray(rgb, format="rgb24")
        yuv_frame = frame.reformat(format="yuv420p")
        result = yuv_frame.to_ndarray(format="yuv420p")

        _decode_ok_count += 1
        if _decode_ok_count == 1:
            logger.info(
                "Primeiro frame decodificado com sucesso: shape=%s min=%d max=%d",
                result.shape, int(result.min()), int(result.max()),
            )
        elif _decode_ok_count % 300 == 0:
            logger.info("Frames decodificados: %d ok / %d falhas", _decode_ok_count, _decode_fail_count)
        return result

    except Exception as exc:
        _decode_fail_count += 1
        if _decode_fail_count <= 3 or _decode_fail_count % 100 == 0:
            logger.warning("Decode falhou (%d): %s", _decode_fail_count, exc)
        return None


class QueuedVideoTrack(VideoStreamTrack):
    """VideoStreamTrack que serve frames JPEG de uma asyncio.Queue."""

    def __init__(self, frame_queue: asyncio.Queue) -> None:
        super().__init__()
        self._queue = frame_queue
        self._last_yuv: Optional[np.ndarray] = None

    async def recv(self) -> av.VideoFrame:
        pts, time_base = await self.next_timestamp()

        try:
            jpeg_bytes = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            decoded = _jpeg_to_yuv420(jpeg_bytes)
            if decoded is not None:
                self._last_yuv = decoded
        except asyncio.TimeoutError:
            pass

        yuv = self._last_yuv if self._last_yuv is not None else _BLACK_YUV
        frame = av.VideoFrame.from_ndarray(yuv, format="yuv420p")
        frame.pts = pts
        frame.time_base = time_base
        return frame
