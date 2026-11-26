# How to Create Custom News Feeds with OptiSync
**Source:** https://support.optisigns.com/hc/en-us/articles/35337746613139-How-to-Create-Custom-News-Feeds-with-OptiSync

### In this article, we will cover OptiSigns’ ability to create custom news apps using the OptiSync feature.
 
- [SharePoint News Examples](#Examples) 
-  [How to Set Up a Custom News Feed](#Setup) 
  -  [Step 1: Setting Up an API Gateway (SharePoint Example)](#Gateway) 
    - [Obtaining a Site-Specific SharePoint SiteID Value](#SiteID) 
    - [Retrieving Proper Authentication Tokens from Microsoft and Making the Call](#Authentication) 
  
  - [Step 2: Mapping the API to a DataSource](#DataSource) 
  -  [Step 3: Creating a News Feed Using Designer](#Designer)
    - [Element Mapping](#Element)
  
  - [Applying Filters to Customize Which News Stories to Display](#Filters) 
  
It is common for companies to share their internal communications, including memos, news, announcements and more via intranet. Digital signage will heighten employee awareness of published company news and announcements.

Using OptiSync, it’s possible to create a custom news app to display company news stored on your company’s intranet. This is achieved by connecting an intranet API with OptiSync and choosing what data to display in the [OptiSigns Designer app](https://support.optisigns.com/hc/en-us/articles/4404151402899-How-to-use-OptiSigns-Template-Designer-app-to-make-your-Digital-Signs-in-minutes).

Creating news feeds with OptiSync has a key advantage: you have full control of the look and feel of your feed. You can create feeds that match your company branding and design guidelines no matter which news source you use. We will be using SharePoint here as an example, but you can use anything that can be input as a Datasource.

Before we get started, it will be helpful to familiarize yourself with a few other concepts which will be important to understand that we cover in other articles:

 
- [How to Integrate API and Publish API Data via OptiSync](https://support.optisigns.com/hc/en-us/articles/22875592994195-How-to-Integrate-API-and-Publish-API-Data-via-OptiSync) 
- [How to Set Up Dynamic Data Mapping via OptiSync](https://support.optisigns.com/hc/en-us/articles/29217646663187-How-to-Set-Up-Dynamic-Data-Mapping-with-OptiSync) 
The API article in particular will provide detailed instructions for how to pair an API and get its data on screen with automatic updates. Once you’ve got your API set up and its data saved as a data source, you can create some of the examples below using the Designer app.

The main example tackled in this article will be company news, but this feature can be used for far more, including:

 
- Custom RSS feeds 
- Custom XML/JSON feeds 
- Inventory management systems 
- Point-of-sales updates across multiple locations 
- Additional internal communications 
- Other news sites 

---

## SharePoint News Examples
Below are some examples using SharePoint. There are numerous possibilities of how to design and create engaging news feeds using SharePoint news or other intranet applications.

Here are a few examples:

#### Bulletin Feed

This style allows several news stories to be shown at once. The images and text are taken directly from the data source and displayed using OptiSync. These are set to periodically update every 30 minutes.

#### Single Story Feed

This style allows a single story to be featured. Using Repeater settings, this will allow a rotating slate of featured news articles.

---

## How to Set Up a Custom News Feed
In order to set up a custom news feed, you'll need to follow these steps:

 
1. Set Up the Custom API Gateway 
2. Map the API to a DataSource within OptiSigns 
3. Create a News Feed Using OptiSigns Designer 

### Step 1: Setting Up a Custom API Gateway (SharePoint Example)
We cover most of the details of this step in our [How to Integrate API and Publish API Data via OptiSync](https://support.optisigns.com/hc/en-us/articles/22875592994195-How-to-Integrate-API-and-Publish-API-Data-via-OptiSync) guide. Please see that guide for a step-by-step process.

However, there are a few elements which are specific to connecting to a SharePoint API (or a variety of resources in Microsoft 365), which we will cover here.

Setting up this API gateway will consist of two parts:

 
- Configuring a Pre-request call to obtain an Authentication token 
- Using that Authentication token in a "main call" to obtain your SharePoint data. 

#### Obtaining a Site-Specific SharePoint SiteID Value
The first step in this process is obtaining the SiteID value for your SharePoint site. This is necessary to obtain the proper URL to make the API request.

To do this, download ****[Postman](https://www.postman.com/)** **or another API platform. Then, send a GET request to the following URL:

```
https://graph.microsoft.com/v1.0/sites/[YOUR-SHAREPOINT-SITE-URL]
```

The [YOUR-SHAREPOINT-SITE-URL] will be specific to your SharePoint site.

When configured correctly, this API request should return a string of JSON similar to the below:

As you can see, under the "id" section there are two values. You want the string after the URL. That is your **SiteID **value. This will be critical for setting up your API gateway in the next step.

#### Retrieving Proper Authentication Tokens from Microsoft
Authentication for SharePoint can be carried out using different methods, but OAuth 2.0 has become the recommended standard. To get started using OAuth 2.0, you’ll need to [register your application in Azure Active Directory](https://learn.microsoft.com/en-us/azure/healthcare-apis/register-application).

Once that's done, you'll need:

 
- ****[Client ID](https://learn.microsoft.com/en-us/azure/healthcare-apis/register-application#application-id-client-id) 
- ****[Client Secret Value](https://learn.microsoft.com/en-us/azure/healthcare-apis/register-application#certificates--secrets) 
- The **SiteID **from the previous step 
These are required for authentication. Any further authentication can be done in the Pre-Request stage to obtain access tokens. These authentication tokens will need to be kept refreshed: see [Microsoft's article on identity platform certificate credentials](https://learn.microsoft.com/en-us/entra/identity-platform/certificate-credentials) for more information.

With these pieces of information, we can get started. Create a new DataSource Request (see our article on [How to Integrate API and Publish API Data via OptiSync](https://support.optisigns.com/hc/en-us/articles/22875592994195-How-to-Integrate-API-and-Publish-API-Data-via-OptiSync) on how to do this). Set up a **GET **request with the following URL. 

```
https://graph.microsoft.com/v1.0/sites/[YOUR-SITEID-VALUE]/pages/microsoft.graph.sitePage?$filter=promotionKind eq 'newsPost'
```

Input your SiteID value where relevant. Next, we'll set up the headers.

****
##### Headers Configuration
For the request headers, use these:

The "Bearer" field can be left blank, as this value will be obtained in the Pre-Request stage.

****
##### Pre-Request Configuration
The Pre-Request stage is where we will obtain the Authorization token for the request. It will need to be set up in a very specific manner. Input the below code in the Pre-Request field:

```
const body = {
  "grant_type": "client_credentials",
  "client_id": "[YOUR-CLIENT-ID]",
  "client_secret": [YOUR-SECRET-VALUE],
  "scope":"https://graph.microsoft.com/.default"
};

const urlEncodedBody = Object.keys(body || {}).map((key) => {
                return key + '=' + body[key];
            }).join('&');

const {data, headers} = await os.postRequest("https://login.microsoftonline.com/[YOUR-CLIENT-ID]/oauth2/v2.0/token", urlEncodedBody,{headers: {'content-type': 'application/x-www-form-urlencoded'}});

const token = 'Bearer ' + data.access_token;
os.context.set("request.headers.authorization", token);

```

Replace the areas marked [YOUR-CLIENT-ID] and [YOUR-SECRET-VALUE] with your Client ID and Secret Value, respectively.

****
##### Final Request and Testing
With these configured, your request should look like this: