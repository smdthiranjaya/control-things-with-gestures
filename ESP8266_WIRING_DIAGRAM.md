# ESP8266 Wiring Diagram for Gesture Control System

## Components Required

- ESP8266 (NodeMCU or similar)
- 3x LEDs (LED1, LED2, LED3)
- 3x 220Ω - 330Ω Resistors (for LEDs)
- 1x Main Motor (optional)
- 1x Finger Motor (for rotation control)
- 1x Hand Motor (for rotation control)
- 1x Bulb/Light (with dimming support)
- Motor driver modules (L298N or similar for motors)
- Breadboard and jumper wires
- External power supply (5V/12V depending on motors)

## Pin Connections

### LEDs (with 220Ω resistors)

```
LED1:
  ESP8266 D1 (GPIO5) → Resistor → LED Anode (+)
  LED Cathode (-) → GND

LED2:
  ESP8266 D2 (GPIO4) → Resistor → LED Anode (+)
  LED Cathode (-) → GND

LED3:
  ESP8266 D3 (GPIO0) → Resistor → LED Anode (+)
  LED Cathode (-) → GND
```

### Motors (using L298N Motor Driver)

```
Main Motor:
  ESP8266 D5 (GPIO14) → L298N IN1
  L298N OUT1 → Motor Terminal 1
  L298N OUT2 → Motor Terminal 2
  L298N 12V → External Power Supply (+)
  L298N GND → ESP8266 GND & Power Supply (-)

Finger Motor (PWM Control):
  ESP8266 D6 (GPIO12) → L298N IN2 (PWM)
  L298N OUT3 → Motor Terminal 1
  L298N OUT4 → Motor Terminal 2

Hand Motor (PWM Control):
  ESP8266 D7 (GPIO13) → L298N IN3 (PWM)
  L298N OUT5 → Motor Terminal 1
  L298N OUT6 → Motor Terminal 2
```

### Bulb/Dimmer (PWM Control)

```
Smart Bulb (with PWM dimming):
  ESP8266 D8 (GPIO15) → MOSFET Gate (IRF540N)
  MOSFET Drain → Bulb (-)
  MOSFET Source → GND
  Bulb (+) → External Power Supply (+)
```

## Visual Diagram

```
                    ESP8266 NodeMCU
                    ┌─────────────┐
                    │   [USB]     │
                    │             │
        LED1 ───────┤ D1 (GPIO5)  │
        LED2 ───────┤ D2 (GPIO4)  │
        LED3 ───────┤ D3 (GPIO0)  │
                    │             │
   Main Motor ──────┤ D5 (GPIO14) │
 Finger Motor ──────┤ D6 (GPIO12) │ (PWM)
   Hand Motor ──────┤ D7 (GPIO13) │ (PWM)
         Bulb ──────┤ D8 (GPIO15) │ (PWM)
                    │             │
          GND ──────┤ GND         │
                    │             │
                    └─────────────┘
```

## Detailed Schematic

```
ESP8266          Resistor        LED1
  D1 ─────────── 220Ω ──────────┤►├──── GND
  D2 ─────────── 220Ω ──────────┤►├──── GND (LED2)
  D3 ─────────── 220Ω ──────────┤►├──── GND (LED3)


ESP8266          Motor Driver (L298N)         Main Motor
  D5 ────────── IN1                OUT1 ─────┐
                IN2                OUT2 ─────┤ Motor
                12V ← External Power          │
                GND ← ESP8266 GND ────────────┘


ESP8266          MOSFET (IRF540N)      Bulb      Power
  D8 ─────────── Gate
                Drain ──────────────── (-)
                Source ─────────────── GND
                                       (+) ──── 12V+
```

## Pin Summary Table

| Device       | ESP8266 Pin | GPIO | Type | Notes            |
| ------------ | ----------- | ---- | ---- | ---------------- |
| LED1         | D1          | 5    | OUT  | Through 220Ω     |
| LED2         | D2          | 4    | OUT  | Through 220Ω     |
| LED3         | D3          | 0    | OUT  | Through 220Ω     |
| Main Motor   | D5          | 14   | OUT  | Via motor driver |
| Finger Motor | D6          | 12   | PWM  | Via motor driver |
| Hand Motor   | D7          | 13   | PWM  | Via motor driver |
| Bulb         | D8          | 15   | PWM  | Via MOSFET       |

## Important Notes

1. **Power Supply**:

   - ESP8266 can be powered via USB (5V)
   - Motors need separate power supply (5V-12V depending on motor specs)
   - **Common GND** between ESP8266 and external power supply

2. **LED Resistors**:

   - Use 220Ω - 330Ω resistors to limit current
   - Prevents LED burnout

3. **Motor Driver**:

   - L298N can handle 2 motors
   - For 3 motors, use 2x L298N or 1x L298N + separate driver
   - Enable pins should be connected to 5V or PWM pins

4. **MOSFET for Bulb**:

   - Use IRF540N or similar N-channel MOSFET
   - Gate resistor (1kΩ) recommended between ESP8266 and Gate
   - Can handle high current loads

5. **WiFi Configuration**:
   - Set WiFi credentials in ESP8266 code
   - Ensure ESP8266 IP matches the Python config (`192.168.1.15`)

## Gesture to Device Mapping

| Gesture             | Device       | Action             |
| ------------------- | ------------ | ------------------ |
| 1 finger up         | LED1         | ON/OFF             |
| 2 fingers up        | LED2         | ON/OFF             |
| 3 fingers up        | LED3         | ON/OFF             |
| 4 fingers up        | Main Motor   | ON/OFF             |
| Finger spread angle | Finger Motor | 0-100% speed (PWM) |
| Wrist rotation      | Hand Motor   | 0-100% speed (PWM) |
| Total fingers (0-5) | Bulb         | 0-100% brightness  |

## Testing Steps

1. **Connect LEDs first** - Test with simple blink sketch
2. **Test each LED individually** - Ensure proper connections
3. **Add motor driver** - Test motors separately
4. **Upload ESP8266 code** - Configure WiFi and pins
5. **Test from Python app** - Check network connectivity
6. **Fine-tune gesture detection** - Adjust sensitivity in settings

## Safety Warnings

⚠️ **IMPORTANT:**

- Never connect motors directly to ESP8266 pins (use motor driver)
- Always use current-limiting resistors with LEDs
- Ensure proper grounding between all components
- Don't exceed ESP8266 pin current limit (12mA per pin)
- Use external power supply for motors/high-power devices
- Double-check polarity before powering on

---

**Next Step**: Upload the ESP8266 Arduino code to control these devices!
