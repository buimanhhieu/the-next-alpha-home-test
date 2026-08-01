# How to use the Web Scripting App
**Source:** https://support.optisigns.com/hc/en-us/articles/1500012522362-How-to-use-the-Web-Scripting-App

### Web Scripting is an advanced feature for OptiSigns' Pro Plus subscribers or higher, enabling users to automate website navigation and form entries without any coding. This guide will walk you through recording your script, creating Web Scripting assets in OptiSigns, and using them securely on your screens.
**In this article**

 
- [What is Web Scripting?](#What) 
- [Record Your Script (no 2FA)](#Record) 
- [Record Your Script (2FA Enabled)](#2FA) 
- [Create Web Scripting Asset in OptiSigns](#Create) 
- [Using It on Your Screens](#Using) 
- [Web Scripting Security Features](#SecurityFeatures) 

---

Web Scripting is a feature that allows users to automate navigation and form entry on websites without any coding. This tool records user actions, such as entering usernames and passwords, navigating to specific pages, handling pop-ups, running your own JavaScript and more on a website, and then encrypts the recorded script for secure execution on designated devices.

OptiSigns encrypts all the scripts and your password entered with our own private keys.

- This will ensure your data/password is safe as soon as it left your browsers and only get decrypted at device level before the fields are entered.
We also provide Zero Knowledge encryption method so that you can protect your script with your own Master Password. *You can read more at the end of this article.*

If your dashboard requires login with the 2FA, OptiSigns supports 2FA in the Web Scripting app, as well.

**Let's jump in and get started!**

---
****
## Record Your Script

In this article, we will show you how to use a tool called Burp Suite Navigation Recorder. You can use other tools if that can generate similar scripts that works too. We recommend Burp Suite because it's a reputable tool used by many companies, including the Fortune 500.

**1. You need to install Burp Suite Navigation Recorder.**

Open **Chrome Browser**.

Go to Chrome Web Store: [https://chrome.google.com/webstore/category/extensions](https://chrome.google.com/webstore/category/extensions)

Search for: "**Burp Suite Navigation Recorder**".

Click on it.

Then click **Add to Chrome.**

Burp Suite Navigation Recorder is installed

Click on the **Navigation Recorder Icon.**

Then click **Open Settings** to finish set up.

Scroll down and click **"Allow in Incognito".**

Close this tab.

Now, if you click on the Navigation Recorder icon again, you will have option to Start Recording.

**2. Record your Script**

From the Navigation Recorder extension pop out like in above screenshot, click **Start Recording.**

It will open an **Chrome Incognito window**.
You can put in the URL of the website or page you want to start with.
Then fill out the forms. (such as, entering your username, password and click Login)

 

You can click around, navigate to certain page, position on page etc.

Once you are done, click on the **Navigation Recorder Extension icon** and click **Stop Recording.**

This will close the Incognito window that you are working on.

 

Go back to Chrome, click **Navigation Recorder icon.**
Click "**Copy to Clipboard**". This will copy your script to clipboard.
Now you are ready to put in use in OptiSigns.

---

****
## Record Your Script (2FA Enabled)