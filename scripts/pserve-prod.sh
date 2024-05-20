
# Reset our environment variable for a new virtual environment:
export VENV=~/env/cfi-self-service/

# Change directory into your project:
cd ..

# Create a new virtual environment:
python3 -m venv $VENV

# Wire your shell to use the virtual environment:
. $VENV/bin/activate

# Install packages as required via requirements.txt:
$VENV/bin/pip install -r requirements.txt

# Installing your newly created project for development:
$VENV/bin/pip install -e .

# Start the application:
$VENV/bin/pserve production.ini
