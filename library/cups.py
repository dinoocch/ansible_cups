#!/usr/bin/env python

from ansible.module_utils.basic import AnsibleModule
try:
    import cups
    HAS_CUPS = 1
except:
    HAS_CUPS = 0

__author__ = "Dino Occhialini"
__email__ = "dino.occhialini@gmail.com"

DOCUMENTATION = '''
---
module: cups
author:
    - Dino Occhialini (dinoocch) <dino.occhialini@gmail.com>
short_description: Manage cups configuration
description:
    - Manage printers and classes in CUPS
version_added: "2.4"
notes: []
requirements:
    - pycups
options:
    name:
        description: Name of printer or class
        required: true
    state:
        description: Whether object should exist
        required: false
        default: present
        choices: ["present", "absent", "enabled", "disabled"]
    driver:
        description: Driver to configure fo printer
        required: false
        default: null
    description:
        description: Description of printer or class (info)
        required: false
        default: null
    location:
        description: Location Description of printer or class
        required: false
        default: null
    type:
        description: Printer or class
        required: false
        default: printer
        choices: ["printer", "class"]
    uri:
        description: URI to connect to for the printer
        required: false
        default: null
    shared:
        description: Share printer with network
        required: false
        default: false
        choices: ["true", "false"]
    default:
        description: Set the default printer for the server
        required: false
        default: false
        choices: ["true", "false"]
    members:
        description: Printers to include in class
        required: false
        default: false
    policy:
        description: OpPolicy to apply to object
        required: false
        default: default
    error_policy:
        description: Error policy to apply to the printer
        required: false
        default: abort-job
'''

EXAMPLES = '''
TODO
'''


