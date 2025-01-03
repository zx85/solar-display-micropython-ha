# on-board goodies
import sys
import os
import gc
import uasyncio
import urequests as requests
from time import sleep, gmtime, localtime
import network
from machine import Pin, SPI, reset

sys.path.append("/include")
# external things
from ili9341 import Display, color565
from xglcd_font import XglcdFont
from math import sin,cos,pi

# Global variables so it can be persistent
solar_usage = {}
# led_bright = 800
CRED_FILE = const("config/credentials.env")
SOLIS_FILE = const("config/solis.env")

clear_btn = Pin(0, Pin.IN, Pin.PULL_UP)
bl_pin = Pin(21, Pin.OUT)
bl_state = True
bl_night_start = "23"
bl_night_end = "5"

# Define the display doings
spi1 = SPI(1, baudrate=40000000, sck=Pin(14), mosi=Pin(13))
display = Display(spi1, dc=Pin(2), cs=Pin(15), rst=Pin(0), rotation=270)
bl_pin.on()
gc.collect()

# load the fonts
font = XglcdFont('fonts/FuturaNum21x39.c', 21, 39, 46)
font_uom = XglcdFont('fonts/Calibri12x14.c', 12, 14, 87)
font_num = XglcdFont('fonts/FuturaNum20x22.c', 20, 22, 47)
font_icon = XglcdFont('fonts/Emoji24x24.c',24, 24, 49)

# Local time doings
def stringTime(thisTime):
    year, month, date, hour, minute, second, week_day, year_day = thisTime
    week_day_lookup = b"MonTueWedThuFriSatSun"
    month_lookup = b"JanFebMarAprMayJunJulAugSepOctNovDec"
    stringTime = (
        week_day_lookup.decode()[week_day * 3 : week_day * 3 + 3]
        + ", "
        + f"{date:02}"
        + " "
        + month_lookup.decode()[(month - 1) * 3 : (month - 1) * 3 + 3]
        + " "
        + f"{year:02}"
        + " "
        + f"{hour:02}"
        + ":"
        + f"{minute:02}"
        + ":"
        + f"{second:02}"
        + " GMT"
    )
    return stringTime


def get_ha(ha_info):
    headers={"Authorization": "Bearer "+ha_info['ha_token'].decode("utf-8"),
             "content-type": "application/json"}
    solar_dict = {}
    ha_url = ha_info["ha_url"].decode("utf-8")+"/api/states/input_text.solar_display_data"
    print(f"Getting data...")
    try:
        gc.collect()
        resp=requests.get(url=ha_url,headers=headers,timeout=10)
        solar_dict=resp.json()['attributes']['info']
        print(f"Here's what I got: {solar_dict}")
    except Exception as e:
        print(f" ... o no!\nI couldn't get the data from {ha_url}")
        print(f"Exception: {e}")

    return solar_dict

def validate_data(solar_usage):
    # Sanity check printing business
    success=True
    for each_param in ["timestamp",
                       "solar_in",
                       "battery_per",
                       "grid_in",
                       "power_used",
                       "solar_today",
                       "export_today",
                       "grid_in_today"]:
        if each_param in solar_usage:
            print(f"{each_param} is {solar_usage[each_param]}")
        # Extra bit to sort out occasional negative export
            if each_param=="export_today":
                if float(solar_usage[each_param])<0:
                    solar_usage[each_param]="0.0"   
        else:
            print(f"{each_param} is empty - skipping this run")
            success=False
    if success:
        return solar_usage
    else:
        return False

def bl_control(timestamp):
    global bl_state
    timestamp_value=timestamp.split("T")[1][:2]
    if timestamp_value==bl_night_end and not(bl_state):
        print("Turning backlight on")
        bl_state=True
        bl_pin.on()
    if timestamp_value==bl_night_start and bl_state:
        print("Turning backlight off")
        bl_state=False
        bl_pin.off()

