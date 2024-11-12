import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from io import BytesIO

# Fungsi untuk mengatasi missing value
def handle_missing_values(data):
    data = data.applymap(lambda x: np.nan if isinstance(x, str) and x.isspace() else x)
    st.write("Informasi setelah mengganti string kosong dan whitespace dengan NaN:")
    st.write(data.info())
    for column in data.select_dtypes(include=['object']).columns:
        data[column] = data[column].fillna(method='ffill').fillna(method='bfill')
    for column in data.select_dtypes(include=[np.number]).columns:
        data[column] = data[column].fillna(data[column].mean())
    return data

# Fungsi untuk membersihkan outlier menggunakan IQR
def remove_outliers(data, column):
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    filtered_data = data[(data[column] >= lower_bound) & (data[column] <= upper_bound)]
    outliers_removed = len(data) - len(filtered_data)
    st.write(f"Jumlah data outlier yang telah dibersihkan pada kolom '{column}': {outliers_removed}")
    return filtered_data

# Fungsi untuk encoding variabel kategorik
def encode_categorical(data):
    label_encoders = {}
    for column in data.select_dtypes(include=['object']).columns:
        data[column] = data[column].astype(str)
        le = LabelEncoder()
        data[column] = le.fit_transform(data[column])
        label_encoders[column] = le
    return data, label_encoders

# Fungsi untuk mengonversi DataFrame ke format Excel
def to_excel(data):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        data.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# Judul aplikasi
st.title("Aplikasi Preprocessing Data Berbasis Streamlit")

# Upload dataset
uploaded_file = st.file_uploader("Unggah file CSV atau Excel", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        data = pd.read_excel(uploaded_file)

    data = data.applymap(lambda s: s.lower() if isinstance(s, str) else s)
    
    # Penggantian nilai dalam kolom 'BB_U' jika kolom tersebut ada
    if 'BB_U' in data.columns:
        bb_u_columns = ['BB_U']
        data[bb_u_columns] = data[bb_u_columns].applymap(lambda x: str(x).strip())
        data[bb_u_columns] = data[bb_u_columns].replace(
            to_replace=['kurang', 'berat kurang'],
            value='berat badan kurang'
        )
        data[bb_u_columns] = data[bb_u_columns].replace(
            to_replace=['normal', 'berat normal'],
            value='berat badan normal'
        )
        data[bb_u_columns] = data[bb_u_columns].replace(
            to_replace=['sangat kurang'],
            value='berat badan sangat kurang'
        )

    # Penggantian nilai dalam kolom 'TB_U' jika kolom tersebut ada
    if 'TB_U' in data.columns:
        tb_u_columns = ['TB_U']
        data[tb_u_columns] = data[tb_u_columns].applymap(lambda x: str(x).strip())
        data[tb_u_columns] = data[tb_u_columns].replace(
            to_replace=['pendeek api testing'],
            value='pendek'
        )
        data[tb_u_columns] = data[tb_u_columns].replace(
            to_replace=['sangat pendek'],
            value='sangat pendek'
        )

    # Pembersihan duplikat data
    st.write("Jumlah data sebelum menghapus duplikat:", len(data))
    data = data.drop_duplicates()
    st.write("Jumlah data setelah menghapus duplikat:", len(data))

    # Tampilkan data awal
    st.write("Data Awal:")
    st.write(data.head())

    # Menampilkan kolom kategorikal dan numerik
    categorical_columns = data.select_dtypes(include=['object']).columns
    non_categorical_columns = data.select_dtypes(include=[np.number]).columns
    st.write("Kolom Kategorikal:", list(categorical_columns))
    st.write("Kolom Numerik:", list(non_categorical_columns))

    # Penanganan missing value
    st.header("Penanganan Missing Value")
    data = handle_missing_values(data)
    st.write("Data setelah penanganan missing value:")
    st.write(data.head())

    missing_values = data.isnull().sum()
    st.write("Apakah masih ada missing value di setiap kolom?")
    st.write(missing_values[missing_values > 0])

    # Pembersihan outlier
    st.header("Pembersihan Outlier")
    num_columns = data.select_dtypes(include=[np.number]).columns
    if len(num_columns) > 0:
        outlier_column = st.selectbox("Pilih kolom numerik untuk membersihkan outlier", num_columns)
        data = remove_outliers(data, outlier_column)
        st.write(f"Data setelah pembersihan outlier pada kolom {outlier_column}:")
        st.write(data.head())
    else:
        st.write("Tidak ada kolom numerik untuk pembersihan outlier.")

    # Encoding data kategorik
    st.header("Encoding Data Kategorik")
    data, label_encoders = encode_categorical(data)
    st.write("Data setelah encoding:")
    st.write(data.head())

    # Unduh data yang telah diproses
    st.header("Unduh Data yang Telah Diproses")
    file_name = st.text_input("Masukkan nama file (tanpa ekstensi)", "processed_data")
    format_option = st.selectbox("Pilih format file", ["CSV", "Excel"])

    if format_option == "CSV":
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Unduh CSV",
            data=csv,
            file_name=f"{file_name}.csv",
            mime="text/csv"
        )
    elif format_option == "Excel":
        excel = to_excel(data)
        st.download_button(
            label="Unduh Excel",
            data=excel,
            file_name=f"{file_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
