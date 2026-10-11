"""Avisa no Telegram quando um gato fica na vasilha de água.

Uso:
    python gato_agua.py              # usa a vasilha marcada antes (roi.json)
    python gato_agua.py --marcar     # marca (ou remarca) a vasilha
    python gato_agua.py --sem-janela # roda sem mostrar vídeo (ex.: Raspberry Pi)

Configuração no arquivo .env (veja .env.example).
"""
import argparse
import json
import os
import threading
import time

import cv2
import requests
from ultralytics import YOLO

from logica import DetectorBebida, cobertura

ARQUIVO_ROI = "roi.json"
CLASSE_GATO = 15  # "cat" no COCO


def carregar_env(caminho=".env"):
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


class Leitor:
    """Lê sempre o quadro mais recente (evita atraso do RTSP) e reconecta se a câmera cair."""

    def __init__(self, fonte):
        self.fonte = fonte
        self.frame = None
        self.lock = threading.Lock()
        threading.Thread(target=self._ler, daemon=True).start()

    def _ler(self):
        cap = cv2.VideoCapture(self.fonte)
        falhas = 0
        while True:
            ok, f = cap.read()
            if ok:
                falhas = 0
                with self.lock:
                    self.frame = f
                continue
            falhas += 1
            time.sleep(0.5)
            if falhas >= 10:
                print("Câmera sem imagem, reconectando...")
                cap.release()
                time.sleep(2)
                cap = cv2.VideoCapture(self.fonte)
                falhas = 0

    def ler(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()


def enviar_telegram(token, chat_id, imagem, legenda):
    _, buf = cv2.imencode(".jpg", imagem)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": legenda},
            files={"photo": ("gato.jpg", buf.tobytes(), "image/jpeg")},
            timeout=20,
        )
        if not r.ok:
            print(f"Telegram recusou o envio: {r.status_code} {r.text}")
    except requests.RequestException as e:
        print(f"Falha ao enviar para o Telegram: {e}")


def obter_roi(frame, remarcar):
    if not remarcar and os.path.exists(ARQUIVO_ROI):
        with open(ARQUIVO_ROI) as f:
            return tuple(json.load(f))
    roi = cv2.selectROI("Marque a vasilha e aperte ENTER", frame)
    cv2.destroyAllWindows()
    if roi[2] == 0 or roi[3] == 0:
        raise SystemExit("Nenhuma área marcada.")
    with open(ARQUIVO_ROI, "w") as f:
        json.dump([int(v) for v in roi], f)
    return tuple(int(v) for v in roi)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--marcar", action="store_true", help="marcar a vasilha de novo")
    p.add_argument("--sem-janela", action="store_true", help="não mostrar o vídeo")
    args = p.parse_args()

    carregar_env()
    fonte = os.environ.get("CAMERA_URL")
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not fonte or not token or not chat_id:
        raise SystemExit("Defina CAMERA_URL, TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no arquivo .env")

    cobertura_min = float(os.environ.get("COBERTURA_MIN", 0.15))
    confianca = float(os.environ.get("CONFIANCA", 0.5))
    detector = DetectorBebida(
        segundos=float(os.environ.get("SEGUNDOS_BEBENDO", 3)),
        cooldown=float(os.environ.get("COOLDOWN", 120)),
    )

    modelo = YOLO("yolov8n.pt")
    leitor = Leitor(fonte)
    print("Conectando na câmera...")
    while (frame := leitor.ler()) is None:
        time.sleep(0.2)

    roi = obter_roi(frame, args.marcar)
    rx, ry, rw, rh = roi
    print(f"Vasilha em {roi}. Vigiando (aperte q na janela para sair).")

    while True:
        frame = leitor.ler()
        res = modelo(frame, classes=[CLASSE_GATO], conf=confianca, verbose=False)[0]

        perto = False
        for c in res.boxes.xyxy.cpu().numpy().astype(int):
            cv2.rectangle(frame, (c[0], c[1]), (c[2], c[3]), (0, 255, 0), 2)
            if cobertura(c, roi) > cobertura_min:
                perto = True
        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)

        if detector.atualizar(perto, time.time()):
            hora = time.strftime("%H:%M")
            print(f"{hora} gato na vasilha, enviando foto")
            threading.Thread(
                target=enviar_telegram,
                args=(token, chat_id, frame.copy(), f"Um gato está bebendo água ({hora})"),
                daemon=True,
            ).start()

        if not args.sem_janela:
            cv2.imshow("Vasilha", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break


if __name__ == "__main__":
    main()
