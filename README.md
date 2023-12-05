
# CFI Self Service Portal

## Project Description

This project is a web-based self service portal for CFI users.

## Getting Started

1. Make a fork the [cfi-self-service](https://github.com/UKHomeOffice/cfi-self-service) repository
2. Clone the forked repository
3. Move into the cfi-self-service-portal project directory by using the command `cd cfi-self-service-portal`
4. Please make sure that the all required dependencies are installed:
   1. **Note:** You will need to check that PIP package manager is installed beforehand by using the command - `python -m pip install --upgrade pip`
   2. All of the dependencies required for this app are bundled within the `requirements.txt` file - these can be installed by using the command - `pip install -r requirements.txt`
5. Create a new virtual environment by using the command `python -m venv env`
6. Install the project by using the command `pip install -e .`
7. Run the project's tests by using the command `pytest`
8. To run the project, use the command `pserve` followed with the config of your choice (i.e. `development.ini`).
