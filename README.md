# gato_hidratacao

Avisa no Telegram, com foto, quando um dos gatos fica na vasilha de água.
Usa a câmera IP (RTSP) e o YOLOv8 para detectar gatos.

## Como decide que está bebendo

Você marca um retângulo em volta da vasilha. Se um gato cobre pelo menos
`COBERTURA_MIN` dessa área por `SEGUNDOS_BEBENDO` segundos seguidos, o script
manda a foto. Depois de um aviso, espera `COOLDOWN` segundos antes de avisar de
novo, para não chegar uma foto por segundo da mesma bebida.

## Preparar o Telegram (uma vez só)

1. No Telegram, fale com @BotFather, envie `/newbot` e siga os passos. Ele te dá um TOKEN.
2. Mande qualquer mensagem para o seu bot novo.
3. Abra `https://api.telegram.org/botSEU_TOKEN/getUpdates` no navegador e procure
   o número em `"chat":{"id":...}`. Esse é o CHAT_ID.

## Instalar e rodar

```bash
pip install -r requirements.txt
cp .env.example .env      # preencha câmera, token e chat id
python gato_agua.py --marcar
```

Na primeira vez, desenhe o retângulo em volta da vasilha **e um pouco do espaço
acima dela**, onde fica a cabeça do gato quando ele bebe, e aperte ENTER. A
marcação fica salva em `roi.json`; nas próximas vezes basta `python gato_agua.py`.
Use `--marcar` de novo se mudar a câmera ou a vasilha de lugar, e `--sem-janela`
para rodar sem mostrar o vídeo (num Raspberry Pi, por exemplo; nesse caso faça a
marcação antes num computador com tela e copie o `roi.json`).

## Ajustes nos primeiros dias

| Problema | O que mudar no `.env` |
|---|---|
| Avisa quando o gato só passa perto | aumentar `SEGUNDOS_BEBENDO` ou `COBERTURA_MIN` |
| Não avisa quando ele bebe | diminuir `SEGUNDOS_BEBENDO` ou `COBERTURA_MIN` |
| Não reconhece o gato (principalmente à noite) | diminuir `CONFIANCA` (ex.: 0.35) |

Limites desta versão:

- Ela sabe que *um* gato está na vasilha, não qual deles.
- Um gato sentado ao lado da vasilha pode gerar aviso falso. Se acontecer com
  frequência, o próximo passo é exigir que a cabeça esteja abaixada sobre a vasilha.
- À noite a câmera muda para infravermelho (preto e branco). O YOLO costuma
  continuar detectando, mas com menos confiança.

## Testes

```bash
pip install pytest
python -m pytest
```
