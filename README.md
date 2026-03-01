![Embedded](https://img.shields.io/badge/Subject-Embedded%20System-blue)
![University](https://img.shields.io/badge/University-UniMAP-red)
![Language](https://img.shields.io/badge/Language-CircuitPython-green)

## ⚠️ IMPORTANT NOTICE

> 🚨 This system involves hardware integration.  
> Please read this documentation carefully before powering the device.

---

# 🏍 Crash Detection & Emergency Alert System for Riders

## 📌 Academic Background

This project was developed as a Mini Project for the Embedded Systems course during my engineering studies at Universiti Malaysia Perlis (UniMAP).

The objective of this project was to apply embedded system concepts learned in class into a real-world safety application. The system integrates sensor data processing, microcontroller programming, and wireless communication to create an automated crash detection and emergency alert mechanism for motorcycle riders.

---

## 📌 Project Overview

The system is built using Raspberry Pi Pico W and MPU6050 accelerometer sensor. It continuously monitors acceleration data and detects abnormal impact forces that may indicate a crash event.

Once the crash threshold is exceeded:
- An emergency alert is sent via Telegram Bot
- A buzzer is activated
- The system continues monitoring in real time

This project demonstrates the practical application of embedded programming, sensor interfacing, and IoT communication within an academic environment.
---

## 🎯 Project Objectives

- Develop a real-time crash detection mechanism using accelerometer data
- Implement safety interlock using helmet limit switch
- Integrate wireless communication for emergency notification
- Apply multitasking concepts using embedded programming
- Enhance rider safety through automated alert system

---

## ⚙️ Hardware Components

- Raspberry Pi Pico W (Microcontroller with WiFi)
- MPU6050 (3-axis Accelerometer & Gyroscope)
- Limit Switch (Helmet buckle detection)
- Buzzer
- LDR (Light sensor for environment monitoring)
- Power supply module

---

## 🧠 Engineering Concepts Applied

This project allowed the application of multiple embedded engineering principles:

### 1️⃣ Sensor Data Acquisition
- Interfacing MPU6050 via I2C protocol
- Real-time acceleration reading
- Data processing for crash detection threshold

### 2️⃣ Embedded Programming
- Structured Python-based firmware development
- Modular code design
- Sensor abstraction and system control logic

### 3️⃣ Real-Time System Behavior
- Continuous monitoring loop
- Threshold-based event triggering
- Immediate interrupt-like response to abnormal acceleration

### 4️⃣ IoT Communication
- WiFi connectivity using Pico W
- Integration with Telegram Bot API
- Cloud-based emergency alert transmission

### 5️⃣ Safety System Design
- Fail-safe mechanism using helmet limit switch
- Audible alert via buzzer
- Controlled system activation

---

## 🚀 System Workflow

1. Helmet buckle is fastened (system activated).
2. MPU6050 continuously reads acceleration values.
3. Total acceleration force is calculated.
4. If crash threshold is exceeded:
   - Emergency alert is sent via Telegram.
   - Buzzer is activated.
5. System continues monitoring in real-time.

---

## 🔄 Flowchart

---

## 🧠 System Architecture

![Block Diagram]

---

## 📸 Prototype

---

## 🎥 Demo Video

---

## 📄 Project Report

Full documentation available here:  
[Download Mini Project Report](MINI PROJECT REPORT (1).pdf)

---

## 🔬 Technical Highlights

- Real-time impact detection algorithm
- Embedded IoT alert system
- Wireless emergency notification
- Practical application of I2C communication
- Sensor calibration and threshold tuning
- Safety-driven embedded system design

---

## 📚 Learning Outcomes

Through this project, the following skills were developed:

- Embedded hardware interfacing
- Microcontroller programming
- Sensor data processing
- IoT-based alert system development
- Debugging hardware-software integration
- System-level problem solving
- Real-world safety system implementation

---

## 🏁 Future Improvements

- GPS integration for live location tracking
- GSM fallback communication
- Mobile application interface
- Battery optimization for long-term deployment
- Data logging for crash analysis

---

## 👨‍💻 Author

Developed by: - Muhammad Luqman Hakim (@Luqi2002)
              - Muhammad Iqbal(@ )
Embedded Systems Mini Project  
Engineering Student

---
