# How to set up SAML 2.0  with OptiSigns and Okta
**Source:** https://support.optisigns.com/hc/en-us/articles/4404590815635-How-to-set-up-SAML-2-0-with-OptiSigns-and-Okta

With Pro Plus and Enterprise plans, you can configure SAML 2.0 with OptiSigns via Okta.

Assuming you already using Okta for identity management. If you have not used Okta, it is the leading identity management platform, you can learn more [here](https://www.okta.com/intro-to-okta/).

 

****
### Set up OptiSigns & Okta:
**First, you need to do some setup in OptiSigns:**

If you don't have a subdomain yet, you can set up one by going to:
[https://app.optisigns.com/app/s/branding-settings](https://app.optisigns.com/app/s/branding-settings)

Fill in the subdomain field and click Activate. After that, you can use this subdomain for "
You can also map your domain like digitalsigns.yourcompany.com by following this [article](https://support.optisigns.com/hc/en-us/articles/1500000480302).

This will be the URL that you can share with your users so they can log in to use the app, once integration has set up. In our example, we will use [https://advanced.optisigns.net/](https://advanced.optisigns.net/)

Next, go to the SAML Single Sign On setting page:

[https://app.optisigns.com/app/s/saml-settings](https://app.optisigns.com/app/s/saml-settings)

Click Enable SAML SSO.

The settings are:

 
- Enable Username & Password login: Allow users to also log in with username/password. It’s recommended to disable it once integration is all done. As Admin/Owner, it's recommended that you keep at least 1 account with a password log in, in case there's issues, you can always log back in from app.optisigns.com to reconfigure.  
- Enable User Creation: If users are authenticated, but do not exist in OptiSigns, they will be created in OptiSigns. You should enable this, because you likely already assign/approve users/groups to use OptiSigns, unless for some reason you want to be very strict and want to review the roles of users before they can start using OptiSigns. 
- Enable User Override: Every time a user logs in, if their group assignment has changed on SAML, OptiSigns will update, and override new profile settings.  
- Note the "Single Sign On URL" and "Audience URI (SP Entity ID) URL", you will need this to use in Okta later. 

 

**Next, add OptiSigns as an App to your Okta account:**

Log in to your Okta account as admin -> Application

Or go to: [https://optisigns-admin.okta.com/admin/apps/active](https://optisigns-admin.okta.com/admin/apps/active)

Click Create App Integration

Select SAML 2.0

Enter App name: OptiSigns

If you want to upload a logo, you can use our logo [here](https://download.optisignsapp.com/marketing/optisigns-logo.png).

Click Next

In "Single sign-in URL" and "Audience URI (SP Entity ID)", these are the URL that you have in [https://app.optisigns.com/app/s/saml-settings](https://app.optisigns.com/app/s/saml-settings)
Check "Use this for Recipient URL and Destination URLs"

Click Next.