from pathlib import Path
import numpy as np
import pandas as pd


def selecionar_imagens(
    df_audio: pd.DataFrame,
    caminho_oasis_csv: str | Path,
    raio_afastamento: float = 0.15,
    min_duracao_seg: int = 3,
    max_duracao_seg: int = 5,
) -> pd.DataFrame:
    df_audio = df_audio.copy()
    df_imgs = pd.read_csv(caminho_oasis_csv).rename(columns={"Unnamed: 0": "img_id"})

    # Normalizar imagens de [1, 7] para [0, 1]
    df_imgs["val_norm"] = (df_imgs["Valence_mean"] - 1.0) / 6.0
    df_imgs["ati_norm"] = (df_imgs["Arousal_mean"] - 1.0) / 6.0

    coords_imgs = df_imgs[["val_norm", "ati_norm"]].to_numpy()
    ids_imgs = df_imgs["img_id"].to_numpy()
    themes_imgs = dict(zip(df_imgs["img_id"], df_imgs["Theme"]))

    escolhas = []
    img_atual_idx = None
    inicio_bloco = 0

    # Processo de escolha de imagens baseado na distância euclidiana
    # entre os pontos de valência/ativação do áudio e das imagens
    for _, row in df_audio.iterrows():
        tempo = int(row["tempo_seg"])
        ponto_audio = np.array([row["valencia"], row["ativacao"]])
        distancias = np.linalg.norm(coords_imgs - ponto_audio, axis=1)

        if img_atual_idx is None:
            img_atual_idx = int(np.argmin(distancias))
            inicio_bloco = tempo
        else:
            dist_atual = distancias[img_atual_idx]
            duracao_atual = tempo - inicio_bloco

            # Condicoes de troca de imagem
            expirou_tempo = duracao_atual >= max_duracao_seg
            afastou_suficiente = (
                dist_atual > raio_afastamento and duracao_atual >= min_duracao_seg
            )

            if expirou_tempo or afastou_suficiente:
                if expirou_tempo and len(distancias) > 1:
                    # Impede que a mesma imagem seja reescolhida e fundida no groupby
                    dist_candidatas = distancias.copy()
                    dist_candidatas[img_atual_idx] = np.inf
                    melhor_idx = int(np.argmin(dist_candidatas))
                else:
                    melhor_idx = int(np.argmin(distancias))

                if melhor_idx != img_atual_idx:
                    img_atual_idx = melhor_idx
                    inicio_bloco = tempo

        escolhas.append(ids_imgs[img_atual_idx])

    df_audio["img_id"] = escolhas

    # Agrupar intervalos contínuos para gerar o guia
    df_audio["bloco"] = (df_audio["img_id"] != df_audio["img_id"].shift()).cumsum()
    guia = (
        df_audio.groupby("bloco")
        .agg(
            inicio_seg=("tempo_seg", "min"),
            ultimo_seg=("tempo_seg", "max"),
            img_id=("img_id", "first"),
        )
        .reset_index(drop=True)
    )

    guia["fim_seg"] = guia["ultimo_seg"] + 1
    guia["duracao_seg"] = guia["fim_seg"] - guia["inicio_seg"]
    guia["theme"] = guia["img_id"].map(themes_imgs)

    return guia[["inicio_seg", "fim_seg", "duracao_seg", "img_id", "theme"]]