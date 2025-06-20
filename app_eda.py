import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("\U0001F3E0 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}\uB2D8 \uD658\uC601\uD569\uB2C8\uB2E4.")

        st.markdown("""
           ---
           **Population Trends 데이터셋**  
           - 설명: 지역별 연도별 인구, 출생자수, 사망자수 등의 통계
           - 분석 주제: 인구 변화 분석 및 시각화
           """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("\U0001F4CA Population Trends 분석")
        uploaded = st.file_uploader("population_trends.csv 업로드", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드해주세요.")
            return

        df = pd.read_csv(uploaded)
        df.replace('-', 0, inplace=True)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        with tabs[0]:
            st.subheader("기초 통계")
            st.write("결측치:", df.isnull().sum())
            st.write("중복:", df.duplicated().sum())
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())

        with tabs[1]:
            st.subheader("연도별 인구 추이")
            nation = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            ax.plot(nation['연도'], nation['인구'], marker='o')
            ax.set_title("National Population")
            last = nation['연도'].max()
            birth = nation.tail(3)['출생아수(명)'].mean()
            death = nation.tail(3)['사망자수(명)'].mean()
            pred = nation['인구'].values[-1] + (birth - death) * (2035 - last)
            ax.axhline(pred, color='red', linestyle='--')
            ax.text(2034, pred, f"Predicted: {int(pred):,}")
            st.pyplot(fig)

        with tabs[2]:
            st.subheader("최근 5년 지역별 인구 변화")
            recent = df[df['연도'] >= df['연도'].max() - 5]
            pivot = recent.pivot(index='지역', columns='연도', values='인구').dropna()
            pivot['변화량'] = pivot[pivot.columns[-1]] - pivot[pivot.columns[0]]
            pivot['변화율'] = (pivot['변화량'] / pivot[pivot.columns[0]]) * 100
            pivot.index = pivot.index.map(lambda x: REGION_MAP.get(x, x))
            pivot = pivot.sort_values('변화량', ascending=False)

            fig, ax = plt.subplots()
            sns.barplot(x=pivot['변화량']/1000, y=pivot.index, ax=ax)
            st.pyplot(fig)

        with tabs[3]:
            st.subheader("증감률 상위 100")
            df_local = df[df['지역'] != '전국'].copy()
            df_local['증감'] = df_local.groupby('지역')['인구'].diff()
            top100 = df_local.sort_values('증감', ascending=False).head(100)

            def highlight(val):
                color = 'background-color: lightblue' if val > 0 else 'background-color: salmon'
                return color

            styled = top100.style.applymap(highlight, subset=['증감']).format("{:,}")
            st.dataframe(styled)

        with tabs[4]:
            st.subheader("누적 영역 시각화")
            area_df = df.pivot(index='연도', columns='지역', values='인구').drop('전국', axis=1, errors='ignore').fillna(0)
            area_df.rename(columns=REGION_MAP, inplace=True)
            fig, ax = plt.subplots(figsize=(12, 6))
            area_df.plot.area(ax=ax, colormap='tab20')
            st.pyplot(fig)
