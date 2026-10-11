"""Regras de decisão, sem dependência de OpenCV/YOLO (fáceis de testar)."""


def cobertura(caixa, roi):
    """Fração da área da vasilha (roi = x, y, w, h) coberta pela caixa do gato (x1, y1, x2, y2)."""
    gx1, gy1, gx2, gy2 = caixa
    rx, ry, rw, rh = roi
    if rw <= 0 or rh <= 0:
        return 0.0
    ix = max(0, min(gx2, rx + rw) - max(gx1, rx))
    iy = max(0, min(gy2, ry + rh) - max(gy1, ry))
    return (ix * iy) / (rw * rh)


class DetectorBebida:
    """Decide quando avisar: gato perto da vasilha por `segundos` seguidos, respeitando o `cooldown`.

    `tolerancia` evita zerar a contagem quando o YOLO perde o gato por um ou dois quadros.
    """

    def __init__(self, segundos=3, cooldown=120, tolerancia=1.0):
        self.segundos = segundos
        self.cooldown = cooldown
        self.tolerancia = tolerancia
        self.inicio = None
        self.visto_por_ultimo = None
        self.ultimo_aviso = None

    def atualizar(self, perto, agora):
        """Recebe se há gato na vasilha neste quadro; devolve True quando é hora de avisar."""
        if perto:
            if self.inicio is None:
                self.inicio = agora
            self.visto_por_ultimo = agora
        elif self.visto_por_ultimo is None or agora - self.visto_por_ultimo > self.tolerancia:
            self.inicio = None
            return False

        if self.inicio is None or agora - self.inicio < self.segundos:
            return False
        if self.ultimo_aviso is not None and agora - self.ultimo_aviso < self.cooldown:
            return False
        self.ultimo_aviso = agora
        return True