# Display function - does all the doings
def display_data(solar_usage,force=False):
    if solar_usage:=validate_data(solar_usage):
        if force or (solar_usage["timestamp"] != solar_usage["prev_timestamp"]):
            gc.collect()
            print("Solis data has been updated - do the LCD thing...")
            display.clear()

            bl_control(solar_usage["timestamp"]) # do stuff with the backlight

            ############
            # solar_in #
            ############
            solar_in_max=5000
            solar_in_val=float(solar_usage["solar_in"])
            solar_in_per=int(solar_in_val/solar_in_max*100)

            if solar_in_val>1000:
                solar_in=str(solar_in_val/1000)[:4]
                solar_in_uom="kW[[now"
            else:
                solar_in=solar_usage["solar_in"].split(".")[0]
                solar_in_uom="W[[now"
            display.draw_text(65, 319, solar_in,font, color565(192, 255, 255), landscape=True) # solar_in value
            display.draw_vline(104,250,69,color565(64, 64, 64)) # solar_in line
            display.draw_text(105, 316, solar_in_uom,font_uom, color565(224, 224, 224), landscape=True) # solar_in uom

            if solar_in_val>1800:
                display.draw_text(32, 292, "1", font_icon, color565(192, 255, 255), landscape=True) # sun
            elif solar_in_val>1000:
                display.draw_text(32, 292, "2", font_icon, color565(64, 192, 192), landscape=True) # partial_cloud
            else:
                display.draw_text(32, 292, "3", font_icon, color565(128, 128, 128), landscape=True) # cloud

            draw_arc(display, 48, 250, 30, 5, solar_in_per,color565(64, 0, 0))


            ########################
            # solar_today - in kWh #
            ########################
            solar_today_max=30.0
            solar_today_per=int(float(solar_usage["solar_today"])/solar_today_max*100)
            solar_today_uom="kWh[[today"
            display.draw_text(180, 319, solar_usage["solar_today"][:4], font, color565(192, 255, 255), landscape=True) # solar_today value
            display.draw_vline(218,250,69,color565(64, 64, 64)) # solar_today line
            display.draw_text(220, 316, solar_today_uom,font_uom, color565(224, 224, 224), landscape=True) # solar_today uom
            display.draw_text(148, 293, "1", font_icon, color565(192, 255, 255), landscape=True) # sun

            draw_arc(display, 165, 250, 30, 5, solar_today_per,color565(64, 0, 0))

            #####################
            # power_used - in W #
            #####################
            power_used_max=15000
            power_used_val=float(solar_usage["power_used"])
            power_used_per=int(power_used_val/power_used_max*100)
            if power_used_val>1000:
                power_used=str(power_used_val/1000)[:4]
                power_used_uom="kW[[now"
            else:
                power_used=solar_usage["power_used"].split(".")[0]
                power_used_uom="W[[now"

            display.draw_text(65, 228, power_used,font, color565(255, 255, 255), landscape=True) # power_used value
            display.draw_vline(104,159,69,color565(64, 64, 64)) # power_used line
            display.draw_text(105, 224, power_used_uom,font_uom, color565(224, 224, 224), landscape=True) # power_used uom
            display.draw_text(32, 206, "5", font_icon, color565(64, 64, 64), landscape=True) # plug

            draw_arc(display, 48, 162, 30, 5, power_used_per,color565(64, 0, 0))

            #########################
            # export_today - in kWh #
            #########################
            export_today_max=25.0
            export_today_per=int(float(solar_usage["export_today"])/export_today_max*100)
            export_today_uom="kWh[[today"

            display.draw_text(180, 210, solar_usage["export_today"][:4],font, color565(192, 255, 192), landscape=True) # export_today value
            display.draw_vline(218,140,69,color565(64, 64, 64)) # export_today line
            display.draw_text(220, 206, export_today_uom,font_uom, color565(224, 224, 224), landscape=True)

            display.draw_text(148, 200, "6", font_icon, color565(64, 192, 64), landscape=True) # up
            display.draw_text(148, 176, "4", font_icon, color565(192, 192, 192), landscape=True) # zap

            draw_arc(display, 165, 140, 33, 5, export_today_per,color565(64, 0, 0))

            ##################
            # grid_in - in W #
            ##################
            grid_in_max=15000
            grid_out_max=5000
            grid_in_val=float(solar_usage["grid_in"])
            grid_in_per=int(abs(grid_in_val)/grid_in_max*100)
            if abs(grid_in_val)>1000:
                grid_in=str(abs(grid_in_val/1000))[:4]
                grid_in_uom="kW[[now"
            else:
                grid_in=str(abs(grid_in_val)).split(".")[0]
                grid_in_uom="W[[now"

            # colours for import / export
            if grid_in_val<0:
                grid_colour=color565(128, 128, 255) # pink
            elif grid_in_val>0:
                grid_colour=color565(128, 255, 128) # green
                # recalibrate for export
                grid_in_per=int(abs(grid_in_val)/grid_out_max*100)
            else:
                grid_colour=color565(255, 255, 255) # grey

            display.draw_text(65, 138, grid_in,font, grid_colour, landscape=True) # grid_in value
            display.draw_vline(104,69,69,color565(64, 64, 64)) # grid_in line
            display.draw_text(105, 132, grid_in_uom,font_uom, color565(224, 224, 224), landscape=True) # grid_in uom

            if grid_in_val<0:
                display.draw_text(32, 130, "7", font_icon, color565(64, 64, 192), landscape=True) # down
                display.draw_text(32, 106, "4", font_icon, color565(192, 192, 192), landscape=True) # zap
            elif grid_in_val>0:
                display.draw_text(32, 130, "6", font_icon, color565(64, 192, 64), landscape=True) # up
                display.draw_text(32, 106, "4", font_icon, color565(192, 192, 192), landscape=True) # zap
            else:
                display.draw_text(32, 116, "4", font_icon, color565(192, 192, 192), landscape=True) # zap

            draw_arc(display, 48, 74, 30, 5, grid_in_per,color565(64, 0, 0))

            ##########################
            # grid_in_today - in kWh #
            ##########################
            grid_in_today_max=40.0
            grid_in_today_per=int(float(solar_usage["grid_in_today"])/grid_in_today_max*100)
            grid_in_today_uom="kWh[[today"

            display.draw_text(180, 100, solar_usage["grid_in_today"][:4],font, color565(64, 64, 255), landscape=True)
            display.draw_vline(218,29,69,color565(64, 64, 64)) # grid_in_today line
            display.draw_text(220, 94, grid_in_today_uom,font_uom, color565(224, 224, 224), landscape=True)

            display.draw_text(148, 86, "7", font_icon, color565(64, 64, 192), landscape=True) # down
            display.draw_text(148, 62, "4", font_icon, color565(192, 192, 192), landscape=True) # zap

            draw_arc(display, 165, 30, 32, 6, grid_in_today_per,color565(64, 0, 0))

            ##################
            # battery - in % #
            ##################
            battery_per_val=float(solar_usage["battery_per"])
            # note: % symbol is actually / in the font bytecode
            display.draw_text(98, 52, f"{solar_usage["battery_per"].split(".")[0]}/",font_num, color565(255, 230, 230), landscape=True)
            display.fill_rectangle(12, 25, 6, 16, color565(255, 192, 192)) # battery top
            display.fill_rectangle(18, 18, 60, 30, color565(255, 192, 192)) # battery outline
            display.fill_rectangle(21, 22, 50-int(battery_per_val/2), 22, color565(0, 0, 0)) # battery drain
            if battery_per_val<solar_usage["prev_battery_int"]: # battery goes down
                display.fill_polygon(3,87,35,8,color565(64, 64, 192),0)
            elif battery_per_val>solar_usage["prev_battery_int"]: # battery goes up
                display.fill_polygon(3,91,33,8,color565(64, 192, 64),180)
            else: # battery stays the same
                display.fill_rectangle(86,24,6,20,color565(192, 192, 192))

            ###################
            # timestamp hh:mm #
            ###################
            # note: @ symbol is actually ; in the font bytecode
            display.draw_text(1, 319, f";{solar_usage["timestamp"].split("T")[1][:5]}", font_num, color565(64, 64, 64), landscape=True) # time
    
    else: # data not valid
            display.fill_rectangle(238, 0, 2, 2, color565(0,192,192)) # done

