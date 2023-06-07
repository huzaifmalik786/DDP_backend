import os
import json
import requests
from dotenv import load_dotenv
from ddpui.ddpairbyte import schema
from ddpui.utils.ab_logger import logger
from ddpui.utils.helpers import remove_nested_attribute
from ddpui.ddpairbyte.schema import AirbyteSourceCreate, AirbyteDestinationCreate

load_dotenv()


class AirbyteError(Exception):
    """exception class with two strings"""

    def __init__(self, detail: str, errors: str):
        super().__init__(detail)
        self.errors = errors


def abreq(endpoint, req=None):
    """Request to the airbyte server"""
    abhost = os.getenv("AIRBYTE_SERVER_HOST")
    abport = os.getenv("AIRBYTE_SERVER_PORT")
    abver = os.getenv("AIRBYTE_SERVER_APIVER")
    token = os.getenv("AIRBYTE_API_TOKEN")

    logger.info("Making request to Airbyte server: %s", endpoint)
    res = requests.post(
        f"http://{abhost}:{abport}/api/{abver}/{endpoint}",
        headers={"Authorization": f"Basic {token}"},
        json=req,
        timeout=30,
    )
    try:
        result_obj = remove_nested_attribute(res.json(), "icon")
        logger.info("Response from Airbyte server:")
        logger.info(json.dumps(result_obj, indent=2))
    except ValueError:
        logger.info("Response from Airbyte server: %s", res.text)
    try:
        res.raise_for_status()
    except Exception as error:
        logger.exception(error)

    if "application/json" in res.headers.get("Content-Type", ""):
        return res.json()
    return {}


def get_workspaces():
    """Fetch all workspaces in airbyte server"""
    return abreq("workspaces/list")

def get_workspace(workspace_id: str) -> dict:
    """Fetch a workspace from the airbyte server"""
    if not isinstance(workspace_id, str):
        raise TypeError("workspace_id must be a string")
    
    try:
        return abreq("workspaces/get", {"workspaceId": workspace_id})
    except Exception as e:
        raise RuntimeError(f"Error fetching workspace: {str(e)}")

def set_workspace_name(workspace_id: str, name: str) -> dict:
    """Set workspace name in the airbyte server"""
    if not isinstance(workspace_id, str):
        raise TypeError("Workspace ID must be a string")
    
    if not isinstance(name, str):
        raise TypeError("Name must be a string")
    
    try:
        return abreq("workspaces/update_name", {"workspaceId": workspace_id, "name": name})
    except Exception as e:
        raise RuntimeError(f"Error setting workspace name: {str(e)}")

def create_workspace(name: str) -> dict:
    """Create a workspace in the airbyte server"""
    if not isinstance(name, str):
        raise TypeError("Name must be a string")

    try:
        res = abreq("workspaces/create", {"name": name})
        if "workspaceId" not in res:
            raise Exception(res)
        return res
    except Exception as e:
        raise RuntimeError(f"Error creating workspace: {str(e)}")

def get_source_definitions(workspace_id, **kwargs):  # pylint: disable=unused-argument
    """Fetch source definitions for an airbyte workspace"""
    res = abreq("source_definitions/list_for_workspace", {"workspaceId": workspace_id})
    if "sourceDefinitions" not in res:
        raise Exception(res)
    return res["sourceDefinitions"]


def get_source_definition_specification(workspace_id, sourcedef_id):
    """Fetch source definition specification for a source in an airbyte workspace"""
    res = abreq(
        "source_definition_specifications/get",
        {"sourceDefinitionId": sourcedef_id, "workspaceId": workspace_id},
    )
    if "connectionSpecification" not in res:
        raise Exception(res)
    return res["connectionSpecification"]


def get_sources(workspace_id):
    """Fetch all sources in an airbyte workspace"""
    res = abreq("sources/list", {"workspaceId": workspace_id})
    if "sources" not in res:
        raise Exception(res)
    return res["sources"]


def get_source(workspace_id, source_id):  # pylint: disable=unused-argument
    """Fetch a source in an airbyte workspace"""
    res = abreq("sources/get", {"sourceId": source_id})
    if "sourceId" not in res:
        raise Exception(res)
    return res


def delete_source(workspace_id, source_id):  # pylint: disable=unused-argument
    """Deletes a source in an airbyte workspace"""
    res = abreq("sources/delete", {"sourceId": source_id})
    return res


def create_source(workspace_id, name, sourcedef_id, config):
    """Create source in an airbyte workspace"""
    res = abreq(
        "sources/create",
        {
            "workspaceId": workspace_id,
            "name": name,
            "sourceDefinitionId": sourcedef_id,
            "connectionConfiguration": config,
        },
    )
    if "sourceId" not in res:
        raise Exception("Failed to create source")
    return res


