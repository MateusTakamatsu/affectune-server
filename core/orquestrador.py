import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path mesmo rodando `python core/orquestrador.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.extrair_metricas import extrair_metricas_audio
from core.calcular_valencia_ativacao import calcular_valencia_ativacao
from core.selecionar_imagens import selecionar_imagens
from core.gerar_video import gerar_video_leve

DEFAULT_OASIS_CSV = ROOT_DIR / "oasis" / "OASIS.csv"
DEFAULT_OASIS_IMAGES = ROOT_DIR / "oasis" / "images"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output"


def executar_pipeline(
    caminho_mp3: str | Path,
    caminho_oasis_csv: str | Path = DEFAULT_OASIS_CSV,
    pasta_imagens: str | Path = DEFAULT_OASIS_IMAGES,
    pasta_saida: str | Path = DEFAULT_OUTPUT_DIR,
    caminho_saida_video: str | Path | None = None,
    raio_afastamento: float = 0.15,
    min_duracao_seg: int = 3,
) -> str:
    caminho_mp3 = Path(caminho_mp3)
    if not caminho_mp3.exists():
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {caminho_mp3}")

    nome_musica = caminho_mp3.stem
    if caminho_saida_video is None:
        caminho_saida_video = Path(pasta_saida) / f"{nome_musica}.mp4"

    print(f"[1/4] Extraindo métricas de áudio: {nome_musica}...")
    df_features = extrair_metricas_audio(caminho_mp3)

    print("[2/4] Calculando Valência e Ativação...")
    df_emocao = calcular_valencia_ativacao(df_features, exibir_grafico=False)

    print("[3/4] Selecionando imagens compatíveis...")
    df_guia = selecionar_imagens(
        df_emocao,
        caminho_oasis_csv=caminho_oasis_csv,
        raio_afastamento=raio_afastamento,
        min_duracao_seg=min_duracao_seg,
    )
    print(f"      -> {len(df_guia)} blocos de imagem definidos.")

    print("[4/4] Renderizando vídeo final...")
    video_gerado = gerar_video_leve(
        df_guia=df_guia,
        caminho_mp3=caminho_mp3,
        pasta_imagens=pasta_imagens,
        caminho_saida_video=caminho_saida_video,
    )

    print(f"Concluído! Vídeo salvo em: {video_gerado}")
    return video_gerado


if __name__ == "__main__":
    audio_teste = ROOT_DIR / "audios" / "quarters" / "Killing In the Name.mp3"
    executar_pipeline(audio_teste)