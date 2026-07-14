# How to Use the CAP Alert App
**Source:** https://support.optisigns.com/hc/en-us/articles/6604468198291-How-to-Use-the-CAP-Alert-App

### In this article, we will show you how to set up and test the CAP Alert app in OptiSigns.
 
- [What You'll Need](#WhatYouNeed) 
-  [How to Set Up a CAP Alert App](#Set) 
  - [Theme Settings](#ThemeSettings) 
  - [Advanced Settings](#AdvancedSettings) 
  
- [How to Test Your CAP Alert](#Test) 
Some Emergency Alert Systems or Emergency Mass Notification Systems (like Everbridge, RAVE. and Alertus) can push CAP (Common Alerting Protocol) and Integrated Public Alert and Warning System (IPAWS) messages to the targets including digital signage when there is an emergency. You can integrate with these systems using the CAP Alert app with OptiSigns.

Using OptiSigns' CAP Alert app, you can generate a webhook and integrate it with the Emergency Alert System. When there is an emergency, the emergency alert system will call the webhook to send the CAP/IPAWS message and trigger the CAP alert app. The CAP/IPAWS alert will take over the target screens and display the emergency message. The screen will resume and play the original content when the emergency is over. 

---

## What You'll Need
 
- An OptiSigns account - [Pro Plus Plan or higher](https://www.optisigns.com/pricing)  
- An Emergency Alert Feed 
- An [OptiSigns-enabled device](https://support.optisigns.com/hc/en-us/articles/360021855653-What-hardware-and-devices-are-supported)  
- A screen, [set up and paired with OptiSigns](https://support.optisigns.com/hc/en-us/articles/18823504383891-OptiSigns-Getting-Started-Guide)  

---

## How to Set Up a CAP Alert App
 Go to the OptiSigns portal. Go to **Assets → Add Asset → Apps.**

 

 Select **CAP Alert:**

 

 Now you can set up your Looker Studio app:

 

     
-  **Name** - Name of your assets, this will not be displayed on the screens. 
-  **Content Type** - Choose between **Post to Webhook** or **XML**. 
-  **Enable Authentication** - When checked, will add a **Username **and **Password **section to check Authentication.

 

  
-  **Webhook / XML** - Depending on whether you've selected "Post to Webhook" or "XML" above, here is where the webhook or XML script will be placed. 
-  **Target** - Choose whether this alert will target a specific screen, or tag. 
-  **Screens/Tags** - Select which screens or group of screens (tags) you want to target for this emergency. (i.e. Fire in building/location 1) 
-  **Status** - Swap between Active or Inactive for this alert. 
-  **Emergency Duration** - How long the CAP Alert will take over the screen. Measured in seconds. 
-  **Content-Type** - Select "Post to Webhook" if you would like to post the CAP/IPAWS message to your signage. The app also supports RSS feed. 
-  **Webhook** - The app will generate a webhook URL after it is saved. This is what you should share with the emergency alert system. 
-  **Display Type **- Currently the app will take over the full screen when there is an emergency 
-  **State **- Set the app to active or inactive. 
-  **Emergency Duration **- How long the emergency message will take over the screen. The value can be overwritten by the webhook call. 
 

 
### Theme Settings
 Click **Theme Settings **to expand the field and provide a slate of additional options:

  

  
-  **Background Image:** Lets you choose a Background image for your RSS feed. When **Custom** is selected, it will give you the opportunity to **Choose Photo:**

 

 This photo must already exist as an asset within OptiSigns.

  
-  **Theme:** Choose between **Light **and **Dark** theme. This will disappear if Background Image is set to "Custom". 
-  **Text Color: **Determines the text color. Can be chosen with Hex Code or via color picker. 
-  **Text Font:** Choose the font for the text. 
-  **Font Size: **Choose between Default Font Size, or Custom. When Custom is selected, will provide a new option: **Custom Font Size**.
****
  -  **Custom Font Size: **Choose your font size.
  
-  **Text Alignment/Position:** Choose the alignment and position of the CAP Alert text. 
-  **Max Number of Rows:** Choose the maximum number of rows to dedicate to the CAP Alert feed. 
 

 
### Advanced Settings
 Click **Advanced **to expand the field and provide a slate of additional options:

 

  
-  **Enable Lifecycle Handling** - When checked, it allows handling of CAP message lifecycle events including Update, Cancel, and All Clear messages. It does this by checking the <identifier> field. **This option is only applied when "Post to Webhook" is set as the Content Type**. It also enables the below options: