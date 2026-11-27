from pathlib import Path
import librosa
import numpy as np
import pandas as pd


def extrair_metricas_audio(caminho_mp3: str | Path) -> pd.DataFrame:
    sr = 22050
    hop_length = 2205
    y, sr = librosa.load(str(caminho_mp3), sr=sr)

    y_harm, y_perc = librosa.effects.hpss(y)

    # --- MÉTRICAS DE BASE PARA ATIVAÇÃO ---
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    onset_env = librosa.onset.onset_strength(y=y_perc, sr=sr, hop_length=hop_length)

    janela = 50
    tempo_local = np.zeros(len(onset_env))

    for i in range(len(onset_env)):
        inicio = max(0, i - janela // 2)
        fim = min(len(onset_env), i + janela // 2)

        tempo_local[i] = librosa.feature.tempo(
            onset_envelope=onset_env[inicio:fim],
            sr=sr,
            hop_length=hop_length,
        )[0]

    # --- MÉTRICAS DE BASE PARA VALÊNCIA ---
    chroma = librosa.feature.chroma_cens(y=y_harm, sr=sr, hop_length=hop_length)
    tonnetz = librosa.feature.tonnetz(y=y_harm, sr=sr, hop_length=hop_length)
    contrast = librosa.feature.spectral_contrast(y=y_harm, sr=sr, hop_length=hop_length)
    flatness = librosa.feature.spectral_flatness(y=y_harm, hop_length=hop_length)[0]

    chroma_std = np.std(chroma, axis=0)
    harmonic_change = np.linalg.norm(librosa.feature.delta(chroma), axis=0)
    contrast_mean = np.mean(contrast, axis=0)

    series = [rms, centroid, onset_env, tempo_local, chroma_std, harmonic_change, contrast_mean, flatness]
    min_len = min(min(len(s) for s in series), tonnetz.shape[1])

    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    onset_event = np.zeros(min_len)
    onset_event[onset_frames[onset_frames < min_len]] = 1

    dados = {
        "tempo_seg": np.round(np.arange(min_len) * 0.1, 1),
        "rms": rms[:min_len],
        "spectral_centroid": centroid[:min_len],
        "onset_strength": onset_env[:min_len],
        "onset_event": onset_event,
        "tempo_bpm": tempo_local[:min_len],
        "chroma_std": chroma_std[:min_len],
        "harmonic_change": harmonic_change[:min_len],
        "spectral_contrast": contrast_mean[:min_len],
        "spectral_flatness": flatness[:min_len],
        "tonnetz_quintas_x": tonnetz[0, :min_len],
        "tonnetz_quintas_y": tonnetz[1, :min_len],
        "tonnetz_terca_menor_x": tonnetz[2, :min_len],
        "tonnetz_terca_menor_y": tonnetz[3, :min_len],
        "tonnetz_terca_maior_x": tonnetz[4, :min_len],
        "tonnetz_terca_maior_y": tonnetz[5, :min_len],
    }

    df = pd.DataFrame(dados)

    colunas_ignorar = {"tempo_seg", "onset_event"}
    for col in df.columns:
        if col not in colunas_ignorar:
            c_min, c_max = df[col].min(), df[col].max()
            df[f"{col}_norm"] = (df[col] - c_min) / (c_max - c_min + 1e-8)

    return df