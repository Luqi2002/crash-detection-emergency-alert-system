import time #NI REAL PUNYA
import board
import busio
import digitalio
import pyRTOS
import wifi
import socketpool
import ssl
import adafruit_requests
import microcontroller

from helmet_system import MPUCrashDetector, TelegramBot, LightMonitor, BuzzerAlert, helmet_state, HelmetGPS

# ───── WiFi Connect ─────
print("🌐 Connecting to WiFi...")
wifi.radio.connect("Redmi Note 10", "lhna1234")  # Ganti dengan SSID & password sebenar
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
print("✅ Connected to WiFi:", wifi.radio.ipv4_address)

# ───── I2C for MPU6050 ─────
i2c = busio.I2C(scl=board.GP3, sda=board.GP2)

# ───── GPIO Setup ─────
yellow_led = digitalio.DigitalInOut(board.GP19)
yellow_led.direction = digitalio.Direction.OUTPUT
buzzer = BuzzerAlert(pin=board.GP18)

# ───── Limit Switch Setup ─────
limit_switch = digitalio.DigitalInOut(board.GP14)
limit_switch.direction = digitalio.Direction.INPUT
limit_switch.pull = digitalio.Pull.UP  # Active LOW

# ───── GPS via UART ─────
uart_gps = busio.UART(board.GP4, board.GP5, baudrate=9600, timeout=10)
gps_module = HelmetGPS(uart_gps)

# ───── Telegram Setup ─────
bot = TelegramBot("Redmi Note 10", "lhna1234", "7389065044:AAGhuABAEoXIslYOzsxQOTZ-6e9tZK2hPZA")
bot.requests = requests
bot.send_message("🟢 Helmet System Booted. Awaiting /start.")

# ───── Sensors ─────
crash_detector = MPUCrashDetector(i2c)
light_sensor = LightMonitor(ldr_pin=board.GP26, led_pin=board.GP0)

# ───── Limit Switch Logic with Auto-Reboot ─────
last_switch_state = None  # To track state changes

def is_system_enabled():
    global last_switch_state
    switch_state = not limit_switch.value  # Active LOW: pressed = True

    if last_switch_state is None:
        last_switch_state = switch_state

    if not switch_state:
        if last_switch_state:
            print("⛔ Limit switch released. System paused.")
            bot.send_message("🛑 Helmet system deactivated. Limit switch released.")
        last_switch_state = switch_state
        return False

    # Bila ditekan semula, sistem terus sambung
    if switch_state and not last_switch_state:
        print("✅ Limit switch pressed again. System resumed.")
        bot.send_message("✅ Helmet system resumed.")

        # 🧠 Reset crash flags so system can detect crash semula
        helmet_state["crash"] = False
        helmet_state["pending_crash"] = False

    last_switch_state = switch_state
    return helmet_state.get("started", False) and switch_state

    # Bila ditekan semula, sistem terus sambung tanpa reboot
    if switch_state and not last_switch_state:
        print("✅ Limit switch pressed again. System resumed.")
        bot.send_message("✅ Helmet system resumed.")

    last_switch_state = switch_state
    return helmet_state.get("started", False) and switch_state
# ───── RTOS Tasks ─────
def telegram_task(self):
    yield
    while True:
        cmd = bot.get_updates() 
        if cmd == "/start" and not helmet_state["started"]:
            helmet_state["started"] = True
            bot.send_message("🤖 Helmet Safety System Activated")
        yield [pyRTOS.timeout(1.0)]

def crash_task(self):
    yield
    blink_interval = 0.5  # seconds
    last_blink_time = time.monotonic()
    led_state = False
    buzzer_state = False

    while True:
        if is_system_enabled():
            crash, acc, gyro = crash_detector.check_crash()
            print("📈 Accel:", acc)
            print("🌀 Gyro:", gyro)

            if crash and not helmet_state["crash"]:
                helmet_state["crash"] = True
                loc = helmet_state.get("gps")

                if loc:
                    msg = f"🚨 Crash Detected\n📍 Location: {loc['Latitude']:.6f}, {loc['Longitude']:.6f}"
                    bot.send_message(msg)
                else:
                    bot.send_message("🚨 Crash Detected. GPS acquiring...")
                    helmet_state["pending_crash"] = True

            elif not crash:
                helmet_state["crash"] = False
                helmet_state["pending_crash"] = False
                yellow_led.value = False
                buzzer.off()
                led_state = False
                buzzer_state = False

            # Blinking during crash
            if helmet_state["crash"]:
                now = time.monotonic()
                if now - last_blink_time >= blink_interval:
                    led_state = not led_state
                    buzzer_state = not buzzer_state

                    yellow_led.value = led_state

                    if buzzer_state:
                        buzzer.on()
                    else:
                        buzzer.off()

                    last_blink_time = now

        else:
            yellow_led.value = False
            buzzer.off()

        yield [pyRTOS.timeout(0.1)]

def gps_task(self):
    yield
    last_update = time.monotonic()
    while True:
        gps_module.update()
        now = time.monotonic()
        if now - last_update >= 1.0:
            last_update = now
            if gps_module.has_fix():
                loc = gps_module.get_location()
                helmet_state["gps"] = loc
                print(f"📍 GPS Fix: {loc['Latitude']:.6f}, {loc['Longitude']:.6f}")
                if helmet_state.get("pending_crash"):
                    bot.send_message(f"🚨 Crash Location Update:\n📍 {loc['Latitude']:.6f}, {loc['Longitude']:.6f}")
                    helmet_state["pending_crash"] = False
            else:
                print("❌ GPS: No fix")
        yield [pyRTOS.timeout(1.0)]

def light_task(self):
    yield
    while True:
        if is_system_enabled():
            lux = light_sensor.check_light()
            helmet_state["lux"] = lux
        yield [pyRTOS.timeout(3.0)]

# ───── Start RTOS ─────
pyRTOS.add_task(pyRTOS.Task(telegram_task, name="Telegram", priority=1))
pyRTOS.add_task(pyRTOS.Task(crash_task, name="Crash", priority=2))
pyRTOS.add_task(pyRTOS.Task(light_task, name="Light", priority=3))
pyRTOS.add_task(pyRTOS.Task(gps_task, name="GPS", priority=4))

pyRTOS.start()
