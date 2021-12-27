import sys, os, json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone

# has tide_key, owm_key, weather_city, weather_country, tide_lat, tide_lon, sea_temperature_url
import config 

img = Image.new("L",(800,480), (255))
d = ImageDraw.Draw(img)

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def text_at(text, x, y, size=20):
    fnt = ImageFont.truetype("helvetica.ttf",size)
    d.text((x,y), text, font=fnt, fill=(0))

def icon_for_text(text, x, y):
    ic = "cloudy.png"
    if(text == "Rain" or text=="Drizzle"): ic = "rain.png"
    if(text == "Fog"): ic = "fog.png"
    if(text == "Thunderstorm"): ic = "storm.png"
    if(text == "Snow"): ic = "snow.png"
    if(text == "Clear"): ic = "sun.png"
    if(text == "Ocean"): ic = "ocean.png"
    icon = Image.open(ic)
    img.paste(icon, (x, y), icon)       

def get_weather():
    from pyowm import OWM
    owm = OWM(config.owm_key)
    mgr = owm.weather_manager()
    reg = owm.city_id_registry()
    list_of_locations = reg.locations_for(config.weather_city, country=config.weather_country)
    mine = list_of_locations[0]
    return mgr.one_call(lat=mine.lat, lon=mine.lon)

def get_sea_temperature():
    import requests, re
    try:
        user_agent = {'User-agent': 'Mozilla/5.0'}
        resp = requests.get(config.sea_temperature_url,headers=user_agent)
        res = re.search(r"today is (.*?)\&deg", resp.text)
        return float(res.groups()[0])
    except:
        return 0

def get_tides(cached=False):
    import requests, time
    try:
        if(time.time() - os.stat("tides.json").st_mtime) < 86400:
            return json.load(open('tides.json'))
    except FileNotFoundError:
        pass
    resp = requests.get("https://www.worldtides.info/api/v2?localtime=1&heights&datum=CD&datums&lat=%s&lon=%s&days=3&key=%s" % \
        (config.tide_lat, config.tide_lon, config.tide_key))
    w = open('tides.json','w')
    w.write(resp.text)
    w.close()
    return resp.json()

def draw_to_epd():  
    from waveshare_epd import epd7in5_V2
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()
    epd.display(epd.getbuffer(img))
    epd.sleep()

def hourstring(dt):
    if(dt.hour == 12): return "12pm"
    if(dt.hour == 0): return "12am"
    ampm = "am"
    if(dt.hour >= 12): ampm = "pm"
    return "%d%s" % (dt.hour % 12, ampm)

def draw_tides(tides, x=0,y=0, w=800, h=200,hours=48):
    min_height = 100
    max_height = -100
    t = []
    date = []
    now = -1
    for height in tides["heights"][:hours*2]:
        indicated_date = datetime.fromisoformat(height["date"])
        if(now == -1 and indicated_date > datetime.now().astimezone()): now = len(t)
        date.append(indicated_date)
        height = height["height"]
        if height > max_height: max_height = height
        if height < min_height: min_height = height
        t.append(height)

    segments = []
    for i,height in enumerate(t):
        scaled_y = (height - min_height) / (max_height-min_height)
        scaled_x = float(i) / float(len(tides["heights"][:hours*2]))
        draw_y = y + 20 + ((1-scaled_y) * h)
        draw_x = x + (scaled_x * w)
        segments.append((draw_x, draw_y))
        if(i % 8 == 0):
            text_at(hourstring(date[i]), draw_x, y, 20)
        if(i == now):
            draw_now_y = draw_y
            draw_now_x = draw_x

    icon = Image.open("swim.png")
    img.paste(icon, (int(draw_now_x), int(draw_now_y)), icon)

    d.line([x+50, y+25, x, y+25, x, y+h+15, x+50, y+h+15])
    text_at("%2.1fm" % (max_height), x, y+25)
    text_at("%2.1fm" % (min_height), x, y+h-5)
    d.line(segments, fill = (0), width=1)



def main():
    margin = 20
    weather = get_weather()
    draw_tides(get_tides(cached=True), x=margin,y=margin)

    now = weather.current
    daily = weather.forecast_daily
    hourly = weather.forecast_hourly

    d.line([margin-10, 250, 170, 250, 170, 360, margin-10, 360, margin-10, 250])
    icon_for_text(now.status, margin, 290)
    text_at("%2.1f°" % (now.temperature("celsius")["temp"]), margin, 330, 20)
    text_at("Wind: %2.1f kph" % (now.wind()["speed"]*3.6), margin, 270, 20)
    text_at("%2.1f°" % (get_sea_temperature()), margin+100, 330, 20)
    icon_for_text("Ocean", margin+100, 290)
    for i in range(1,7):
        dt = utc_to_local(hourly[i].reference_time('date'))
        text_at(hourstring(dt), margin + (i+1)*100, 270, 20)
        icon_for_text(hourly[i].status, margin + (i+1)*100, 290)
        text_at("%2.1f°" % (hourly[i].temperature("celsius")["temp"]), margin + (i+1)*100, 330, 20)

    for i in range(8):
        dt = utc_to_local(daily[i].reference_time('date'))
        text_at('%s' % (dt.strftime('%A')[:3]), margin + i*100, 370, 20)
        icon_for_text(daily[i].status, margin + i*100, 390)
        text_at("%2.1f°" % (daily[i].temperature("celsius")["min"]), margin + i*100, 430, 20)
        text_at("%2.1f°" % (daily[i].temperature("celsius")["max"]), margin + i*100, 450, 20)

    if(os.uname().nodename.startswith("tideclock")):
        draw_to_epd()   
    else:
        img.show()

if __name__ == "__main__":
    main()


