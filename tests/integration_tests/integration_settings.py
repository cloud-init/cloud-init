import os

##################################################################
# LAUNCH SETTINGS
##################################################################

# Keep instance (mostly for debugging) when test is finished
KEEP_INSTANCE = False

# One of "lxd_container', 'oracle', ... more to come
PLATFORM = 'lxd_container'

# The cloud-specific instance type to run. E.g., a1.medium on AWS
# If the pycloudlib instance provides a default, this can be left None
INSTANCE_TYPE = None

# Determines the base image to use or generate new images from.
# Can be the name of the OS if running a stock image,
# otherwise the id of the image being used if using a custom image
OS_IMAGE = 'focal'

# Populate if you want to use a pre-launched instance instead of
# creating a new one. The exact contents will be platform dependent
EXISTING_INSTANCE_ID = None

##################################################################
# IMAGE GENERATION SETTINGS
##################################################################

# Depending on where we are in the development / test / SRU cycle, we'll want
# different methods of getting the source code to our SUT. Because of
# this there are a number of different ways to initialize
# the target environment.

# Can be any of the following:
# NONE
#   Don't modify the target environment at all. This will run
#   cloud-init with whatever code was baked into the image
# IN_PLACE
#   LXD/VM only. Mount the source code as-is directly into
#   the container to override the pre-existing cloud-init code
# CURRENT
#   Build and install a deb of the code as it currently exists,
#   including uncommitted code
# COMMIT
#   Build and install a deb from a particular commit hash
# PROPOSED
#   Install from the proposed repo
# PPA
#   Install from a PPA
# <file path>
#   A path to a valid package to be uploaded and installed
# <image id>
#   A pre-existing (platform dependent) image id
IMAGE_SOURCE = 'NONE'

##################################################################
# ORACLE SPECIFIC SETTINGS
##################################################################
# Compartment-id found at
# https://console.us-phoenix-1.oraclecloud.com/a/identity/compartments
# Required for Oracle
ORACLE_COMPARTMENT_ID = None

##################################################################
# USER SETTINGS OVERRIDES
##################################################################
# Bring in any user-file defined settings
try:
    from tests.integration_tests.user_settings import *
except:  # noqa
    pass

##################################################################
# ENVIRONMENT SETTINGS OVERRIDES
##################################################################
# Any of the settings in this file can be overridden with an
# environment variable of the same name prepended with CLOUD_INIT_
# E.g., CLOUD_INIT_PLATFORM
# Perhaps a bit too hacky, but it works :)
current_settings = [var for var in locals() if var.isupper()]
for setting in current_settings:
    globals()[setting] = os.getenv(
        'CLOUD_INIT_{}'.format(setting), globals()[setting]
    )
