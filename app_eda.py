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
    
REGION_MAP = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
    '제주': 'Jeju'
}

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("\U0001F3E0 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

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

# ---------------------
import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Firebase 설정
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

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# 한글 지역명 → 영어 매핑
REGION_MAP = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
    '제주': 'Jeju'
}

# EDA 클래스 정의
class EDA:
    def __init__(self):
        st.title("\U0001F4CA Population Trends EDA")
        uploaded = st.file_uploader("population_trends.csv 업로드", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드해주세요.")
            return

        self.df = pd.read_csv(uploaded)
        self.clean_data()

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        with tabs[0]: self.basic_statistics()
        with tabs[1]: self.plot_national_trend()
        with tabs[2]: self.plot_region_change()
        with tabs[3]: self.show_top_changes()
        with tabs[4]: self.plot_stacked_area()

    def clean_data(self):
        # '세종' 행의 '-' 처리 후 수치형 변환
        self.df.replace('-', 0, inplace=True)
        cols = ['인구', '출생아수(명)', '사망자수(명)']
        self.df[cols] = self.df[cols].apply(pd.to_numeric, errors='coerce')

    def basic_statistics(self):
        st.header("📊 기초 통계")
        st.write("결측치:", self.df.isnull().sum())
        st.write("중복:", self.df.duplicated().sum())
        buffer = io.StringIO()
        self.df.info(buf=buffer)
        st.text(buffer.getvalue())
        st.dataframe(self.df.describe())

    def plot_national_trend(self):
        st.header("📈 연도별 인구 추이")
        nation = self.df[self.df['지역'] == '전국']
        fig, ax = plt.subplots()
        ax.plot(nation['연도'], nation['인구'], marker='o')
        ax.set_title("National Population")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population")

        last = nation['연도'].max()
        birth_mean = nation.tail(3)['출생아수(명)'].mean()
        death_mean = nation.tail(3)['사망자수(명)'].mean()
        prediction = nation['인구'].values[-1] + (birth_mean - death_mean)*(2035 - last)
        ax.axhline(prediction, color='red', linestyle='--')
        ax.text(2034, prediction, f"Predicted: {int(prediction):,}")
        st.pyplot(fig)

    def plot_region_change(self):
        st.header("📉 지역별 인구 변화량 순위")
        df_recent = self.df[self.df['연도'] >= self.df['연도'].max() - 5]
        pivot = df_recent.pivot(index='지역', columns='연도', values='인구')
        pivot = pivot.drop('전국', errors='ignore')
        pivot['변화량'] = pivot[pivot.columns[-1]] - pivot[pivot.columns[0]]
        pivot['변화율'] = (pivot['변화량'] / pivot[pivot.columns[0]]) * 100
        pivot.index = pivot.index.map(lambda x: REGION_MAP.get(x, x))
        pivot.sort_values('변화량', ascending=False, inplace=True)

        fig1, ax1 = plt.subplots()
        sns.barplot(x=pivot['변화량']/1000, y=pivot.index, ax=ax1)
        ax1.set_title("Change (K)")
        for i, val in enumerate(pivot['변화량']/1000):
            ax1.text(val, i, f"{val:.1f}", va='center')
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        sns.barplot(x=pivot['변화율'], y=pivot.index, ax=ax2)
        ax2.set_title("Change Rate (%)")
        for i, val in enumerate(pivot['변화율']):
            ax2.text(val, i, f"{val:.1f}%", va='center')
        st.pyplot(fig2)

    def show_top_changes(self):
        st.header("🔍 증감률 상위 지역 및 연도")
        df_local = self.df[self.df['지역'] != '전국'].copy()
        df_local['증감'] = df_local.groupby('지역')['인구'].diff()
        top100 = df_local.sort_values('증감', ascending=False).head(100)

        def highlight(val):
            if pd.isnull(val): return ''
            return 'background-color: lightblue' if val > 0 else 'background-color: salmon'

        st.dataframe(
            top100.style.applymap(highlight, subset=['증감']).format({'증감': '{:,.0f}'})
        )

    def plot_stacked_area(self):
        st.header("📊 누적 영역 그래프")
        pivot = self.df.pivot(index='연도', columns='지역', values='인구')
        pivot = pivot.drop('전국', axis=1, errors='ignore')
        pivot.rename(columns=REGION_MAP, inplace=True)

        fig, ax = plt.subplots(figsize=(12, 6))
        pivot.fillna(0).plot.area(ax=ax, colormap="tab20")
        ax.set_title("Population by Region")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population")
        st.pyplot(fig)

# 페이지 등록 및 실행
Page_EDA = st.Page(EDA, title="EDA", icon="📊", url_path="eda")
Page_Home = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_Login = st.Page(Login, title="Login", icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_User = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout = st.Page(Logout, title="Logout", icon="🔓", url_path="logout")

if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
