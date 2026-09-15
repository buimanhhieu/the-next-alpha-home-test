# OptiSigns IoT Sensor Add-on - Quick Start
**Source:** https://support.optisigns.com/hc/en-us/articles/13097501958291-OptiSigns-IoT-Sensor-Add-on-Quick-Start

### How to quickly get your IoT sensors up and running on any screens you wish.
In this article:

 
- [Set Up Serial Communication Channel](#Serial) 
- [Set Up IoT Sensor via Lift and Learn](#Lift) 
-  [Assign the IoT Sensor to a Screen](#assign) 
  - [Option 1: Through Lift and Learn](#1) 
  - [Option 2: Through Edit Screen Menu](#2) 
  
- [Advanced Settings](#Advanced) 

---
The OptiSigns IoT Sensor Add-on allows you to use any IoT sensors that work with serial communication to interact with your screens. You'll be able to:

 
1. Detect and monitor sensor data about the surroundings, such as motion, temperature and humidity, object liftup/placedown.  
2. Responsively display different content based on the sensor event that was received by the player connected to the screen. 
3. Send command to other IoT devices to control its behavior, e.g. turn on the atmosphere light, turn on/off the screen monitor. 
Our YouTube video shows how it supports the lift and learn use cases using a Nexmosphere brand sensor.

*This feature supports Windows, Linux , MacOS, BrightSigns Player, and our pre-configured Android Stick.*

---
****
## Quick Start Guide for OptiSigns IoT Sensor Add-on
For the following example, we will use a temperature sensor with an **Arduino** board to demonstrate how it works. ***Your board may have slightly different connection options - we will note instances where this may be the case.***

**EDITOR’S NOTE — PRIVACY: the first screenshot (repeated as the last image) shows a real person photo, full name and social handle, readable at full size. Recommend replacing or blurring it. It is also the same image twice, opening and closing the article. (delete before publishing)**

The temperature sensor will send data in its own format to the OptiSigns player through serial communication. The temperature data can be displayed on the screen in realtime, and when the defined condition met, the screen content will change to show overheat status. 

Setting up the IoT sensor add-on will take three steps:

 
1. Set up the serial communication channel. 
2. Set up IoT sensor via Lift and Learn 
3. Activate the IoT sensor on the screen and assign the IoT sensor addon app to it. 
From there you can modify the set up to fit your need.

---

****
## 1. Set Up Serial Communication Channel
In the top right corner, click on the account name.

Then, click **Personal Profile → **Look to the left hand column.

See **"Advanced" →** **"External Communications"**.

 

*You can also go the the page using this link: *******[https://app.optisigns.com/app/s/external-coms](https://app.optisigns.com/app/s/external-coms)

 

Click **"Add New"** in the **Connections** tab to bring up the **Add Connection** page, where you can define the parameters for the serial communication.

We are only going to cover three main settings off this screen: **Name, COM Port, **and **Baud Rate.**

 
-  **Name: **A quick name for your sensor. Enter whatever you'd like. 
-  **COM port: **Designates which serial port the serial communication channel will enter from.
Please note, different systems will organize the serial port differently. 
  -  **Windows:** Normally represented as "COM#". This will depend on the port you've plugged the sensor into. 
  -  **Linux: **Normally represented as something like "/dev/ttyUSB0" or "/dev/ttyACM0". 
  -  **Brightsigns: **Normally represented as "1" or "2" 
  -  **OptiSigns Preconfigured Android Sticks: **Usually is "USB0"