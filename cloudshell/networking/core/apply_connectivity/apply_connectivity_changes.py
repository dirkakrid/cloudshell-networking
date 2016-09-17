import logging

import jsonpickle
from cloudshell.core.action_result import ActionResult
from cloudshell.core.driver_request import DriverRequest
from cloudshell.core.driver_response import DriverResponse
from cloudshell.core.driver_response_root import DriverResponseRoot
from cloudshell.networking.core.apply_connectivity.connectivity_action_request import ConnectivityActionRequest
from cloudshell.networking.core.apply_connectivity.connectivity_action_result import ConnectivityActionResult


def connectivity_request_from_json(json_request):
    json_obj = jsonpickle.decode(json_request)
    if 'driverRequest' not in json_obj:
        raise Exception('ConnectivityOperations', 'Deserialized request is None or empty')
    request = DriverRequest()
    request.actions = []
    for action in json_obj['driverRequest']['actions']:
        request.actions.append(ConnectivityActionRequest.from_dict(action))
    return request


def apply_connectivity_changes(request, add_vlan_action, remove_vlan_action, logger=None):
    """
    Standard implementation for the apply_connectivity_changes operation
    This function will accept as an input the actions to perform for add/remove vlan. It implements
    the basic flow of decoding the JSON connectivity changes requests, and combining the results
    of the add/remove vlan functions into a result object.

    :param str request: json string sent from the CloudShell server describing the connectivity changes to perform
    :param (ConnectivityActionRequest) -> ConnectivityActionResult remove_vlan_action: This action will be called for VLAN remove operations
    :param (ConnectivityActionRequest) -> ConnectivityActionResult add_vlan_action: This action will be called for VLAN_add_operations
    :param logger: logger to use for the operation, if you don't provide a logger, a default Python logger will be used
    :return Returns a driver action result object, this can be returned to CloudShell server by the command result
    :rtype: DriverResponseRoot
    """

    if not logger:
        logger = logging.getLogger("apply_connectivity_changes")

    if request is None or request == '':
        raise Exception('ConnectivityOperations', 'request is None or empty')

    holder = connectivity_request_from_json(request)

    driver_response = DriverResponse()
    results = []
    driver_response_root = DriverResponseRoot()

    for action in holder.actions:
        logger.info('Action: ', action.__dict__)
        if action.type == ConnectivityActionRequest.SET_VLAN:
            action_result = add_vlan_action(action)

        elif action.type == ConnectivityActionRequest.REMOVE_VLAN:
            action_result = remove_vlan_action(action)

        else:
            continue
        results.append(action_result)

    driver_response.actionResults = results
    driver_response_root.driverResponse = driver_response
    return driver_response_root


class ConnectivitySuccessResponse(ConnectivityActionResult):
    def __init__(self, action, result_string):
        ConnectivityActionResult.__init__(self)
        self.type = action.type
        self.actionId = action.actionId
        self.errorMessage = None
        self.updatedInterface = action.actionTarget.fullName
        self.infoMessage = result_string
        self.success = True



class ConnectivityErrorResponse(ConnectivityActionResult):
    def __init__(self, action, error_string):
        ConnectivityActionResult.__init__(self)
        self.type = action.type
        self.actionId = action.actionId
        self.infoMessage = None
        self.updatedInterface = action.actionTarget.fullName
        self.errorMessage = error_string
        self.success = False
