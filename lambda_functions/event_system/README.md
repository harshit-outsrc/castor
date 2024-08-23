# Event System

## Prerequisite for running locally
In order to run the event system, the AWS profile and configs need to be setup. It is important to make sure that the configs are setup to run against `us-west-2` and the AWS_SSO is properly setup.

## How to Install for Deployment
Ensure you have npm installed.
Install the required packages:
 - `cd lambda_functions/event_system`
 - `npm install`

## How to Deploy
From project root run `./lambda_functions/event_system/deploy.sh`

## Debugging issues

If you are getting permission denied from github or on deploy you are haning on `Installing Requirements` make sure your ssh identity is associated to your terminal session. To do figure out if this is the case, do the following:
```
brendanvolheim:~/ $ eval "$(ssh-agent -s)"  #  Ensure your SSH Agent is running
Agent pid 26802
brendanvolheim:~/ $ ssh-add -L  # Check to see if your ssh key is associated with your session
The agent has no identities.
brendanvolheim:~/ $ ssh-add --apple-use-keychain ~/.ssh/id_ed25519  # Since there is no identities detected add my local ssh key
Identity added: /Users/brendanvolheim/.ssh/id_ed25519 (brendan.volheim@calbright.org)
brendanvolheim:~/ $ ssh-add -L  # Verify your key is now assicated
ssh-ed25519 ............ brendan.volheim@calbright.org
```

## Event Documentation
All workflow diagrams can be found on [Lucid Chart here](https://lucid.app/lucidchart/a2562182-5f5b-4eff-ae47-a1520b8a85a7/edit?view_items=t9sZnftH9idH&invitationId=inv_7a2c45fb-7838-4ac6-b43d-705c6f0e3b50). Each tab is a different event type.
 - [csep_completed](event_documentation/csep_completed.md)
 - [veterans_intake_complete](event_documentation/veterans_intake_complete.md)


## Event System Structure
 1.  Each event requires an event type, which is passed in through the SQS body. That event type value must then be mapped to an event class in the EventSystem `_event_type_mapping`. 
 2.  Each event class class requires 2 methods that will be called during invocation:
     1.  A static `build` method which builds all necessary arguments needed for run (i.e. Salesforce, Hubspot)
     2.  A `run` method that will do the work required for the event

