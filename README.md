# tide-clock-epaper

![Example](https://github.com/bwhitman/tide-clock-epaper/blob/main/example.png)

A very simple but useful clock for an ePaper display that shows the weather and tide.

I used this [ePaper display](https://www.waveshare.com/7.5inch-e-paper-hat.htm) alongisde a Raspberry Pi Zero.

To use, get API keys from [OpenWeatherMap](https://openweathermap.org) and [WorldTides](https://www.worldtides.info). Rename `config.py.example` to `config.py` and add your API keys there, along with your actual location, and a URL from [SeaTemperature](https://seatemperature.info) if you want to show that.

Then run `python3 tide.py` and it will generate a black and white PNG file. If the WaveShare libraries are all setup and you run this from a Pi with the hostname of `tideclock`, it will instead update the e-Paper screen. I have this in a cron job on the Pi like so:

```
# m h  dom mon dow   command
@reboot sleep 60 && /home/pi/tide/tide.sh >> /home/pi/tide/log 2>&1
0 * * * * /home/pi/tide/tide.sh >> /home/pi/tide/log 2>&1
```

So that it runs on reboot (after waiting 60s for network to come up) and every hour.

![Live shot](https://github.com/bwhitman/tide-clock-epaper/blob/main/live.png)


