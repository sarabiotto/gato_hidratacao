import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logica import DetectorBebida, cobertura

ROI = (100, 100, 50, 50)  # x, y, w, h


def test_cobertura_total():
    assert cobertura((0, 0, 300, 300), ROI) == 1.0


def test_cobertura_parcial():
    assert cobertura((125, 100, 200, 200), ROI) == 0.5


def test_cobertura_sem_contato():
    assert cobertura((0, 0, 50, 50), ROI) == 0.0


def test_cobertura_roi_vazio():
    assert cobertura((0, 0, 300, 300), (10, 10, 0, 0)) == 0.0


def test_avisa_depois_do_tempo_minimo():
    d = DetectorBebida(segundos=3, cooldown=120)
    assert not d.atualizar(True, 0)
    assert not d.atualizar(True, 2.9)
    assert d.atualizar(True, 3)


def test_passar_rapido_nao_avisa():
    d = DetectorBebida(segundos=3, cooldown=120, tolerancia=1)
    d.atualizar(True, 0)
    d.atualizar(True, 1)
    d.atualizar(False, 2.5)  # saiu há mais que a tolerância
    assert not d.atualizar(True, 3.5)


def test_tolera_falha_curta_de_deteccao():
    d = DetectorBebida(segundos=3, cooldown=120, tolerancia=1)
    d.atualizar(True, 0)
    d.atualizar(True, 1.5)
    d.atualizar(False, 2)  # YOLO perdeu o gato por um instante
    assert d.atualizar(True, 3)


def test_cooldown_entre_avisos():
    d = DetectorBebida(segundos=3, cooldown=120)
    d.atualizar(True, 0)
    assert d.atualizar(True, 3)
    assert not d.atualizar(True, 60)
    assert d.atualizar(True, 123)
