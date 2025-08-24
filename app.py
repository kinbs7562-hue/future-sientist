import streamlit as st
import requests

# 🔑 OpenWeather API 키 입력
API_KEY = "3231c90d13ace8e403a9459ea9a92236"

# ----------------------------
# 좌표 변환 (주소 → 위도/경도)
# ----------------------------
def get_coordinates(address):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"
    headers = {"User-Agent": "streamlit-app"}  # ✅ User-Agent 추가
    response = requests.get(url, headers=headers).json()
    if response:
        lat = float(response[0]["lat"])
        lon = float(response[0]["lon"])
        return lat, lon
    return None, None

# ----------------------------
# 날씨 정보 가져오기 (OpenWeather)
# ----------------------------
def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=kr"
    response = requests.get(url).json()
    if "main" in response:
        rain = response.get("rain", {}).get("1h", 0)  # 1시간 강수량 (mm)
        return {
            "temp": response["main"]["temp"],
            "humidity": response["main"]["humidity"],
            "desc": response["weather"][0]["description"],
            "wind": response["wind"]["speed"],
            "rain": rain
        }
    return None

# ----------------------------
# 산불 위험도 점수 + 단계
# ----------------------------
def get_fire_risk_score(temp, humidity, rain, wind):
    temp_score = min(max(temp / 40 * 30, 0), 30)
    humidity_score = min(max((100 - humidity) / 100 * 30, 0), 30)
    rain_score = min(max((1 - min(rain, 20) / 20) * 20, 0), 20)
    wind_score = min(max(wind / 20 * 20, 0), 20)

    score = temp_score + humidity_score + rain_score + wind_score
    score = round(score, 1)

    # 🔥 최대 99% 제한
    if score >= 99:
        score = 99

    # 위험 단계 판정
    if score < 30:
        level = "낮음"
    elif score < 60:
        level = "보통"
    elif score < 80:
        level = "높음"
    else:
        level = "매우 높음"

    return score, level

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="날씨 + 산불 위험도 알리미", page_icon="🔥", layout="centered")

st.title("🔥 날씨 + 산불 위험도 알리미")

address = st.text_input("시/동 이름을 입력하세요 (예: 서울특별시 강남구 역삼동)", "")

if st.button("조회하기"):
    if not address.strip():
        st.error("주소를 입력해주세요.")
    else:
        lat, lon = get_coordinates(address)
        if not lat:
            st.error("주소를 찾을 수 없습니다.")
        else:
            weather = get_weather(lat, lon)
            if not weather:
                st.error("날씨 정보를 가져올 수 없습니다.")
            else:
                st.success(f"📍 위치: {address}")
                st.write(f"🌡️ 기온: {weather['temp']}°C")
                st.write(f"💧 습도: {weather['humidity']}%")
                st.write(f"☁️ 날씨: {weather['desc']}")
                st.write(f"🌬️ 바람: {weather['wind']} m/s")
                st.write(f"🌧️ 강수량(최근 1시간): {weather['rain']} mm")

                score, level = get_fire_risk_score(
                    weather["temp"], weather["humidity"], weather["rain"], weather["wind"]
                )
                st.warning(f"🔥 산불 위험도: {score}% → {level}")
                st.progress(score / 100)
