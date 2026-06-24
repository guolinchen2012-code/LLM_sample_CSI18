import os
import pandas as pd
from google import genai 
from google.genai import types
import streamlit as st

st.title("Welcome to Viet Cuisine Restaurant Website!")

#Load menu cua quan an
menu_df = pd.read_csv("menu.csv")

#Cau hinh chat bot gemini
MODEL_VESION="gemini-2.5-flash"

#prompt 
SYSTEM_INSTRUCTION = f"""
    Bạn tên là PhoBot, một trợ lý AI có nhiệm vụ hỗ trợ giải đáp thông tin cho khách hàng đến nhà hàng Viet Cuisine.
    Các chức năng mà bạn hỗ trợ gồm:
    1. Giới thiệu nhà hàng Viet Cuisine: là một nhà hàng thành lập bởi người Việt, ở địa chỉ 329 Scottmouth, Georgia, USA
    2. Giới thiệu menu của nhà hàng, gồm các món: {', '.join(menu_df['name'].to_list())}.
    3. Hỏi đáp về món ăn trong menu, ví dụ như thành phần món ăn, cách chế biến (dựa trên thông tin trong menu: {menu_df.to_dict(orient='records')})
    Ngoài ba chức năng trên, bạn không hỗ trợ chức năng nào khác. Đối với các câu hỏi ngoài chức năng mà bạn hỗ trợ, trả lời bằng 'Tôi đang không hỗ trợ chức năng này. Xin liên hệ nhân viên nhà hàng qua hotline 318-237-3870 để được trợ giúp.'
    Hãy có thái độ thân thiện và lịch sự khi nói chuyện với khác hàng, vì khách hàng là thượng đế.
"""
INITIAL_MESSAGE= """
Xin chao!

Toi la PhoBot, tro ly truc tuyen cua nha hang Viet Cusine

Toi co the ho tro:
- Giới thiệu nhà hàng Viet Cuisine
- Giới thiệu menu của nhà hàng
- Hỏi đáp về món ăn trong menu

Ban can toi giup gi? (PhoBot cua nha hang Viet Cuisine)

"""

#Ham tao chatbot
def restaurant_chatbot():
    #config cho trang web
    st.set_page_config(
        page_title="PhoBot - Viet Cuisine",
        page_icon=":robot_face:",
        layout="centered",
        )
    
    st.title("PhoBot - Viet Cuisine")

    #slide bar(1 trang nhap API key, 1 trang chat)'
    with st.sidebar:
        st.header("API Key Config")
        api_key=st.text_input(
            "Enter your Gemini API Key",
            type="password",
            placeholder="Enter your Gemini API Key here"
            )
        
        st.divider()

        st.markdown("""
            ###Chuc nang ho tro
            - Giới thiệu nhà hàng Viet Cuisine
            - Giới thiệu menu của nhà hàng
            - Hỏi đáp về món ăn trong menu     
        """)

    if not api_key:
        st.error("Vui lòng nhập API Key để sử dụng chatbot.")
        st.stop()   

    #co API thi tao chat
    try:
        client=genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Loi API key:{e}")
        st.stop()

    #tap section chat 

    if"chat_history" not in st.session_state:
        st.session_state.chat_history=[
            {
                "role":"assistant",
                "content":INITIAL_MESSAGE
            }
        ]

    #hien thi lich su chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # nhap cau hoi tu nguoi dung
    prompt=st.chat_input("Nhap cau hoi cua ban vao day")
    
    if prompt:
        #Luu vao lich su chat
        st.session_state.chat_history.append(
            {
                "role":"user",
                "content":prompt
            }
        )

        #hien thi cau hoi tu nguoi dung
        with st.chat_message("user"):
            st.markdown(prompt)

        #Toi uu hoa(neu can menu thi tra ve menu_df, khong can goi ra API)
        chat_response=""

        if any(word in prompt.lower() for word in ["menu", "thực đơn"]):
            chat_response= f"##Duoi day la menu mon an cua nha hang Viet Cuisine:\n\n"
            for _, row in menu_df.iterrows():
                chat_response += f'### {row["name"]}\n{row["description"]}\n'
        else:
            #goi API de tra loi
            try:
                response=client.models.generate_content(
                    model=MODEL_VESION,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                        max_output_tokens=500,
                    ),
                )

                chat_response=response.text
            except Exception as e:
                st.error(f"Loi khi goi API: {e}")

        #Luu lich su cau tra loi tu chatbot
        st.session_state.chat_history.append(
            {
                "role":"assistant",
                "content":chat_response
            }
        )

        #hien thi cau tra loi tu chatbot
        with st.chat_message("assistant"):
            st.markdown(chat_response)


#chay app
if __name__ == "__main__":
    restaurant_chatbot()