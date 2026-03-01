# ============================================================
# 🪖 HELMET SAFETY SYSTEM - MAIN CONTROLLER
# Platform  : Raspberry Pi Pico W
# Language  : CircuitPython
# Architecture : pyRTOS (Real-Time Task Scheduling)
# Author : Iqbal And Luqman
# ============================================================


# ---------------------- IMPORT LIBRARIES ----------------------
import time                    # For timing functions
import board                   # Pin definitions
import busio                   # I2C & UART communication
import digitalio               # GPIO control
import pyRTOS                  # Real-Time Operating System
import wifi                    # WiFi connectivity
import socketpool              # Network socket pool
import ssl                     # Secure connection
import adafruit_requests       # HTTP requests
import microcontroller         # MCU control (reset etc.)

# Import custom helmet system modules
from helmet_system import (
    MPUCrashDetector,          # Crash detection class (MPU6050)
    TelegramBot,               # Telegram communication
    LightMonitor,              # LDR light monitoring
    BuzzerAlert,               # Buzzer control
    helmet_state,              # Shared global system state dictionary
    HelmetGPS                  # GPS handler
)


# ---------------------- WIFI CONNECTION ----------------------
print("🌐 Connecting to WiFi...")
wifi.radio.connect("ssid", "password")  # Replace with actual SSID & password

# Create secure HTTPS session
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

print("✅ Connected to WiFi:", wifi.radio.ipv4_address)


# ---------------------- I2C SETUP (MPU6050) ----------------------
# I2C communication for accelerometer & gyroscope sensor
i2c = busio.I2C(scl=board.GP3, sda=board.GP2)


# ---------------------- GPIO OUTPUT SETUP ----------------------
# Yellow LED (Crash indicator)
yellow_led = digitalio.DigitalInOut(board.GP19)
yellow_led.direction = digitalio.Direction.OUTPUT

# Buzzer alert system
buzzer = BuzzerAlert(pin=board.GP18)


# ---------------------- LIMIT SWITCH SETUP ----------------------
# Detect whether helmet buckle is locked (safety condition)
limit_switch = digitalio.DigitalInOut(board.GP14)
limit_switch.direction = digitalio.Direction.INPUT
limit_switch.pull = digitalio.Pull.UP   # Active LOW configuration


# ---------------------- GPS SETUP (UART) ----------------------
# UART communication for GPS module
uart_gps = busio.UART(board.GP4, board.GP5, baudrate=9600, timeout=10)
gps_module = HelmetGPS(uart_gps)


# ---------------------- TELEGRAM BOT SETUP ----------------------
bot = TelegramBot("ssid", "password", "telegram token id")
bot.requests = requests
bot.send_message("🟢 Helmet System Booted. Awaiting /start.")


# ---------------------- SENSOR INITIALIZATION ----------------------
crash_detector = MPUCrashDetector(i2c)        # MPU6050 handler
light_sensor = LightMonitor(ldr_pin=board.GP26, led_pin=board.GP0)


# ============================================================
# LIMIT SWITCH SYSTEM CONTROL FUNCTION
# Purpose:
# - Enable system only when helmet is worn
# - Handle pause/resume logic
# - Reset crash flags when resumed
# ============================================================
last_switch_state = None

def is_system_enabled():
    global last_switch_state
    
    # Active LOW → pressed = True
    switch_state = not limit_switch.value  

    if last_switch_state is None:
        last_switch_state = switch_state

    # If helmet removed → pause system
    if not switch_state:
        if last_switch_state:
            print("⛔ Limit switch released. System paused.")
            bot.send_message("🛑 Helmet system deactivated.")
        last_switch_state = switch_state
        return False

    # If helmet worn again → resume system
    if switch_state and not last_switch_state:
        print("✅ Limit switch pressed again. System resumed.")
        bot.send_message("✅ Helmet system resumed.")

        # Reset crash state so detection can run again
        helmet_state["crash"] = False
        helmet_state["pending_crash"] = False

    last_switch_state = switch_state
    return helmet_state.get("started", False) and switch_state