# Arc drawing nicked from here https://www.scattergood.io/arc-drawing-algorithm/
def draw_arc(display, x, y, r1, r2, per,colour):
    gc.collect()
    if per>=100:
        fraction=1.0
    else:
        fraction=per/100
    start_angle=pi/2
    xs=x # cos(0) = 1
    ys=y+r1 # sin(0) = 0

#    display.draw_line(xs1,ys1,xs2,ys2,colour)

    max_angle=start_angle+(fraction*pi) # end at 270 degrees
    each_angle=start_angle # start at 90 degress
    step=pi/90
    while each_angle<max_angle:

        display.fill_polygon(4,
                            int(xs+(r1*cos(each_angle))),
                            int(ys+(r1*sin(each_angle))),
                            r2,colour,45+int(each_angle/pi*180))
        each_angle+=step

# Coroutine: get the solis data every 45 seconds
async def timer_ha_data(ha_info):
    global solar_usage
    solar_usage["prev_battery_int"] = 0
    solar_usage["prev_timestamp"] = "0"
    while True:
        display.fill_rectangle(238, 0, 2, 2, color565(192, 64, 64)) # checking
        await uasyncio.sleep(1)
        gc.collect()
        solar_dict = get_ha(ha_info)
        if "timestamp" in solar_dict:
            display.fill_rectangle(238, 0, 2, 2, color565(0,0,0)) # done
            solar_usage.update(solar_dict)
            display_data(solar_usage)
            # ready to loop then
            solar_usage["prev_battery_int"] = float(solar_usage["battery_per"])
            solar_usage["prev_timestamp"] = solar_usage["timestamp"]
        else:
            display.fill_rectangle(238, 0, 2, 2, color565(0,0,192)) # failed
            print("No data returned")
            if "resp" in solar_dict:
                solar_usage["resp"] = solar_dict["resp"]
        await uasyncio.sleep(45)