class CupsPrinter(object):
    def __init__(self, connection, params, check_mode):
        self.connection = connection
        self.params = params
        self.name = params['name']
        self.check_mode = check_mode
        self.type = params['type']

        self.state = self.get_information()

    def _class_members(self):
        changes = []
        if len(self.params['members']) == 0:
            self.module.fail_json(msg="At least one member is required.")
        current_members = set(self.state['members'])
        wanted_members = set(self.params['members'])
        if current_members != wanted_members:
            changes.append("members")
            if not self.check_mode:
                add_members = list(wanted_members - current_members)
                del_members = list(current_members - wanted_members)
                for queue in add_members:
                    self.connection.addPrinterToClass(queue, self.name)
                for queue in del_members:
                    self.connection.deletePrinterFromClass(queue,
                                                           self.name)
        return changes

    def _queue_exist(self):
        changes = []
        if (self.params['state'] in ['present', 'enabled'] and
                not self.state['queue_exist']):
            changes.append("Queue Added")
            if not self.check_mode:
                self.connection.addPrinter(self.name)
        return changes

    def _enabled(self):
        changes = []
        if (self.state.get('enabled', True) and
                self.params['state'] == 'disabled'):
            changes.append('Disabled Printer')
            if not self.check_mode:
                self.connection.disablePrinter(self.name)
        elif (not self.state.get('enabled', False) and
                self.params['state'] == 'enabled'):
            changes.append('Enabled Printer')
            if not self.check_mode:
                self.connection.enablePrinter(self.name)
        return changes

    def _driver(self):
        changes = []
        if (self.state.get('ppdname', None) != self.params['driver'] and
                self.params['driver'] is not None):
            changes.append('driver')
            if not self.check_mode:
                self.connection.addPrinter(self.name,
                                           ppdname=self.params['driver'])
        return changes

    def _description(self):
        changes = []
        if self.params['description'] != self.state.get('printer-info', None):
            changes.append('description')
            if not self.check_mode:
                self.connection.setPrinterInfo(self.name,
                                               self.params['description'])

        return changes

    def _location(self):
        changes = []
        if self.params['location'] != self.state.get('printer-location', None):
            changes.append('location')
            if not self.check_mode:
                self.connection.setPrinterLocation(self.name,
                                                   self.params['location'])
        return changes

    def _device(self):
        changes = []
        if self.params['uri'] != self.state.get('device-uri', None):
            changes.append('device uri')
            if not self.check_mode:
                self.connection.setPrinterDevice(self.name,
                                                 self.params['uri'])
        return changes

    def _opPolicy(self):
        changes = []
        current_policy = self.state.get('printer-op-policy', 'default')
        if self.params['policy'] != current_policy:
            changes.append('opPolicy')
            if not self.check_mode:
                self.connection.setPrinterOpPolicy(self.name,
                                                   self.params['policy'])
        return changes

    def _errorPolicy(self):
        changes = []
        error_policy = self.params['error_policy']
        if error_policy != self.state.get('printer-error-policy', None):
            changes.append('error-policy')
            if not self.check_mode:
                self.connection.setPrinterErrorPolicy(self.name,
                                                      error_policy)
        return changes

    def _users(self):
        changes = []
        # users allowed
        current_allowed = set(self.state.get('requesting-user-name-allowed',
                                             ['all']))
        wanted_allowed = set(self.params['users_allowed'])
        if current_allowed != wanted_allowed:
            changes.append('User Allow List')
            if not self.check_mode:
                self.connection.setPrinterUsersAllowed(
                        self.name,
                        self.params['users_allowed'])

        # users denied
        current_denied = set(self.state.get('requesting-user-name-denied',
                                            ['none']))
        wanted_denied = set(self.params['users_denied'])
        if current_denied != wanted_denied:
            changes.append('User Deny List')
            if not self.check_mode:
                self.connection.setPrinterUsersDenied(
                        self.name,
                        self.params['users_denied'])
        return changes

    def _default(self):
        changes = []
        is_default = self.state['default_printer'] == self.name
        if self.params['is_default'] and not is_default:
            changes.append("Default Printer")
            if not self.check_mode:
                self.connection.setDefault(self.name)
        return changes

    def _shared(self):
        changes = []
        is_shared = self.state.get('printer-is-shared', False)
        if self.params['shared'] and not is_shared:
            changes.append("Shared Printer")
            if not self.check_mode:
                self.connection.setPrinterShared(self.name, True)
        elif not self.params['shared'] and is_shared:
            changes.append("UnShared Printer")
            if not self.check_mode:
                self.connection.setPrinterShared(self.name, True)
        return changes

    def get_information(self):
        state = {}
        connection = self.connection
        printers = connection.getPrinters()
        state['default_printer'] = connection.getDefault()

        if self.type == 'class':
            classes = connection.getClasses()
            if self.name not in classes:
                state['members'] = []
            else:
                state['members'] = classes[self.name]
        if self.name not in printers:
            state['queue_exist'] = False
            return state

        state['queue_exist'] = True
        printer_definition = connection.getPrinterAttributes(self.name)

        if printer_definition['printer-state'] == 5:
            state['enabled'] = False
        else:
            state['enabled'] = True
        printer_make = printer_definition['printer-make-and-model']
        try:
            state['ppdname'] = connection.getPPDs(
                    ppd_make_and_model=printer_make)
            state['ppdname'] = list(state['ppdname'].keys())[0]
        except:
            state['ppdname'] = None

        for key, value in printer_definition.items():
            state[key] = value

        return state

    def enforce_params(self):
        check = self.check_mode
        changes = []

        # Existence and Members
        if self.type == 'class':
            if self.params['state'] == 'absent':
                changes = ['Class Deleted']
                if not check:
                    self.connection.deleteClass(self.name)
                    return changes
            changes.extend(self._class_members())
        else:
            if (self.params['state'] == 'absent' and
                    not self.state['queue_exist']):
                return changes
            changes.extend(self._queue_exist())

        # Enabled/Disabled
        changes.extend(self._enabled())

        # Driver
        changes.extend(self._driver())

        # Info
        changes.extend(self._description())

        # Location
        changes.extend(self._location())

        # uri
        changes.extend(self._device())

        # policy
        changes.extend(self._opPolicy())

        # error policy
        changes.extend(self._errorPolicy())

        # users
        changes.extend(self._users())

        # default
        changes.extend(self._default())

        # shared
        changes.extend(self._shared())

        # set default options
        for option, value in self.params['options'].items():
            if self.state.get(option, None) != value:
                changes.append('Changed value of {0}'.format(option))
                if not check:
                    self.connection.addPrinterOptionDefault(self.name, option,
                                                            value)
        return changes


def main():
    argument_spec = dict(
            name=dict(required=True),
            state=dict(default="present",
                       choices=["present", "absent", "enabled", "disabled"]),
            driver=dict(default=None),
            description=dict(default=""),
            is_default=dict(default=False, type="bool"),
            location=dict(default=""),
            type=dict(default="printer", choices=["printer", "class"]),
            uri=dict(default="file:///dev/null"),
            members=dict(default=[], type="list"),
            policy=dict(default="default"),
            shared=dict(default=False),
            error_policy=dict(default="abort-job"),
            users_allowed=dict(default=["all"], type="list"),
            users_denied=dict(default=["none"], type="list"),
            options=dict(default={}, type="dict")
            )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_CUPS:
        module.fail_json(msg="Missing required package 'pycups'")

    connection = None
    try:
        connection = cups.Connection()
    except:
        module.fail_json(msg="Failed to connect to cups server.")

    printer = CupsPrinter(connection, module.params, module.check_mode)

    changed = printer.enforce_params()

    module.exit_json(changed=len(changed), diff=dict(before='',
                     after='\n'.join(changed + ['\n'])))


main()

# vim: ai ts=4 sts=4 et sw=4 ft=python
