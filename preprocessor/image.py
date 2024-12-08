from PIL import Image
import io
import base64

def get_resized_img(uploaded_file, max_size=(300,300)):
    """
    st.file_uploader로 업로드된 파일 객체를 받아 이미지 리사이즈
    Args:
        uploaded_file (UploadedFile): Streamlit file uploader 객체.
        max_size (tuple): 리사이즈할 최대 크기 (width, height).
    Returns:
        BytesIO: 리사이즈된 이미지의 BytesIO 객체.
    """
    # PIL Image로 변환
    with Image.open(uploaded_file) as img:
        img.thumbnail(max_size)
        resized_img = io.BytesIO()  # 메모리 내 파일 객체 생성
        img.save(resized_img, format='JPEG', quality=85)
        print(">>> 이미지 리사이즈 완료")
        resized_img.seek(0)  # 파일 포인터를 처음으로 이동
    return resized_img

def encode_bytesio_to_base64(img_bytes_io):
    """
    BytesIO 객체로부터 base64 문자열 생성
    Args:
        img_bytes_io (BytesIO): BytesIO로 저장된 이미지 객체.
    Returns:
        str: base64로 인코딩된 이미지 문자열.
    """
    # BytesIO 객체를 base64로 인코딩
    encoded_string = base64.b64encode(img_bytes_io.read()).decode('utf-8')
    return encoded_string

