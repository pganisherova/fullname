from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import httpx

app = FastAPI(
    title="Obhavo.uz API",
    description="Obhavo.uz saytidan kunlik va haftalik ob-havo ma'lumotlarini oluvchi norasmiy API.",
    version="1.0.0"
)

async def fetch_html(url: str) -> str:
    """Saytdan HTML kodini asinxron tarzda yuklab olish"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Shahar topilmadi yoki sayt ishlamayapti")
        return response.text

def parse_weather_data(html: str) -> dict:
    """HTML dan ob-havo ma'lumotlarini ajratib olish (Parsing)"""
    soup = BeautifulSoup(html, "html.parser")
    
    try:
        # Shahar nomi va bugungi sana
        city_name = soup.find("h2").text.strip()
        current_day = soup.find("div", class_="current-day").text.strip()
        
        # Bugungi asosiy harorat
        forecast_div = soup.find("div", class_="current-forecast")
        spans = forecast_div.find_all("span")
        temp_day = spans[1].text.strip()
        temp_night = spans[2].text.strip()
        
        # Ob-havo tavsifi (masalan: Yomg'ir, Ochiq havo)
        description = soup.find("div", class_="current-forecast-desc").text.strip()
        
        # Qo'shimcha ma'lumotlar (Namlik, Shamol, Bosim va h.k)
        details_col1 = soup.find("div", class_="col-1").find_all("p")
        humidity = details_col1[0].text.replace("Namlik:", "").strip()
        wind = details_col1[1].text.replace("Shamol:", "").strip()
        pressure = details_col1[2].text.replace("Bosim:", "").strip()
        
        details_col2 = soup.find("div", class_="col-2").find_all("p")
        moon = details_col2[0].text.replace("Oy:", "").strip()
        sunrise = details_col2[1].text.replace("Quyosh chiqishi:", "").strip()
        sunset = details_col2[2].text.replace("Quyosh botishi:", "").strip()
        
        current_weather = {
            "temp_day": temp_day,
            "temp_night": temp_night,
            "description": description,
            "humidity": humidity,
            "wind": wind,
            "pressure": pressure,
            "moon": moon,
            "sunrise": sunrise,
            "sunset": sunset
        }
        
        # Haftalik ob-havo ma'lumotlari
        weekly_forecast = []
        table = soup.find("table", class_="weather-table")
        if table:
            rows = table.find_all("tr")[1:]  # Birinchi qatorni (sarlavhani) tashlab o'tamiz
            for row in rows:
                day_div = row.find("td", class_="weather-row-day")
                if not day_div:
                    continue
                
                day_name = day_div.find("strong").text.strip()
                date_val = day_div.find("div").text.strip()
                
                forecast_td = row.find("td", class_="weather-row-forecast")
                t_day = forecast_td.find("span", class_="forecast-day").text.strip()
                t_night = forecast_td.find("span", class_="forecast-night").text.strip()
                
                row_desc = row.find("td", class_="weather-row-desc").text.strip()
                row_pop = row.find("td", class_="weather-row-pop").text.strip()
                
                weekly_forecast.append({
                    "day": day_name,
                    "date": date_val,
                    "temp_day": t_day,
                    "temp_night": t_night,
                    "description": row_desc,
                    "precipitation": row_pop
                })
                
        return {
            "city": city_name,
            "date": current_day,
            "current": current_weather,
            "weekly": weekly_forecast
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ma'lumotlarni parse qilishda xatolik yuz berdi: {str(e)}")

@app.get("/")
def read_root():
    return {
        "message": "Obhavo.uz API ga xush kelibsiz",
        "endpoints": {
            "/weather/{city}": "Shahar bo'yicha ob-havo ma'lumotlarini olish (masalan: /weather/tashkent yoki /weather/navoi)"
        }
    }

@app.get("/weather/{city}")
async def get_weather(city: str):
    """
    Kiritilgan shahar nomi asosida ob-havo ma'lumotlarini qaytaradi.
    Shahar nomlari lotin harflarida kiritilishi kerak (masalan: tashkent, navoi, samarkand).
    """
    url = f"https://obhavo.uz/{city.lower()}"
    html_content = await fetch_html(url)
    data = parse_weather_data(html_content)
    return data

 
