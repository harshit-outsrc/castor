from setuptools import setup, find_packages

# These are the project dependencies which are necessary for development and unit tests. When actually working on a
# specific project please install the requirements specific to that project (usually a requirements.txt within the
# project directory).

dependencies = [
    "asyncio>=3.4.3",
    "propus @ git+ssh://git@github.com/calbright-college/propus.git@b556e6c6b4e75edc1b4690e97c09abe92d5bb359",
    "oracledb>=1.3.0",
    "fpdf>=1.7.0",
    "ssm-cache>=2.10",
    "aiohttp>=3.8.0",
    "salesforce-api>=0.1.40",
    "pandas>=2.0.0",
    "python-dotenv>=1.0.0",
    "paramiko>=3.2.0",
    # Test Dependencies
    "coverage>=4.5.1",
    "flake8>=6.0.0",
    "mock-alchemy>=0.2.0",
    "dictdiffer<=1.0.0",
]

setup(
    name="calbright-castor",
    version="0.0.1",
    description="Calbright CASTOR Repository for scripts",
    author="Calbright",
    packages=find_packages(),
    install_requires=dependencies,
    python_requires=">=3.9",
)
