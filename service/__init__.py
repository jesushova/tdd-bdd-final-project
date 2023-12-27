######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Package: service

Package for the application models and service routes
This module creates and configures the Flask app and sets up the logging
and SQL database
"""
import sys
from flask import Flask
from service import config
from service.common import log_handlers
from unittest import TestCase
from unittest.mock import patch, MagicMock

# Create the Flask app
app = Flask(__name__)  # pylint: disable=invalid-name

# Load Configurations
app.config.from_object(config)

# Set up logging for production
log_handlers.init_logging(app, "gunicorn.error")

# Initialize the app logger
app.logger.info(70 * "*")
app.logger.info("  P E T   S E R V I C E   R U N N I N G  ".center(70, "*"))
app.logger.info(70 * "*")

# Initialize the models
try:
    from service.models import init_db
    init_db(app)
except Exception as error:  # pylint: disable=broad-except
    app.logger.critical("%s: Cannot continue", error)
    # gunicorn requires exit code 4 to stop spawning workers when they die
    sys.exit(4)

app.logger.info("Service initialized!")

# Import routes and other modules that require the app to be created first
# These imports are placed here to avoid circular dependency issues
from service import routes  # noqa: F401, E402
from service.common import error_handlers, cli_commands  # noqa: F401, E402

class TestAppInitialization(TestCase):
    
    @patch('service.models.init_db')
    def test_app_initialization_success(self, mock_init_db):
        """ Test app initialization with successful DB connection """
        mock_init_db.return_value = None  # Simulate successful DB init
        with self.assertLogs(app.logger, level='INFO') as log:
            # Re-import app to trigger initialization
            import service
            self.assertIn("Service initialized!", log.output)

    @patch('service.models.init_db')
    @patch('sys.exit')
    def test_app_initialization_db_failure(self, mock_sys_exit, mock_init_db):
        """ Test app initialization with DB connection failure """
        mock_init_db.side_effect = Exception("DB connection failed")
        with self.assertLogs(app.logger, level='CRITICAL') as log:
            # Re-import app to trigger initialization with error
            import service
            self.assertIn("Cannot continue", log.output)
        mock_sys_exit.assert_called_with(4)

    def test_app_logging_configuration(self):
        """ Test if the logging is configured properly """
        with self.assertLogs(app.logger, level='INFO') as log:
            import service
            self.assertIn("PET SERVICE RUNNING", log.output)