def update_source(source_id, name, config, sourcedef_id):
    """Update source in an airbyte workspace"""
    res = abreq(
        "sources/update",
        {
            "sourceId": source_id,
            "name": name,
            "connectionConfiguration": config,
            "sourceDefinitionId": sourcedef_id,
        },
    )
    if "sourceId" not in res:
        raise Exception(f"Failed to update source {source_id}: {res}")
    return res


def check_source_connection(workspace_id, data: AirbyteSourceCreate):
    """Test a potential source's connection in an airbyte workspace"""
    res = abreq(
        "scheduler/sources/check_connection",
        {
            "sourceDefinitionId": data.sourceDefId,
            "connectionConfiguration": data.config,
            "workspaceId": workspace_id,
        },
    )
    # {
    #   'status': 'succeeded',
    #   'jobInfo': {
    #     'id': 'ecd78210-5eaa-4a70-89ad-af1d9bc7c7f2',
    #     'configType': 'check_connection_source',
    #     'configId': 'Optional[decd338e-5647-4c0b-adf4-da0e75f5a750]',
    #     'createdAt': 1678891375849,
    #     'endedAt': 1678891403356,
    #     'succeeded': True,
    #     'connectorConfigurationUpdated': False,
    #     'logs': {'logLines': [str]}
    #   }
    # }
    return res


def get_source_schema_catalog(
    workspace_id, source_id
):  # pylint: disable=unused-argument
    """Fetch source schema catalog for a source in an airbyte workspace"""
    res = abreq("sources/discover_schema", {"sourceId": source_id})
    if "catalog" not in res and "jobInfo" in res:
        raise AirbyteError(
            "Failed to get source schema catalogs",
            res["jobInfo"]["failureReason"]["externalMessage"],
        )
    if "catalog" not in res and "jobInfo" not in res:
        raise AirbyteError("Failed to get source schema catalogs", res["message"])
    return res


def get_destination_definitions(
    workspace_id, **kwargs
):  # pylint: disable=unused-argument
    """Fetch destination definitions in an airbyte workspace"""
    res = abreq(
        "destination_definitions/list_for_workspace", {"workspaceId": workspace_id}
    )
    if "destinationDefinitions" not in res:
        raise Exception("Failed to get destination definitions")
    return res["destinationDefinitions"]


def get_destination_definition_specification(workspace_id, destinationdef_id):
    """Fetch destination definition specification for a destination in a workspace"""
    res = abreq(
        "destination_definition_specifications/get",
        {"destinationDefinitionId": destinationdef_id, "workspaceId": workspace_id},
    )
    if "connectionSpecification" not in res:
        raise Exception("Failed to get destination definition specification")
    return res["connectionSpecification"]


def get_destinations(workspace_id):
    """Fetch all desintations in an airbyte workspace"""
    res = abreq("destinations/list", {"workspaceId": workspace_id})
    if "destinations" not in res:
        raise Exception("Failed to get destinations")
    return res["destinations"]


def get_destination(workspace_id, destination_id):  # pylint: disable=unused-argument
    """Fetch a destination in an airbyte workspace"""
    res = abreq("destinations/get", {"destinationId": destination_id})
    if "destinationId" not in res:
        raise Exception("Failed to get destination")
    return res


def create_destination(workspace_id, name, destinationdef_id, config):
    """Create destination in an airbyte workspace"""
    res = abreq(
        "destinations/create",
        {
            "workspaceId": workspace_id,
            "name": name,
            "destinationDefinitionId": destinationdef_id,
            "connectionConfiguration": config,
        },
    )
    if "destinationId" not in res:
        raise Exception(res)
    return res


def update_destination(destination_id, name, config, destinationdef_id):
    """Update a destination in an airbyte workspace"""
    res = abreq(
        "destinations/update",
        {
            "destinationId": destination_id,
            "name": name,
            "connectionConfiguration": config,
            "destinationDefinitionId": destinationdef_id,
        },
    )
    if "destinationId" not in res:
        raise Exception(f"Failed to update destination {destination_id}: {res}")
    return res


def check_destination_connection(workspace_id, data: AirbyteDestinationCreate):
    """Test a potential destination's connection in an airbyte workspace"""
    res = abreq(
        "scheduler/destinations/check_connection",
        {
            "destinationDefinitionId": data.destinationDefId,
            "connectionConfiguration": data.config,
            "workspaceId": workspace_id,
        },
    )
    return res


def get_connections(workspace_id):
    """Fetch all connections of an airbyte workspace"""
    res = abreq("connections/list", {"workspaceId": workspace_id})
    if "connections" not in res:
        raise Exception(res)
    return res["connections"]


def get_connection(workspace_id, connection_id):  # pylint: disable=unused-argument
    """Fetch a connection of an airbyte workspace"""
    res = abreq("connections/get", {"connectionId": connection_id})
    if "connectionId" not in res:
        raise Exception(res)
    return res


