# Automated Term Creation

# Table of Contents
- [Automated Term Creation](#automated-term-creation)
- [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Salesforce](#salesforce)
  - [Calbright Database](#calbright-database)
  - [Anthology](#anthology)

<a id="description"></a>
## Description
This job runs once a week and will automatically create any missing terms for the upcoming 8 weeks of terms in Salesforce, Calbright Database,
and Anthology. There are two environments that this job will run on (stage and production).

<a id="salesforce"></a>
## Salesforce
Within salesforce this process will create the end of term objects which can be found [here](https://calbright.lightning.force.com/lightning/o/hed__Term__c/list?filterName=00B3k000008eq4EEAQ). All methods are called from within Propus, no custom code is within Castor. Within the Salesforce object the following fields will be created:
 - Term Name
 - Start Date
 - End Date

<a id="calbright_database"></a>
## Calbright Database
The process will create rows in the term table with the following items:
 - Term Name
 - Start Date
 - End Date
 - Add Drop Date
 - Anthology ID (REQUIRED)

<a id="anthology"></a>
## Anthology
Within Anthology many steps need to be completed, however all methods and actions are called within Propus and all castor is doing is calling a
propus helper to create terms. But all in all the following actions are taken (within propus):
 - Term Creation
 - Create Start Dates for the new Term
 - Create Programs for the new Term
 - Copy class schedule from the most recent term into the new term

