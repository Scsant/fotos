import streamlit as st
from PIL import Image
import exifread
import pandas as pd
import os
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np

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

# Classe para captura de frames da câmera
class VideoTransformer(VideoTransformerBase):
    def __init__(self):
        self.frame = None

    def transform(self, frame):
        self.frame = frame.to_ndarray(format="bgr24")
        return frame

# Configuração inicial
data_file = "local_data.csv"
os.makedirs("images", exist_ok=True)

if not os.path.exists(data_file):
    pd.DataFrame(columns=["Imagem", "Latitude", "Longitude", "Descrição"]).to_csv(data_file, index=False)

# Streamlit UI
st.title("Aplicativo de Captura de Fotos com Informações de Localização")

# WebRTC para capturar imagens
ctx = webrtc_streamer(key="example", video_transformer_factory=VideoTransformer, rtc_configuration={"iceServers": []})

if ctx.video_transformer:
    if st.button("Capturar Foto"):
        if ctx.video_transformer.frame is not None:
            image = ctx.video_transformer.frame
            image_path = os.path.join("images", "captured_image.jpg")
            cv2.imwrite(image_path, image)
            st.image(image, caption="Imagem capturada", use_column_width=True)

            # Obter coordenadas GPS
            lat, lon = get_gps_coordinates(image_path)

            if lat and lon:
                st.success(f"Coordenadas GPS extraídas: Latitude {lat}, Longitude {lon}")
            else:
                st.warning("Não foi possível obter coordenadas GPS desta imagem.")

            # Formulário para descrição
            description = st.text_input("Adicione uma descrição para o local")

            # Botão para salvar
            if st.button("Salvar informações"):
                new_data = {"Imagem": "captured_image.jpg", "Latitude": lat, "Longitude": lon, "Descrição": description}
                df = pd.read_csv(data_file)
                df = df.append(new_data, ignore_index=True)
                df.to_csv(data_file, index=False)
                st.success("Informações salvas com sucesso!")

# Exibir tabela com informações salvas
if st.checkbox("Exibir dados salvos"):
    df = pd.read_csv(data_file)
    st.dataframe(df)
