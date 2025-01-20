import streamlit as st
from PIL import Image, UnidentifiedImageError
import exifread
import pandas as pd
import os

# Função para extrair coordenadas GPS de uma imagem
def get_gps_coordinates(image_path):
    try:
        with open(image_path, 'rb') as img_file:
            tags = exifread.process_file(img_file)
            gps_latitude = tags.get('GPS GPSLatitude')
            gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
            gps_longitude = tags.get('GPS GPSLongitude')
            gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = convert_to_degrees(gps_latitude)
                if gps_latitude_ref.values[0] != 'N':
                    lat = -lat

                lon = convert_to_degrees(gps_longitude)
                if gps_longitude_ref.values[0] != 'E':
                    lon = -lon

                return lat, lon
    except Exception as e:
        st.error(f"Erro ao processar EXIF: {e}")
    return None, None

# Conversão para graus decimais
def convert_to_degrees(value):
    d, m, s = [float(v.num) / float(v.den) for v in value.values]
    return d + (m / 60.0) + (s / 3600.0)

# Configuração inicial
data_file = "local_data.csv"
os.makedirs("files", exist_ok=True)

if not os.path.exists(data_file):
    pd.DataFrame(columns=["Arquivo", "Latitude", "Longitude", "Descrição", "Tipo"]).to_csv(data_file, index=False)

# Streamlit UI
st.title("Aplicativo de Captura de Mídia com Informações de Localização")

uploaded_files = st.file_uploader("Selecione imagens, vídeos, PDFs ou arquivos ZIP", 
                                  type=['jpg', 'jpeg', 'png', 'mp4', 'avi', 'pdf', 'zip'], 
                                  accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join("files", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if uploaded_file.type.startswith('image'):
            try:
                st.image(Image.open(file_path), caption=f"Imagem carregada: {uploaded_file.name}", use_column_width=True)
                lat, lon = get_gps_coordinates(file_path)
            except UnidentifiedImageError:
                st.error(f"O arquivo {uploaded_file.name} não é uma imagem válida.")
                lat, lon = None, None

        elif uploaded_file.type.startswith('video'):
            st.video(file_path)
            lat, lon = None, None  # Processamento de metadados de vídeo pode ser adicionado posteriormente

        elif uploaded_file.type == 'application/pdf':
            st.success(f"PDF {uploaded_file.name} carregado com sucesso!")
            lat, lon = None, None

        elif uploaded_file.type == 'application/zip':
            st.success(f"Arquivo ZIP {uploaded_file.name} carregado com sucesso!")
            lat, lon = None, None
        else:
            st.warning(f"Tipo de arquivo não suportado: {uploaded_file.type}")
            continue

        description = st.text_input(f"Adicione uma descrição para {uploaded_file.name}")

        if st.button(f"Salvar informações de {uploaded_file.name}"):
            new_data = {"Arquivo": uploaded_file.name, "Latitude": lat, "Longitude": lon, "Descrição": description, "Tipo": uploaded_file.type}
            df = pd.read_csv(data_file)
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(data_file, index=False)
            st.success(f"Informações de {uploaded_file.name} salvas com sucesso!")

# Exibir tabela com informações salvas
if st.checkbox("Exibir dados salvos"):
    df = pd.read_csv(data_file)
    st.dataframe(df)

# Função para permitir download dos arquivos

def download_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            st.download_button(label=f"Baixar {os.path.basename(file_path)}", data=f, file_name=os.path.basename(file_path))
    else:
        st.warning(f"O arquivo {os.path.basename(file_path)} não existe mais para download.")

# Função para deletar um arquivo
def delete_file(file_path):
    try:
        os.remove(file_path)
        st.success(f"Arquivo {os.path.basename(file_path)} deletado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao deletar o arquivo {os.path.basename(file_path)}: {e}")

# Permitir o download e a exclusão das imagens carregadas
if os.path.exists("files"):
    file_list = os.listdir("files")
    for file_name in file_list:
        file_path = os.path.join("files", file_name)

        col1, col2 = st.columns([3, 1])
        with col1:
            download_file(file_path)
        with col2:
            if st.button(f"Deletar {file_name}"):
                delete_file(file_path)
