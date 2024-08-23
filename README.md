# castor
Calbright Automation Systems Toolkit for Operations and Reporting (CASTOR)

Included are Calbright Scripts and Lambda Functions for processing business logic.

The name "Castor" comes from the star of the same name in the Gemini constellation, which 
also happens to be one of the brightest stars in the night sky. 

# Requirements

1. Python3 (dependencies located in setup.py)
2. Docker (Install, dockerfiles exist in respective folders)
3. AWS CLI (Install and Config)
4. Environment Variables (`.env`, will need to exist for scripts to use)

## Project Structure
```
.
├── jobs                      # Business Batch Scripts that run with Docker
├── lambda                    # Lambda Functions for our Automations and Backend
├── tests                     # All unit testing code (if needed)
└── tools                     # All tools used for testing/linting/deployment
```

## Development

QuickStart:

Need to install the virtualenv library and then launch it.
```
$ pip install virtualenv
$ virtualenv -p python3 env
```

Proceed to run the script and perform the setup.

MAC OS:
```
$ source env/bin/activate
$ pip install -e .
```

Windows OS:
```
$ .\env\Scripts\activate
$ pip install -e .
```