# ============================================================
# RTOS TASK: TELEGRAM COMMAND HANDLER
# Handles:
# - Receiving /start command
# - Activating system remotely
# ============================================================
def telegram_task(self):
    yield
    while True:
        cmd = bot.get_updates()
        
        if cmd == "/start" and not helmet_state["started"]:
            helmet_state["started"] = True
            bot.send_message("🤖 Helmet Safety System Activated")
        
        yield [pyRTOS.timeout(1.0)]


# ============================================================
# RTOS TASK: CRASH DETECTION & ALERT SYSTEM
# Handles:
# - Reading MPU6050 data
# - Detect crash event
# - Trigger Telegram alert
# - Blink LED & buzzer during crash
# ============================================================
def crash_task(self):
    yield

    blink_interval = 0.5
    last_blink_time = time.monotonic()
    led_state = False
    buzzer_state = False

    while True:
        if is_system_enabled():

            # Read acceleration & gyro values
            crash, acc, gyro = crash_detector.check_crash()

            print("📈 Accel:", acc)
            print("🌀 Gyro:", gyro)

            # If crash detected
            if crash and not helmet_state["crash"]:
                helmet_state["crash"] = True

                loc = helmet_state.get("gps")

                # If GPS available → send location
                if loc:
                    msg = f"🚨 Crash Detected\n📍 Location: {loc['Latitude']:.6f}, {loc['Longitude']:.6f}"
                    bot.send_message(msg)
                else:
                    # GPS not ready → wait for fix
                    bot.send_message("🚨 Crash Detected. GPS acquiring...")
                    helmet_state["pending_crash"] = True

            # If no crash → reset alert system
            elif not crash:
                helmet_state["crash"] = False
                helmet_state["pending_crash"] = False
                yellow_led.value = False
                buzzer.off()
                led_state = False
                buzzer_state = False

            # Blink LED + Buzzer when crash active
            if helmet_state["crash"]:
                now = time.monotonic()
                if now - last_blink_time >= blink_interval:
                    led_state = not led_state
                    buzzer_state = not buzzer_state

                    yellow_led.value = led_state
                    buzzer.on() if buzzer_state else buzzer.off()

                    last_blink_time = now

        else:
            # If system disabled → turn off alerts
            yellow_led.value = False
            buzzer.off()

        yield [pyRTOS.timeout(0.1)]


# ============================================================
# RTOS TASK: GPS MONITORING
# Handles:
# - Continuously update GPS data
# - Store latest coordinates
# - Send crash location update if needed
# ============================================================
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

                # If crash happened before GPS fix
                if helmet_state.get("pending_crash"):
                    bot.send_message(
                        f"🚨 Crash Location Update:\n📍 {loc['Latitude']:.6f}, {loc['Longitude']:.6f}"
                    )
                    helmet_state["pending_crash"] = False
            else:
                print("❌ GPS: No fix")

        yield [pyRTOS.timeout(1.0)]


# ============================================================
# RTOS TASK: LIGHT MONITORING
# Handles:
# - Monitor ambient light
# - Store lux value into system state
# ============================================================
def light_task(self):
    yield
    while True:
        if is_system_enabled():
            lux = light_sensor.check_light()
            helmet_state["lux"] = lux
        yield [pyRTOS.timeout(3.0)]


# ============================================================
# START RTOS SCHEDULER
# Tasks are prioritized (lower number = higher priority)
# ============================================================
pyRTOS.add_task(pyRTOS.Task(telegram_task, name="Telegram", priority=1))
pyRTOS.add_task(pyRTOS.Task(crash_task, name="Crash", priority=2))
pyRTOS.add_task(pyRTOS.Task(light_task, name="Light", priority=3))
pyRTOS.add_task(pyRTOS.Task(gps_task, name="GPS", priority=4))

pyRTOS.start()
