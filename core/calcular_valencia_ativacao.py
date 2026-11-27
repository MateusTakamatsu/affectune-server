from pathlib import Path
import numpy as np
import pandas as pd


def calcular_valencia_ativacao(
    df_features: pd.DataFrame,
    exibir_grafico: bool = False,
    caminho_salvar_grafico: str | Path | None = None,
) -> pd.DataFrame:
    df = df_features.copy()

    def normalizar(serie):
        return (serie - serie.min()) / (serie.max() - serie.min() + 1e-8)

    # 1. Métricas derivadas
    ataques_seg = df["onset_event"].rolling(window=10, min_periods=1).sum()
    df["ataques_seg_norm"] = normalizar(ataques_seg)

    mag_maior = np.hypot(df["tonnetz_terca_maior_x"], df["tonnetz_terca_maior_y"])
    mag_menor = np.hypot(df["tonnetz_terca_menor_x"], df["tonnetz_terca_menor_y"])
    df["balanco_tercas_norm"] = normalizar(mag_maior - mag_menor)

    # 2. Janelas de memória assimétricas (cada frame = 0.1s)
    win_ativ = 15
    rms_suave = df["rms_norm"].rolling(win_ativ, min_periods=1).mean()
    onset_suave = df["onset_strength_norm"].rolling(win_ativ, min_periods=1).mean()
    ataques_suave = df["ataques_seg_norm"].rolling(win_ativ, min_periods=1).mean()
    brilho_suave = df["spectral_centroid_norm"].rolling(win_ativ, min_periods=1).mean()

    win_val = 50
    contraste_suave = df["spectral_contrast_norm"].rolling(win_val, min_periods=1).mean()
    limpeza_suave = (1.0 - df["spectral_flatness_norm"]).rolling(win_val, min_periods=1).mean()
    chroma_suave = df["chroma_std_norm"].rolling(win_val, min_periods=1).mean()
    tercas_suave = df["balanco_tercas_norm"].rolling(win_val, min_periods=1).mean()

    # 3. Cálculo ponderado (escala 0 a 1)
    df["ativacao"] = (
        0.35 * rms_suave
        + 0.25 * onset_suave
        + 0.20 * ataques_suave
        + 0.20 * brilho_suave
    )

    df["valencia"] = (
        0.30 * contraste_suave
        + 0.25 * limpeza_suave
        + 0.25 * chroma_suave
        + 0.20 * tercas_suave
    )

    # 4. Reduz para 1 linha por segundo
    df_seg = df.iloc[::10][["tempo_seg", "valencia", "ativacao"]].copy()
    df_seg["tempo_seg"] = df_seg["tempo_seg"].round().astype(int)

    # 5. Visualização opcional
    if exibir_grafico or caminho_salvar_grafico:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={"width_ratios": [2, 1]})

        ax1.plot(df_seg["tempo_seg"], df_seg["ativacao"], label="Ativação (Energia/Ritmo)", color="#e63946", linewidth=2)
        ax1.plot(df_seg["tempo_seg"], df_seg["valencia"], label="Valência (Positividade/Harmonia)", color="#1d3557", linewidth=2)
        ax1.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
        ax1.set_ylim(0, 1)
        ax1.set_xlabel("Tempo (segundos)")
        ax1.set_ylabel("Índice (0 a 1)")
        ax1.set_title("Dinâmica Emocional por Segundo")
        ax1.legend()
        ax1.grid(alpha=0.2)

        ax2.scatter(df_seg["valencia"], df_seg["ativacao"], c=df_seg["tempo_seg"], cmap="viridis", alpha=0.8)
        ax2.axhline(0.5, color="gray", linestyle="--", alpha=0.6)
        ax2.axvline(0.5, color="gray", linestyle="--", alpha=0.6)
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.set_xlabel("Valência (Negativa ← → Positiva)")
        ax2.set_ylabel("Ativação (Calma ← → Intensa)")
        ax2.set_title("Mapa de Quadrantes (cor = tempo)")
        ax2.text(0.75, 0.92, "Euforia / Alegria", ha="center", fontsize=8, color="gray")
        ax2.text(0.25, 0.92, "Tensão / Raiva", ha="center", fontsize=8, color="gray")
        ax2.text(0.25, 0.05, "Melancolia / Tristeza", ha="center", fontsize=8, color="gray")
        ax2.text(0.75, 0.05, "Calma / Paz", ha="center", fontsize=8, color="gray")

        plt.tight_layout()
        if caminho_salvar_grafico:
            plt.savefig(str(caminho_salvar_grafico), dpi=150)
        if exibir_grafico:
            plt.show()
        plt.close(fig)

    return df_seg