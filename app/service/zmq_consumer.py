#!/usr/bin/env python3
"""
Cliente ZMQ PULL para testar o publisher do Vision Service.

Recebe frames anotados + metadados e abre uma janela OpenCV em tempo real.
Pressione 'q' para encerrar.

Uso:
    python zmq_consumer.py [endpoint]

    endpoint (padrão): tcp://localhost:5555
"""
import sys
import json

import cv2
import numpy as np
import zmq


def main() -> None:
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "tcp://localhost:5555"

    ctx = zmq.Context()
    sock = ctx.socket(zmq.PULL)
    sock.setsockopt(zmq.RCVTIMEO, 2000)  # 2s timeout para não travar no exit
    sock.connect(endpoint)
    print(f"Conectado em {endpoint} — aguardando frames… (pressione 'q' para sair)")

    while True:
        try:
            parts = sock.recv_multipart()
        except zmq.Again:
            # Timeout — verifica se janela ainda está aberta
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        if len(parts) != 2:
            print(f"[AVISO] Mensagem com {len(parts)} partes — esperado 2, ignorando.")
            continue

        # Decodifica frame JPEG
        frame_bytes, meta_bytes = parts
        buf = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if frame is None:
            print("[AVISO] Falha ao decodificar JPEG")
            continue

        # Decodifica metadados JSON
        try:
            meta = json.loads(meta_bytes.decode("utf-8"))
        except Exception as exc:
            print(f"[AVISO] Falha ao decodificar JSON: {exc}")
            meta = {}

        # Exibe informações no terminal
        frame_id = meta.get("frame_id", "?")
        fps = meta.get("fps_measured", 0.0)
        persons = meta.get("person_count", 0)
        ts = meta.get("timestamp_iso", "")
        inf_err = meta.get("inference_error", False)
        status = "ERRO" if inf_err else "ok"
        print(
            f"frame={frame_id:>6}  fps={fps:>5.1f}  pessoas={persons}  "
            f"inferência={status}  ts={ts}",
            end="\r",
        )

        cv2.imshow("Vision Service — Consumer (q para sair)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    print("\nEncerrando consumer.")
    sock.close()
    ctx.term()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
