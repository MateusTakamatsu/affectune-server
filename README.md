# Affectune

Tradução visual de emoções musicais para acessibilidade de pessoas com deficiência auditiva.

Projeto da disciplina Projeto em Engenharia da Computação I, do curso de Engenharia da Computação da Universidade do Vale do Paraíba (UNIVAP), turma E.Comp 8-UNA, com orientação do Prof. Me. Hélio Esperidião.

## 👥 Integrantes

- **Luiz Thiago Gonçalves Cassab** (RA: 02310050)
- **Mateus Machado Takamatsu** (RA: 02310341)

## 📌 Descrição

O usuário envia uma música e recebe um **vídeo** com imagens que acompanham a emoção de cada trecho, sincronizadas com o áudio. O sistema segue quatro etapas:

1. **Extração de métricas (PDS):** a biblioteca librosa analisa o áudio em quadros de 0,1 s e calcula RMS, centroide espectral, força de ataques, cromagrama, tonnetz, contraste e planicidade espectral.
2. **Valência e ativação:** médias ponderadas e suavizadas dessas métricas geram, a cada segundo, um ponto no plano valência × ativação, inspirado no modelo circumplexo de Russell. O resultado é determinístico: o mesmo áudio sempre gera o mesmo vídeo.
3. **Seleção de imagens:** para cada segundo, o sistema escolhe a imagem do OASIS com valência e ativação mais próximas (distância euclidiana). Cada imagem fica na tela de 3 a 5 segundos.
4. **Geração do vídeo:** o FFmpeg junta as imagens escolhidas com o áudio original em um arquivo MP4.

O OASIS original tem 900 imagens. Os autores revisaram o conjunto manualmente e removeram 57 imagens com nudez, conteúdo sexual ou violência gráfica; o sistema usa as **843** restantes.

## 🛠️ Tecnologias

- **Linguagem:** Python 3.12
- **Interface:** Gradio, com telas de login e cadastro, envio do áudio e visualização do vídeo
- **Processamento de sinais:** librosa, NumPy e pandas
- **Geração de vídeo e decodificação do áudio:** FFmpeg
- **Banco de dados:** SQLite (módulo `sqlite3` do Python)
- **Imagens afetivas:** OASIS (Open Affective Standardized Image Set)

## ⚙️ Como executar

Pré-requisito: Python 3.12, a versão testada. O FFmpeg é opcional, porque o pacote `imageio-ffmpeg` do `requirements.txt` já fornece um.

1. Clone o repositório:
   ```
   git clone https://github.com/MateusTakamatsu/affectune-server.git
   cd affectune-server
   ```
2. Crie e ative um ambiente virtual:
   - Windows (PowerShell):
     ```
     py -3.12 -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
     Se o PowerShell bloquear a ativação, rode antes `Set-ExecutionPolicy -Scope Process Bypass`. Use `py -3.12` em vez de `python`, que no Windows pode abrir a Microsoft Store.
   - Linux/macOS:
     ```
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Extraia as imagens **dentro da pasta `oasis/`**. O arquivo `images.zip` já contém a pasta `images/`, então o resultado precisa ser `oasis/images/*.jpg`:
   - Windows (PowerShell): `Expand-Archive oasis\images.zip -DestinationPath oasis`
   - Linux/macOS: `unzip oasis/images.zip -d oasis`
5. Rode o servidor:
   ```
   python app.py
   ```
6. Abra o endereço mostrado no terminal (por padrão, http://127.0.0.1:7860), crie uma conta na aba **Criar conta** e envie uma música.

Os vídeos gerados ficam em `output/`. A primeira geração de uma música de 3 minutos leva cerca de 20 a 30 segundos. Se a mesma música for enviada de novo, o vídeo sai do cache em menos de 1 segundo.

## 🗄️ Banco de dados

O banco SQLite `database/affectune.db` é criado automaticamente na primeira execução, pela função `inicializar_banco()` em `database/database.py`. Ele tem duas tabelas:

- **`usuarios`:** id, `username` (único), `senha_hash`, `salt` e `criado_em`. A senha é guardada com PBKDF2-HMAC-SHA256, com 100 000 iterações e salt próprio por usuário.
- **`videos_cache`:** `audio_hash` (chave primária), `caminho_video` e `criado_em`. O `audio_hash` é o SHA-256 do **conteúdo** do áudio. O FFmpeg decodifica o áudio para PCM de 16 bits, mono, 22 050 Hz, antes do cálculo, então o hash não muda se mudarem o nome do arquivo, a capa ou as tags.

Para começar com o banco vazio, apague `database/affectune.db` e a pasta `output/`. O script de criação, o diagrama ER e as instruções de restauração estão na pasta `banco-de-dados/` do pacote de entrega (ZIP).

## 📚 Referências

- KURDI, B.; LOZANO, S.; BANAJI, M. R. Introducing the Open Affective Standardized Image Set (OASIS). *Behavior Research Methods*, v. 49, n. 2, p. 457-470, 2017. DOI: 10.3758/s13428-016-0715-3.
- McFEE, B. et al. librosa: audio and music signal analysis in Python. In: PYTHON IN SCIENCE CONFERENCE, 14., 2015, Austin. *Proceedings* [...]. p. 18-25. DOI: 10.25080/Majora-7b98e3ed-003.
- RUSSELL, J. A. A circumplex model of affect. *Journal of Personality and Social Psychology*, v. 39, n. 6, p. 1161-1178, 1980. DOI: 10.1037/h0077714.
- Documentação oficial: [Gradio](https://www.gradio.app/docs), [librosa](https://librosa.org/doc/latest/index.html), [FFmpeg](https://ffmpeg.org/documentation.html), [SQLite](https://www.sqlite.org/docs.html), [hashlib](https://docs.python.org/3/library/hashlib.html).

As referências completas, no padrão ABNT, estão na pasta `referencias/` do pacote de entrega.

## 🔗 Repositório

https://github.com/MateusTakamatsu/affectune-server
