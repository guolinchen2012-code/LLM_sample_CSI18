import os
import pandas as pd
from google import genai 
from google.genai import types
import streamlit as st

# 1. PHẢI ĐẶT ĐẦU TIÊN: Cấu hình trang Streamlit
st.set_page_config(
    page_title="PhoBot - Viet Cuisine",
    page_icon=":robot_face:",
    layout="centered",
)

# Load menu của quán ăn
@st.cache_data
def load_menu():
    try:
        return pd.read_csv("menu.csv")
    except FileNotFoundError:
        # Tạo dataframe giả định nếu chưa có file csv để tránh crash
        return pd.DataFrame({"name": ["Phở Bò", "Gỏi Cuốn"], "description": ["Phở bò truyền thống", "Gỏi cuốn tôm thịt"]})

menu_df = load_menu()

# Cấu hình chat bot gemini
MODEL_VERSION = "gemini-2.5-flash"

# Prompt hệ thống
SYSTEM_INSTRUCTION = f"""
Bạn tên là PhoBot, một trợ lý AI có nhiệm vụ hỗ trợ giải đáp thông tin cho khách hàng đến nhà hàng Viet Cuisine.
Các chức năng mà bạn hỗ trợ gồm:
1. Giới thiệu nhà hàng Viet Cuisine: là một nhà hàng thành lập bởi người Việt, ở địa chỉ 329 Scottmouth, Georgia, USA
2. Giới thiệu menu của nhà hàng, gồm các món: {', '.join(menu_df['name'].to_list())}.
3. Hỏi đáp về món ăn trong menu, ví dụ như thành phần món ăn, cách chế biến (dựa trên thông tin trong menu: {menu_df.to_dict(orient='records')})

Ngoài ba chức năng trên, bạn không hỗ trợ chức năng nào khác. Đối với các câu hỏi ngoài chức năng mà bạn hỗ trợ, trả lời bằng 'Tôi đang không hỗ trợ chức năng này. Xin liên hệ nhân viên nhà hàng qua hotline 318-237-3870 để được trợ giúp.'
Hãy có thái độ thân thiện và lịch sự khi nói chuyện với khách hàng, vì khách hàng là thượng đế.
"""

INITIAL_MESSAGE = """
Xin chào!

Tôi là PhoBot, trợ lý trực tuyến của nhà hàng Viet Cuisine.

Tôi có thể hỗ trợ:
- Giới thiệu nhà hàng Viet Cuisine
- Giới thiệu menu của nhà hàng
- Hỏi đáp về món ăn trong menu

Bạn cần tôi giúp gì?
"""

def restaurant_chatbot():
    st.title("PhoBot - Viet Cuisine")

    # Sidebar nhập API key
    with st.sidebar:
        st.header("API Key Config")
        api_key = st.text_input(
            "Enter your Gemini API Key",
            type="password",
            placeholder="Enter your Gemini API Key here"
        )
        
        st.divider()
        st.markdown("""
            ### Chức năng hỗ trợ
            - Giới thiệu nhà hàng Viet Cuisine
            - Giới thiệu menu của nhà hàng
            - Hỏi đáp về món ăn trong menu     
        """)

    if not api_key:
        st.error("Vui lòng nhập API Key để sử dụng chatbot.")
        st.stop()   

    # Khởi tạo client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Lỗi khởi tạo API client: {e}")
        st.stop()

    # Khởi tạo lịch sử chat trong session_state nếu chưa có
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": INITIAL_MESSAGE
            }
        ]

    # Hiển thị lịch sử chat từ các lượt trước
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Nhập câu hỏi từ người dùng
    prompt = st.chat_input("Nhập câu hỏi của bạn vào đây...")
    
    if prompt:
        # 1. Hiển thị ngay câu hỏi của user lên màn hình
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        chat_response = ""

        # Tối ưu hóa cục bộ: Nếu hỏi menu thì trả về trực tiếp từ file CSV
        if any(word in prompt.lower() for word in ["menu", "thực đơn"]):
            chat_response = "## Dưới đây là menu món ăn của nhà hàng Viet Cuisine:\n\n"
            for _, row in menu_df.iterrows():
                chat_response += f'### {row["name"]}\n{row["description"]}\n\n'
        else:
            # Gọi API và truyền kèm System Instruction
            try:
                # Chuyển đổi lịch sử chat hiện tại sang định dạng types.Content của GenAI SDK để giữ ngữ cảnh hôi thoại
                formatted_contents = []
                for msg in st.session_state.chat_history:
                    # Bỏ qua tin nhắn khởi tạo nếu muốn giảm dung lượng token, hoặc giữ lại tùy bạn
                    role = "user" if msg["role"] == "user" else "model"
                    formatted_contents.append(
                        types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                    )

                response = client.models.generate_content(
                    model=MODEL_VERSION,
                    contents=formatted_contents, # Truyền toàn bộ lịch sử hội thoại vào đây
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.3, # Giảm xuống 0.3 để mô hình bám sát dữ liệu thực tế của quán, ít sáng tạo linh tinh
                        max_output_tokens=1000,
                    ),
                )
                chat_response = response.text
            except Exception as e:
                chat_response = f"Có lỗi xảy ra khi kết nối với AI: {e}"

        # 2. Hiển thị câu trả lời của AI và lưu lại
        with st.chat_message("assistant"):
            st.markdown(chat_response)
        st.session_state.chat_history.append({"role": "assistant", "content": chat_response})
        
        # Đồng bộ lại giao diện Streamlit
        st.rerun()

if __name__ == "__main__":
    restaurant_chatbot()
