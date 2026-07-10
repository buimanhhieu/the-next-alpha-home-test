# How to Set Up Dynamic Data Mapping with OptiSync
**Source:** https://support.optisigns.com/hc/en-us/articles/29217646663187-How-to-Set-Up-Dynamic-Data-Mapping-with-OptiSync

### In today's fast-paced digital environment, manually updating digital displays can be both tedious and error-prone. This guide will show you how to integrate live data into your digital screens, allowing for seamless automatic updates across your displays.
**In this article:**

 
- [What is OptiSync?](#What) 
- [Adding Your Data Source](#Adding) 
- [Inputting Your Data Source in Designer](#Inputting) 
-  [Editing and Designing Your Repeater in Designer](#Editing) 
  - [How to use the Property Mapping Feature](#Property) 
  - [How to use Display Format Options](#Display) 
  
- [Push to Screens](#Push) 

---

## What is OptiSync?
OptiSync is an integrated solution designed to seamlessly connect with various data sources, including spreadsheets, APIs, and tables.

**Key Features:**

 
-  **Easy Setup:** Setting up your data source requires low code or no code, ensuring a quick and straightforward process. 
-  **Automatic Updates:** You can link your data source directly to our Designer app, which will automatically update your content. 
-  **Real-Time Data:** This ensures your digital display always reflects the latest data, eliminating the need for manual entry, reducing errors, and saving time. 
**Use Cases:**

OptiSync is ideal for a wide range of use cases, such as:

 
- Displaying employee birthdays 
- Restaurant menus 
- Work anniversaries 
- Product catalogs 
- Team introductions 
- And, many more! 
With OptiSync, your digital displays remain accurate and up-to-date, enhancing communication and engagement in various settings.

---

## Adding Your Data Source
You can add your data source through **Account Settings** or through **Designer app**.

**Account Settings**

 
- Click on your account name in the top right corner 
- Select **More**  
- Select **DataSources**  
- Select **Add DataSource**  
- Choose your data source from the list of options and follow the instructions on how to import it
  - *If you fully open your account settings, it will be under "Advanced" in the column on the left*
  
**Designer App: **

 
- Open the Designer App 
- Select **DataSources** from the column on the left 
- Select **Add DataSource**  
- Choose your data source from the list of options and follow the instructions on how to import it 
   You can add any data source, such as an Excel sheet, Google Sheet, POS system, inventory management system, HRIS, or other systems. You can also create a table directly in OptiSigns.       **Please follow these guides to upload different kinds of DataSources:**

 
- [How to add Google Sheets as a DataSource for OptiSync](https://support.optisigns.com/hc/en-us/articles/29838866920211) 
- [How to add a Microsoft 365 Excel Spreadsheet as a DataSource for OptiSync](https://support.optisigns.com/hc/en-us/articles/29863080711059) 
In addition, you can integrate and test API requests, and execute any necessary pre- or post-request coding.

Once your data source is set up, you can see **Where Used, Edit** the data source, and/or **Duplicate** it.

 
-  **Where Used: **This will show you which of your designs are using this Data Source. This is useful to track the use of this data source across different assets. 
-  **Edit Data: **Go into your data source and make any updates/changes. 
-  **Duplicate: **This will create a copy of your data source. 

## Inputting Your Data Source in Designer
Once your Data Source is set up, you can connect it to the Designer app.

Go to **DataSource** on the left side of the Side Menu.

As previously mentioned, you can add your DataSource here. Or, if you have already created it in the Data Source section of **Advanced**, then it should show up under **Other DataSources**.

**Select** your data source.

**Drag and drop** the data source elements onto the Designer canvas. 

- You can either drag and drop an entire Row or the individual aspects within the rows. 
A pop-up message will appear, asking "**Would you like to use this data in a Repeater or on its Own?**"

 
- **Use on its own:** It will be an element on its own and will update automatically based on the data source.

 
-  **Use in a Repeater:** This will include the data source element in a Repeater component.
  -  **Repeater** is a tool that can be used on the Designer application to display and repeat a list of items dynamically.
  
 

When you choose to use the data as a Repeater, you're presented with additional options: