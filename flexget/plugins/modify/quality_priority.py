from __future__ import unicode_literals, division, absolute_import
from builtins import *  # pylint: disable=unused-import, redefined-builtin

import logging

from flexget import plugin
from flexget.event import event
from flexget.utils import qualities

log = logging.getLogger('quality_priority')


class QualityPriority(object):
    """
        Allows modifying quality priorities from default values.

        Example:

        quality_priority:
          webrip: 155  # just above hdtv
    """

    schema = {
        'type': 'object',
        'additionalProperties': {
            'type': 'object',
            'properties': {
                'above': {'type': 'string', 'format': 'quality_requirements'},
                'below': {'type': 'string', 'format': 'quality_requirements'}
            },
            'maxProperties': 1
        }
    }

    def __init__(self):
        self.quality_priorities = {}

    def on_task_start(self, task, config):
        self.quality_priorities = {}
        for quality, _config in config.items():
            action, other_quality = list(_config.items())[0]

            if quality not in qualities._registry:
                raise plugin.PluginError('%s is not a valid quality' % quality)
            if other_quality not in qualities._registry:
                raise plugin.PluginError('%s is not a valid quality' % other_quality)

            quality_component = qualities._registry[quality]
            self.quality_priorities[quality] = quality_component.value
            log.debug('stored %s original value %s' % (quality, quality_component.value))

            new_value = qualities._registry[other_quality].value
            if action == 'above':
                new_value += 1
            else:
                new_value -= 1

            quality_component.value = new_value
            log.debug('New value for %s: %s (%s %s)', quality, new_value, action, other_quality)
        log.debug('Changed priority for: %s' % ', '.join(list(config.keys())))

    def on_task_exit(self, task, config):
        if not self.quality_priorities:
            log.debug('nothing changed, aborting restore')
            return
        for name, value in self.quality_priorities.items():
            qualities._registry[name].value = value
        log.debug('Restored priority for: %s' % ', '.join(list(self.quality_priorities.keys())))
        self.quality_priorities = {}

    on_task_abort = on_task_exit


@event('plugin.register')
def register_plugin():
    plugin.register(QualityPriority, 'quality_priority', api_ver=2)
