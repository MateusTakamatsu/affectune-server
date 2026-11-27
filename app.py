from pathlib import Path
import gradio as gr
from core.orquestrador import executar_pipeline
from database.database import (
    inicializar_banco,
    criar_usuario,
    autenticar_usuario,
    calcular_hash_audio,
    buscar_video_cache,
    salvar_video_cache,
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
FAVICON_PATH = BASE_DIR / "assets" / "feeling.png"
CACHE_VIDEOS_DIR = OUTPUT_DIR / "cache"
CACHE_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

inicializar_banco()


def fazer_login(username, senha):
    if not username or not senha:
        gr.Warning("Preencha usuário e senha.")
        return None, gr.update(visible=True), gr.update(visible=False), ""

    if autenticar_usuario(username, senha):
        user_limpo = username.strip().lower()
        return (
            user_limpo,
            gr.update(visible=False),  # Esconde tela de login
            gr.update(visible=True),   # Mostra o Affectune
            f"👤 Conectado como **{user_limpo}**",
        )

    gr.Warning("Usuário ou senha incorretos.")
    return None, gr.update(visible=True), gr.update(visible=False), ""


def registrar_usuario(novo_user, nova_senha, confirma_senha):
    if nova_senha != confirma_senha:
        gr.Warning("As senhas não coincidem.")
        return "", "", ""

    sucesso, mensagem = criar_usuario(novo_user, nova_senha)
    if sucesso:
        gr.Info(mensagem)
        return "", "", ""
    else:
        gr.Warning(mensagem)
        return novo_user, "", ""


def fazer_logout():
    return None, gr.update(visible=True), gr.update(visible=False), None, None


def processar_audio(caminho_audio, usuario_atual, progress=gr.Progress()):
    if not usuario_atual:
        raise gr.Error("Sessão expirada. Faça login novamente.")
    if not caminho_audio:
        gr.Warning("Envie um arquivo de áudio antes de gerar o vídeo.")
        return None

    try:
        progress(0.1, desc="Verificando assinatura do áudio...")
        audio_hash = calcular_hash_audio(caminho_audio)

        video_em_cache = buscar_video_cache(audio_hash)
        if video_em_cache:
            progress(1.0, desc="Vídeo recuperado do cache!")
            gr.Info("Áudio já processado anteriormente. Vídeo carregado instantaneamente!")
            return video_em_cache

        # Passando apenas pasta_saida, o orquestrador usa o nome original do áudio
        progress(0.25, desc="Extraindo métricas e selecionando cenas...")
        caminho_video = executar_pipeline(
            caminho_mp3=caminho_audio,
            pasta_saida=OUTPUT_DIR,
        )

        # Grava no SQLite: audio_hash -> "output/Nome da Musica.mp4"
        salvar_video_cache(audio_hash, caminho_video)
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

css_enxuto = (BASE_DIR / "style" / "styles.css").read_text(encoding="utf-8")

blocks_kwargs = {"title": "Affectune"}
launch_kwargs = {
    "allowed_paths": [str(OUTPUT_DIR)],
    "favicon_path": str(FAVICON_PATH),
}

if "theme" in gr.Blocks.__init__.__code__.co_varnames:
    blocks_kwargs.update({"theme": tema, "css": css_enxuto})
else:
    launch_kwargs.update({"theme": tema, "css": css_enxuto})


with gr.Blocks(**blocks_kwargs) as app:
    usuario_logado = gr.State(None)

    gr.Markdown(
        """
        # ☀️❄️ Affectune 🔥🌊
        Envie sua música para visualizar um vídeo que captura o sentimento contido nela.
        """,
        elem_classes=["hero-header"],
    )

    # --- TELA 1: LOGIN E CADASTRO ---
    with gr.Column(visible=True) as tela_auth:
        with gr.Row():
            gr.Column(scale=1)  # Espaçador esquerdo para centralizar
            with gr.Column(scale=2, min_width=320, variant="panel"):
                with gr.Tabs():
                    with gr.Tab("🔑 Entrar"):
                        login_user = gr.Textbox(label="Usuário", placeholder="seu_usuario")
                        login_pass = gr.Textbox(label="Senha", type="password", placeholder="••••••••")
                        btn_login = gr.Button("Entrar", variant="primary", size="lg")

                    with gr.Tab("✨ Criar conta"):
                        reg_user = gr.Textbox(label="Novo usuário", placeholder="escolha_um_usuario")
                        reg_pass = gr.Textbox(label="Senha", type="password", placeholder="mínimo 4 caracteres")
                        reg_conf = gr.Textbox(label="Confirmar senha", type="password", placeholder="repita a senha")
                        btn_registrar = gr.Button("Cadastrar", variant="primary", size="lg")
            gr.Column(scale=1)  # Espaçador direito

    # --- TELA 2: APLICAÇÃO PRINCIPAL ---
    with gr.Column(visible=False) as tela_app:
        with gr.Row():
            lbl_usuario = gr.Markdown("")
            btn_logout = gr.Button("Sair", size="sm", scale=0)

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

    # Eventos de Autenticação
    btn_login.click(
        fn=fazer_login,
        inputs=[login_user, login_pass],
        outputs=[usuario_logado, tela_auth, tela_app, lbl_usuario],
    )
    btn_registrar.click(
        fn=registrar_usuario,
        inputs=[reg_user, reg_pass, reg_conf],
        outputs=[reg_user, reg_pass, reg_conf],
    )
    btn_logout.click(
        fn=fazer_logout,
        outputs=[usuario_logado, tela_auth, tela_app, audio_input, video_output],
    )

    # Evento Principal
    btn_enviar.click(
        fn=processar_audio,
        inputs=[audio_input, usuario_logado],
        outputs=video_output,
    )

if __name__ == "__main__":
    app.launch(**launch_kwargs)