def create_normalization_operation(workspace_id) -> str:
    """create a normalization operation for this airbyte workspace"""
    response = abreq(
        "/operations/create",
        {
            "workspaceId": workspace_id,
            "name": "op-normalize",
            "operatorConfiguration": {
                "operatorType": "normalization",
                "normalization": {"option": "basic"},
            },
        },
    )
    return response["operationId"]


def create_connection(
    workspace_id, airbyte_norm_op_id, connection_info: schema.AirbyteConnectionCreate
):
    """Create a connection in an airbyte workspace"""
    if len(connection_info.streams) == 0:
        raise Exception("must specify stream names")

    sourceschemacatalog = get_source_schema_catalog(
        workspace_id, connection_info.sourceId
    )
    payload = {
        "sourceId": connection_info.sourceId,
        "destinationId": connection_info.destinationId,
        "sourceCatalogId": sourceschemacatalog["catalogId"],
        "syncCatalog": {
            "streams": [
                # <== we're going to put the stream configs in here in the next step below
            ]
        },
        "status": "active",
        "prefix": "",
        "namespaceDefinition": "destination",
        "namespaceFormat": "${SOURCE_NAMESPACE}",
        "nonBreakingChangesPreference": "ignore",
        "scheduleType": "manual",
        "geography": "auto",
        "name": connection_info.name,
    }
    if connection_info.destinationSchema:
        payload["namespaceDefinition"] = "customformat"
        payload["namespaceFormat"] = connection_info.destinationSchema

    if connection_info.normalize:
        payload["operationIds"] = [airbyte_norm_op_id]

    # one stream per table
    selected_streams = {x["name"]: x for x in connection_info.streams}
    for schema_cat in sourceschemacatalog["catalog"]["streams"]:
        stream_name = schema_cat["stream"]["name"]
        if (
            stream_name in selected_streams
            and selected_streams[stream_name]["selected"]
        ):
            # set schema_cat['config']['syncMode'] from schema_cat['stream']['supportedSyncModes'] here
            schema_cat["config"]["syncMode"] = selected_streams[stream_name]["syncMode"]
            schema_cat["config"]["destinationSyncMode"] = selected_streams[stream_name][
                "destinationSyncMode"
            ]
            payload["syncCatalog"]["streams"].append(schema_cat)

    res = abreq("connections/create", payload)
    if "connectionId" not in res:
        raise Exception(res)
    return res


def update_connection(
    workspace_id, connection_id, connection_info: schema.AirbyteConnectionUpdate
):
    """Update a connection of an airbyte workspace"""
    if len(connection_info.streams) == 0:
        raise Exception("must specify stream names")

    sourceschemacatalog = get_source_schema_catalog(
        workspace_id, connection_info.sourceId
    )

    payload = {
        "connectionId": connection_id,
        "sourceId": connection_info.sourceId,
        "destinationId": connection_info.destinationId,
        "sourceCatalogId": sourceschemacatalog["catalogId"],
        "syncCatalog": {
            "streams": [
                # <== we're going to put the stream configs in here in the next step below
            ]
        },
        "prefix": "",
        "namespaceDefinition": "destination",
        "namespaceFormat": "${SOURCE_NAMESPACE}",
        "nonBreakingChangesPreference": "ignore",
        "scheduleType": "manual",
        "geography": "auto",
        "name": connection_info.name,
        "operations": [
            {
                "name": "Normalization",
                "workspaceId": workspace_id,
                "operatorConfiguration": {
                    "operatorType": "normalization",
                    "normalization": {"option": "basic"},
                },
            }
        ],
    }

    # one stream per table
    selected_streams = [{x["name"]: x} for x in connection_info.streams]
    for schema_cat in sourceschemacatalog["catalog"]["streams"]:
        stream_name = schema_cat["stream"]["name"]
        if (
            stream_name in selected_streams
            and selected_streams[stream_name]["selected"]
        ):
            # set schema_cat['config']['syncMode'] from schema_cat['stream']['supportedSyncModes'] here
            schema_cat["config"]["syncMode"] = (
                "incremental"
                if selected_streams[stream_name]["incremental"]
                else "full_refresh"
            )
            schema_cat["config"]["destinationSyncMode"] = selected_streams[stream_name][
                "destinationSyncMode"
            ]
            payload["syncCatalog"]["streams"].append(schema_cat)

    res = abreq("connections/update", payload)
    if "connectionId" not in res:
        raise Exception(res)
    return res


def delete_connection(workspace_id, connection_id):  # pylint: disable=unused-argument
    """Delete a connection of an airbyte workspace"""
    res = abreq("connections/delete", {"connectionId": connection_id})
    return res


def sync_connection(workspace_id, connection_id):  # pylint: disable=unused-argument
    """Sync a connection in an airbyte workspace"""
    res = abreq("connections/sync", {"connectionId": connection_id})
    return res


def get_job_info(job_id: str):
    """get debug info for an airbyte job"""
    res = abreq("jobs/get_debug_info", {"id": job_id})
    return res
