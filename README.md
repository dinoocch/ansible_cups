```
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
```
