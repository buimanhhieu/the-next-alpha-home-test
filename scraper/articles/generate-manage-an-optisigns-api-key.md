# Generate & Manage an OptiSigns API Key
**Source:** https://support.optisigns.com/hc/en-us/articles/4414563797139-Generate-Manage-an-OptiSigns-API-Key

In order to use the API, you will need first get an API key. To get an API key, you can either use the link below, or click the **API Keys** button in the side menu of account management on the OptiSigns portal.

To get an Within OptiSigns, click the profile menu on the top right, go to **More**, then **API Keys**.

Or, click this link: [https://app.optisigns.com/app/s/apikeys](https://app.optisigns.com/app/s/apikeys)

### Create API Key
1. Click the **New API Key** button

2. Enter the API Key name, and select the scopes and permissions for the API key.

3. Save the API key safely, the key will be used to access your account via API. It can be re-displayed at any time from the row's three-dot menu and selecting Reveal.

Click **Copy **to quickly get the key and Paste it where it needs to go.

### Use API Key
To use the API key, put it in the HTTP request header following this format.

Authorization: Bearer YOUR_KEY_HERE

In the OptiSigns GraphQL playground, you will be able to query your data if the API key is successfully added.

**Previous Article - ******[Introduction](https://support.optisigns.com/hc/en-us/articles/4414552808467-Introduction)

**Next Article - ******[Get Started](https://support.optisigns.com/hc/en-us/articles/4414563863827-Get-Started)