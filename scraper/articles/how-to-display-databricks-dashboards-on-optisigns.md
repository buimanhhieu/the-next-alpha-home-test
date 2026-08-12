# How to Display Databricks Dashboards on OptiSigns
**Source:** https://support.optisigns.com/hc/en-us/articles/53952018650515-How-to-Display-Databricks-Dashboards-on-OptiSigns

### In this article, we'll walk you through setting up Databricks to display on your OptiSigns digital signs.
 
- [What You'll Need](#WhatYouNeed) 
-  [Create a Service Principal Connection](#CreateConnection) 
  - [In Databricks](#InDatabricks) 
  - [In OptiSigns](#InOptiSigns) 
  
-  [Prepare Your Databricks Dashboard](#PrepareDashboard) 
  - [Enable Dashboard Embed](#EnableEmbedding) 
  - [Publish Dashboard](#PublishDashboard) 
  - [Share Dashboard with Service Principal](#ShareDashboard) 
  -  [Grant the Service Principal Access to the Data (Unity Catalog)](#GrantAccessToData)
    - [Granting at the Catalog Level Instead](#CatalogLevel)
  
  
- [Create a Databricks App in OptiSigns](#CreateDatabricksApp) 
- [Deploying a Databricks App](#DeployingDatabricks) 
- [Frequently Asked Questions](#FAQs) 
With the Databricks app, you can display a live **Databricks AI/BI dashboard** on any OptiSigns screen. 

Once set up, the dashboard renders automatically. It does not require a login on the screen, and it refreshes on a schedule you choose.

---

## What You'll Need
 
- An OptiSigns account - ****[Pro Plus Plan or higher](https://www.optisigns.com/pricing)  
- A Databricks workspace (any tier), with Workspace admin access 
- A published AI/BI dashboard 
- An [OptiSigns-enabled device](https://support.optisigns.com/hc/en-us/articles/360021855653-What-hardware-and-devices-are-supported)  
- A screen, [set up and paired with OptiSigns](https://support.optisigns.com/hc/en-us/articles/18823504383891-OptiSigns-Getting-Started-Guide)  
Within Databricks, you'll also need these four values: 

 
- **Workspace URL** 
- **Workspace ID** 
- **Service Principal Client ID** 
- **Service Principal OAuth Secret** 
We will show how to find them in the article below.

---

## Create a Service Principal Connection
A service principal (SP) is what OptiSigns uses to render the dashboard. This securely grants OptiSigns access to your published Dashboards without exposing any endpoints. 

### In Databricks
Create it in Databricks by clicking the workspace menu in the top right, then clicking **Settings:**

Open **Identity and access**, then find **Service principals** and hit **Manage**.