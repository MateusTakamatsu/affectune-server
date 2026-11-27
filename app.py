from pathlib import Path
import gradio as gr
from core.orquestrador import executar_pipeline

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
FAVICON_PATH = BASE_DIR / "assets" / "feeling.png"


def processar_audio(caminho_audio, progress=gr.Progress()):
    if not caminho_audio:
        gr.Warning("Envie um arquivo de áudio antes de gerar o vídeo.")
        return None

    try:
        progress(0.2, desc="Extraindo métricas e selecionando cenas...")
        caminho_video = executar_pipeline(
            caminho_mp3=caminho_audio,
            pasta_saida=OUTPUT_DIR,
        )
        progress(1.0, desc="Concluído!")
        return caminho_video
    except Exception as e:
        raise gr.Error(f"Não foi possível processar o áudio: {e}")


# Tema nativo personalizado
tema = gr.themes.Soft(
    primary_hue="rose",
    secondary_hue="purple",
    neutral_hue="slate",
    radius_size="xxl",
    font=gr.themes.GoogleFont("Plus Jakarta Sans"),
).set(
    body_background_fill="linear-gradient(135deg, #FFF8F3 0%, #FFF0F3 48%, #F3E8FF 100%)",
    panel_background_fill="rgba(255, 255, 255, 0.92)",
    panel_border_color="#F3E8FF",
    panel_border_width="1.5px",
    block_background_fill="#FFFFFF",
    block_border_color="#FFE4E6",
    block_radius="20px",
    block_shadow="0 14px 32px -12px rgba(147, 51, 234, 0.14)",
    button_primary_background_fill="linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #A855F7 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg, #F43F5E 0%, #FB923C 50%, #9333EA 100%)",
    button_primary_text_color="#FFFFFF",
    button_primary_border_color="transparent",
    button_large_radius="999px",
)

css_enxuto = (BASE_DIR / "styles.css").read_text(encoding="utf-8")

blocks_kwargs = {"title": "Affectune"}
launch_kwargs = {
    "auth": ("admin", "1234"),
    "auth_message": "Olá! Faça login com seu usuário e senha para acessar o Affectune.",
    "allowed_paths": [str(OUTPUT_DIR)],
    "favicon_path": str(FAVICON_PATH),
}

if "theme" in gr.Blocks.__init__.__code__.co_varnames:
    blocks_kwargs.update({"theme": tema, "css": css_enxuto})
else:
    launch_kwargs.update({"theme": tema, "css": css_enxuto})


with gr.Blocks(**blocks_kwargs) as app:
    gr.Markdown(
        """
        # ☀️❄️ Affectune 🔥🌊
        Envie sua música para visualizar um vídeo que captura o sentimento contido nela.
        """,
        elem_classes=["hero-header"],
    )

    # min_width = 300 para as colunas ficarem lado a lado
    with gr.Row(equal_height=True):
        with gr.Column(scale=1, min_width=300, variant="panel"):
            gr.Markdown(
                """
                ### 🎵 1. Sua música
                Arraste um arquivo de áudio com a sua música.
                """
            )
            audio_input = gr.Audio(
                sources=["upload"],
                type="filepath",
                label="Arquivo de música",
            )
            btn_enviar = gr.Button(
                "✨ Gerar vídeo",
                variant="primary",
                size="lg",
            )

        with gr.Column(scale=1, min_width=300, variant="panel"):
            gr.Markdown(
                """
                ### 🎬 2. Seu vídeo
                Assim que ficar pronto, assista ou baixe o resultado abaixo.
                """
            )
            video_output = gr.Video(
                label="Vídeo sincronizado",
            )

    btn_enviar.click(
        fn=processar_audio,
        inputs=audio_input,
        outputs=video_output,
    )

if __name__ == "__main__":
    app.launch(**launch_kwargs)