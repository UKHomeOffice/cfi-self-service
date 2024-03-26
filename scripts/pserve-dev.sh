
# Reset our environment variable for a new virtual environment:
export VENV=~/env/cfi-self-service/

# Change directory into your project:
cd ..

# Create a new virtual environment:
python3 -m venv $VENV

# Wire your shell to use the virtual environment:
. $VENV/bin/activate

# Upgrade packaging tools:
$VENV/bin/pip install --upgrade pip setuptools

# Install pyramid and waitress:
$VENV/bin/pip install pyramid
$VENV/bin/pip install waitress
$VENV/bin/pip install boto3
$VENV/bin/pip install pyramid_jinja2
$VENV/bin/pip install pyramid_tm

# Installing your newly created project for development:
$VENV/bin/pip install -e .

# Start the application:
$VENV/bin/pserve development.ini