# Coroutine: reset button
async def wait_clear_button():
    btn_count = 0
    bl_count=60
    btn_max = 75
    bl_max=90
    while True:
        if clear_btn.value() == 1:
            btn_count = 0
        if clear_btn.value() == 0:
            print(f"Pressed - count is {str(btn_count)}")
            bl_count=0
            btn_count+=1
        if btn_count >= btn_max:
            sleep(2)
            os.remove(CRED_FILE)
            reset()
        if not(bl_state): # only do this if the backlight is off
            if bl_count<bl_max:
                bl_count+=1
                bl_pin.on()
            else:
                bl_count=bl_max
                bl_pin.off()
        await uasyncio.sleep(0.04)

async def main(ha_info):
    # Main loop
    # Get the ha data
    display.clear()
    gc.collect()
    await uasyncio.sleep(2)
    uasyncio.create_task(timer_ha_data(ha_info))

    while True:
        await wait_clear_button()

def setup():
    ha_info = {}
    # Now separate credentials
    # global CRED_FILE
    # global SOLIS_FILE

    # populate the ha_info dictionary:
    try:
        with open(CRED_FILE, "rb") as f:
            contents = f.read().split(b",")
            if len(contents) == 4:
                (
                    ha_info["wifi_ssid"],
                    ha_info["wifi_password"],
                    ha_info["ha_url"],
                    ha_info["ha_token"],
                ) = contents
    except OSError:
        print("No or invalid credentials file - please do a full reset and start again")
        sys.exit()
    # Define the URL list

    ha_api={"solar_in":"sensor.solis_ac_output_total_power",     # current solar power
        "power_used": "sensor.solis_total_consumption_power", # current consumption
        "grid_in": "sensor.solis_power_grid_total_power",  # current grid power
        "battery_per": "sensor.solis_remaining_battery_capacity",  # % battery remaining
        "export_today":"sensor.solis_daily_on_grid_energy",          # exported today
        "solar_today":"sensor.solis_energy_today",                   # solar today
        "grid_in_today":"sensor.solis_daily_grid_energy_purchased"}    # imported today
    ha_info['ha_api']=ha_api

    # Configure the network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Connecting..", end="")
    wlan.connect(ha_info["wifi_ssid"], ha_info["wifi_password"])
    ip_address, net_mask, default_gateway, dns = wlan.ifconfig()
    wifi_count = 0
    while ip_address == "0.0.0.0" and wifi_count < 30:
        print(".", end="")
        sleep(1)
        ip_address, net_mask, default_gateway, dns = wlan.ifconfig()
        wifi_count += 1

    if ip_address == "0.0.0.0":
        print("No WiFi connection - please check details in credentials.env")
        sys.exit()
    gc.collect()

    # display IP address
    print("\nWifi connected - IP address is: " + ip_address)
    display.draw_text(80, 310, ip_address,font, color565(224, 224, 224), landscape=True)

    sleep(1)
    # clear down all the doings
    del sys.modules["captive_portal"]
    del sys.modules["captive_dns"]
    del sys.modules["captive_http"]
    del sys.modules["credentials"]
    del sys.modules["server"]
    gc.collect()

    return(ha_info,display)

if __name__ == "__main__":
    ha_info,display=setup()

    try:
        # Start event loop and run entry point coroutine
        uasyncio.run(main(ha_info))
    except KeyboardInterrupt:
        pass
