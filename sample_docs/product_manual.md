# Northstar Beacon NSB-100 - Quick Product Manual

> The Northstar Beacon NSB-100 is a fictional device created for demonstration purposes.

## Product overview

The Beacon NSB-100 is a small support gateway that connects a customer site to the Northstar Support Portal. The package contains the gateway, a power adapter, an Ethernet cable, and a mounting plate.

## Initial setup

1. Connect the WAN port to a network with internet access.
2. Connect the supplied power adapter.
3. Wait for the status LED to pulse blue.
4. Open the Northstar Support Portal and enter the registration code printed on the device label.
5. Wait until the LED becomes solid green before disconnecting the setup computer.

Initial registration normally takes three to five minutes. The gateway requires outbound HTTPS access on TCP port 443. It does not require inbound internet access.

## Status LED

| LED state | Meaning |
| --- | --- |
| Off | No power |
| Pulsing blue | Starting or waiting for registration |
| Solid green | Connected and operating normally |
| Flashing amber | Installing an update or preparing a factory reset |
| Solid amber | Internet connection is unavailable |
| Solid red | Hardware or startup failure |

If the LED remains solid red after a restart, disconnect power for 30 seconds and reconnect it. If the LED is still red, record the device serial number and contact support.

## Restart and factory reset

To perform a normal restart, briefly press the recessed Reset button for less than two seconds. A normal restart preserves network settings and portal registration.

To perform a factory reset:

1. Keep the device connected to power.
2. Press and hold the recessed Reset button for 10 seconds.
3. Release the button when the status LED begins flashing amber.
4. Wait three to five minutes for the device to restart.
5. Register the device again in the Northstar Support Portal.

A factory reset deletes saved network settings and removes the existing portal registration. It does not delete support tickets stored in the portal.

## Warranty

The NSB-100 includes a 24-month limited hardware warranty from the purchase date. The warranty covers manufacturing defects but not liquid damage, unauthorized repairs, misuse, or unsupported power adapters.
