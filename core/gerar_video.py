import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import pandas as pd


def _obter_executavel_ffmpeg() -> str:
    ffmpeg_sistema = shutil.which("ffmpeg")
    if ffmpeg_sistema:
        return ffmpeg_sistema
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError(
            "FFmpeg não encontrado. Instale no sistema (sudo apt install ffmpeg) "
            "ou no venv (pip install imageio-ffmpeg)."
        )


def _indexar_imagens(pasta_imagens: Path) -> dict[str, Path]:
    if not pasta_imagens.exists():
        raise FileNotFoundError(f"Pasta de imagens não encontrada: {pasta_imagens}")

    extensoes_validas = {".jpg", ".jpeg", ".png", ".webp"}
    indice = {}
    for arquivo in pasta_imagens.iterdir():
        if arquivo.is_file() and arquivo.suffix.lower() in extensoes_validas:
            indice[arquivo.stem.lower()] = arquivo.resolve()
    return indice


def _resolver_caminho_imagem(indice: dict[str, Path], img_id: str, theme: str) -> Path:
    for candidato in (str(theme).strip().lower(), str(img_id).strip().lower()):
        if candidato in indice:
            return indice[candidato]

    raise FileNotFoundError(
        f"Imagem não encontrada para theme='{theme}' ou id='{img_id}'."
    )


def gerar_video_leve(
    df_guia: pd.DataFrame,
    caminho_mp3: str | Path,
    pasta_imagens: str | Path,
    caminho_saida_video: str | Path,
    resolucao: tuple[int, int] = (1280, 720),
    fps: int = 2,
) -> str:
    ffmpeg_exe = _obter_executavel_ffmpeg()
    pasta_imagens = Path(pasta_imagens)
    caminho_saida_video = Path(caminho_saida_video).resolve()
    caminho_saida_video.parent.mkdir(parents=True, exist_ok=True)

    indice_imagens = _indexar_imagens(pasta_imagens)
    largura, altura = resolucao

    linhas_concat = []
    ultimo_caminho = None

    for _, row in df_guia.iterrows():
        caminho_img = _resolver_caminho_imagem(
            indice_imagens, row["img_id"], row["theme"]
        )
        caminho_escapado = str(caminho_img).replace("'", "'\\''")
        duracao = float(row["duracao_seg"])

        linhas_concat.append(f"file '{caminho_escapado}'")
        linhas_concat.append(f"duration {duracao}")
        ultimo_caminho = caminho_escapado

    # Exigência do FFmpeg concat: repetir a última imagem para preservar sua duração
    if ultimo_caminho:
        linhas_concat.append(f"file '{ultimo_caminho}'")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write("\n".join(linhas_concat))
        caminho_lista_tmp = tmp.name

    try:
        filtro_video = (
            f"scale={largura}:{altura}:force_original_aspect_ratio=decrease,"
            f"pad={largura}:{altura}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,format=yuv420p"
        )

        comando = [
            ffmpeg_exe,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", caminho_lista_tmp,
            "-i", str(Path(caminho_mp3).resolve()),
            "-vf", filtro_video,
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(caminho_saida_video),
        ]

        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        erro_ffmpeg = e.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"Erro ao renderizar vídeo no FFmpeg:\n{erro_ffmpeg}")
    finally:
        if os.path.exists(caminho_lista_tmp):
            os.remove(caminho_lista_tmp)

    return str(caminho_saida_video)