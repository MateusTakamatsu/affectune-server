import hashlib
import hmac
import secrets
import shutil
import sqlite3
import subprocess
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "affectune.db"


def inicializar_banco() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS videos_cache (
                audio_hash TEXT PRIMARY KEY,
                caminho_video TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# --- AUTENTICAÇÃO ---

def _gerar_hash_senha(senha: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return dk.hex()


def criar_usuario(username: str, senha: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if len(username) < 3:
        return False, "O nome de usuário deve ter pelo menos 3 caracteres."
    if len(senha) < 4:
        return False, "A senha deve ter pelo menos 4 caracteres."

    salt = secrets.token_hex(16)
    senha_hash = _gerar_hash_senha(senha, salt)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO usuarios (username, senha_hash, salt) VALUES (?, ?, ?)",
                (username, senha_hash, salt),
            )
        return True, "Conta criada com sucesso! Já pode fazer login."
    except sqlite3.IntegrityError:
        return False, "Esse nome de usuário já existe."


def autenticar_usuario(username: str, senha: str) -> bool:
    username = username.strip().lower()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT senha_hash, salt FROM usuarios WHERE username = ?",
            (username,),
        ).fetchone()

    if not row:
        return False

    senha_hash_salva, salt = row
    senha_hash_tentativa = _gerar_hash_senha(senha, salt)
    return hmac.compare_digest(senha_hash_salva, senha_hash_tentativa)


# --- CACHE DE ÁUDIO / VÍDEO ---

def _obter_ffmpeg() -> str:
    ffmpeg_sistema = shutil.which("ffmpeg")
    if ffmpeg_sistema:
        return ffmpeg_sistema
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def calcular_hash_audio(caminho_audio: str | Path) -> str:
    """
    Decodifica apenas o fluxo de áudio para PCM bruto (ignorando nome, capa e tags ID3)
    e retorna o SHA-256 do conteúdo sonoro.
    """
    ffmpeg_exe = _obter_ffmpeg()
    sha256 = hashlib.sha256()

    comando = [
        ffmpeg_exe,
        "-v", "error",
        "-i", str(caminho_audio),
        "-map", "0:a:0",  # Apenas o primeiro stream de áudio (ignora capas/imagens)
        "-vn",
        "-f", "s16le",    # PCM 16-bit sem cabeçalho ou metadados
        "-ac", "1",
        "-ar", "22050",
        "-",
    ]

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert processo.stdout is not None
    while chunk := processo.stdout.read(65536):
        sha256.update(chunk)

    _, stderr = processo.communicate()
    if processo.returncode != 0:
        raise RuntimeError(f"Falha ao ler fluxo de áudio: {stderr.decode('utf-8', errors='ignore')}")

    return sha256.hexdigest()


def buscar_video_cache(audio_hash: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT caminho_video FROM videos_cache WHERE audio_hash = ?",
            (audio_hash,),
        ).fetchone()

    if not row:
        return None

    caminho_video = row[0]
    if Path(caminho_video).is_file():
        return caminho_video

    # Se o arquivo foi apagado manualmente do disco, limpa o registro obsoleto
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM videos_cache WHERE audio_hash = ?", (audio_hash,))
    return None


def salvar_video_cache(audio_hash: str, caminho_video: str | Path) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO videos_cache (audio_hash, caminho_video)
            VALUES (?, ?)
            """,
            (audio_hash, str(Path(caminho_video).resolve())),
        )