# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

from configobj import ConfigObj
from ConfigParser import RawConfigParser
from celery.signals import setup_logging

from mediagoblin import app, mg_globals
from mediagoblin.init.celery import setup_celery_from_config


OUR_MODULENAME = __name__

_log = logging.getLogger(__name__)


def setup_logging_from_paste_ini(loglevel, **kw):
    if os.path.exists(os.path.abspath('paste_local.ini')):
        logging_conf_file = 'paste_local.ini'
    else:
        logging_conf_file = 'paste.ini'

    if not os.path.exists(logging_conf_file):
        raise IOError('{0} does not exist. Logging can not be set up.'.format(
            logging_conf_file))

    logging_conf = ConfigObj(logging_conf_file)

    config = logging_conf

    # Read raw config to avoid interpolation of formatting parameters
    raw_config = RawConfigParser()
    raw_config.readfp(open(logging_conf_file))

    # Set up formatting
    # Get the format string and circumvent configobj interpolation of the value
    fmt = raw_config.get('formatter_generic', 'format')

    # Create the formatter
    formatter = logging.Formatter(fmt)

    # Check for config values
    if not config.get('loggers') or not config['loggers'].get('keys'):
        print('No loggers found')
        return

    # Iterate all teh loggers.keys values
    for name in config['loggers']['keys'].split(','):
        if not config.get('logger_{0}'.format(name)):
            continue

        log_params = config['logger_{0}'.format(name)]

        qualname = log_params['qualname'] if 'qualname' in log_params else name

        if qualname == 'root':
            qualname = None

        logger = logging.getLogger(qualname)

        level = getattr(logging, log_params['level'])
        logger.setLevel(level)

        for handler in logger.handlers:
            handler.setFormatter(formatter)


setup_logging.connect(setup_logging_from_paste_ini)


def setup_self(check_environ_for_conf=True, module_name=OUR_MODULENAME,
               default_conf_file=None):
    """
    Transform this module into a celery config module by reading the
    mediagoblin config file.  Set the environment variable
    MEDIAGOBLIN_CONFIG to specify where this config file is.

    By default it defaults to 'mediagoblin.ini'.

    Note that if celery_setup_elsewhere is set in your config file,
    this simply won't work.
    """
    if not default_conf_file:
        if os.path.exists(os.path.abspath('mediagoblin_local.ini')):
            default_conf_file = 'mediagoblin_local.ini'
        else:
            default_conf_file = 'mediagoblin.ini'

    if check_environ_for_conf:
        mgoblin_conf_file = os.path.abspath(
            os.environ.get('MEDIAGOBLIN_CONFIG', default_conf_file))
    else:
        mgoblin_conf_file = default_conf_file

    if not os.path.exists(mgoblin_conf_file):
        raise IOError(
            "MEDIAGOBLIN_CONFIG not set or file does not exist")

    # By setting the environment variable here we should ensure that
    # this is the module that gets set up.
    os.environ['CELERY_CONFIG_MODULE'] = module_name
    app.MediaGoblinApp(mgoblin_conf_file, setup_celery=False)

    setup_celery_from_config(
        mg_globals.app_config, mg_globals.global_config,
        settings_module=module_name,
        set_environ=False)


if os.environ['CELERY_CONFIG_MODULE'] == OUR_MODULENAME:
    setup_self()
