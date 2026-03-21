from collections import defaultdict
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import json

# jenkins_client = JenkinsClient.getJenkinsClient()

# Internal dictionary for cluster defaults
_cluster_default_configs = {
    "AWS": {
        "master_nodes": "3",
        "worker_nodes": "3",
        "master_flavor": "m5.2xlarge",
        "worker_flavor": "m5.2xlarge",
        "single_node_flavor": "m5.8xlarge",
        "region": "us-east-1"
    },
    "GCP": {
        "master_nodes": "3",
        "worker_nodes": "3",
        "master_flavor": "custom-8-32768",
        "worker_flavor": "n2-standard-8",
        "single_node_flavor": "n2-standard-8",
        "region": "us-central1"
    },
    "IBM": {
        "master_nodes": "3",
        "worker_nodes": "3",
        "master_flavor": "bx2-4x16",
        "worker_flavor": "bx2-4x16",
        "single_node_flavor": "bx2-32x128",
        "region": "us-east"
    },
    "AZURE": {
        "master_nodes": "3",
        "worker_nodes": "3",
        "master_flavor": "Standard_D8s_v4",
        "worker_flavor": "Standard_D8s_v4",
        "single_node_flavor": "Standard_D32s_v4",
        "region": "eastus"
    },
    "ROSA": {
        "master_nodes": "3",
        "worker_nodes": "3",
        "master_flavor": "m5.2xlarge",
        "worker_flavor": "m5.2xlarge",
        "region": "us-east-1"
    }
}


class ClusterProvisionConfig(BaseModel):
    """Configuration for cluster provisioning."""

    # Required fields
    test_environment: Literal["AWS", "GCP", "IBM", "AZURE", "ROSA"] = Field(
        default="AZURE",
        description="Cloud provider to provision the cluster on"
    )
    ocp_version: str = Field(
        default="4.20-latest",
        description="OpenShift version (e.g., '4.20' or '4.20-latest')"
    )

    # Optional - Cluster architecture
    ocp_channel: str = Field(
        default="stable",
        description="OpenShift channel (stable, fast, candidate)"
    )
    region: Optional[str] = Field(
        default=None,
        description="Region to provision in (uses provider default if not specified)"
    )
    cluster_architecture: Literal["amd64", "arm64"] = Field(
        default="amd64",
        description="Cluster CPU architecture"
    )

    # Optional - Cluster size
    number_of_master_nodes: Optional[str] = Field(
        default=None,
        description="Number of master nodes (uses provider default if not specified)"
    )
    number_of_worker_nodes: Optional[str] = Field(
        default=None,
        description="Number of worker nodes (uses provider default if not specified)"
    )
    master_flavor: Optional[str] = Field(
        default=None,
        description="Master node VM type (uses provider default if not specified)"
    )
    worker_flavor: Optional[str] = Field(
        default=None,
        description="Worker node VM type (uses provider default if not specified)"
    )

    # Optional - Special configurations
    single_node_openshift: bool = Field(
        default=False,
        description="Enable Single Node OpenShift (SNO) - only for selfmanaged clusters"
    )
    enable_fips_in_cluster: bool = Field(
        default=False,
        description="Enable FIPS mode in the cluster"
    )
    test_platform: Optional[str] = Field(
        default=None,
        description="Test platform - applicable to managed clusters only"
    )

    # Optional - Post-provisioning
    cluster_action_post_execution: Optional[Literal["Retain", "Delete", "Hibernate"]] = Field(
        default=None,
        description="Action to take after cluster provisioning completes"
    )
    team_name: Optional[str] = Field(
        default=None,
        description="Team name for the provisioning job"
    )

    class Config:
        # Allow both snake_case and SCREAMING_SNAKE_CASE
        populate_by_name = True


@mcp.resource("cluster://defaults")
async def get_cluster_default_configs() -> str:
    """
    Get default cluster configuration values for all supported cloud providers.
    
    Returns cluster defaults for AWS, GCP, IBM, AZURE, and ROSA including:
    - master_nodes: Number of master nodes
    - worker_nodes: Number of worker nodes
    - master_flavor: VM/instance type for master nodes
    - worker_flavor: VM/instance type for worker nodes
    - single_node_flavor: VM/instance type for single node OpenShift (SNO)
    - region: Default region for the provider
    
    Returns:
        str: JSON-formatted cluster default configurations
    """
    return json.dumps(_cluster_default_configs, indent=2)

@mcp.resource("cluster://defaults/{provider}")
async def get_cluster_provider_config(provider: str) -> str:
    """
    Get default cluster configuration for a specific cloud provider.
    
    Args:
        provider: Cloud provider name (AWS, GCP, IBM, AZURE, or ROSA)
    
    Returns:
        str: JSON-formatted cluster configuration for the specified provider
    """
    provider = provider.upper()
    if provider not in _cluster_default_configs:
        raise ValueError(f"Unknown provider: {provider}. Supported providers: {', '.join(_cluster_default_configs.keys())}")
    return json.dumps(_cluster_default_configs[provider], indent=2)


@mcp.tool()
async def run_test_matrix(rhoai_version: str, build_image_url: str, providers: dict, team: str, mode: str = "auto") -> list:
    """
    Run the test_matrix_run job on the given build image URL.
    Validate a RHOAI build against the given providers.

    Args:
        rhoai_version (str): The RHOAI version to validate.
        build_image_url (str): The URL of the build image to validate.
        mode (str): The mode to run the test matrix in.
        providers (dict): The providers to validate the build against.
        team (str): The team to run the test matrix for. Default to devtestops
    Returns:
        String: The jenkins job run URL.
    """
    # Trigger the Jenkins job with the image URL as a parameter
    job_name = "devops/test_matrix_run"
    # name,enabled,ocp,fips,sno@@@
    print(providers)
    prov_strs = ""
    if providers:
        for provider, config_dict in providers.items():
            config_dict = defaultdict(int, config_dict)
            prov_str = f"{provider},"
            prov_str += f"{config_dict.get('enabled', "true")},"
            prov_str += f"{config_dict.get('ocp', None)},"
            prov_str += f"{config_dict.get('fips', "false")},"
            prov_str += f"{config_dict.get('sno', "false")}"
            prov_str += "@@@"
            prov_strs += prov_str

    fetch = True if mode.lower() == "auto" else False
    params = {
        "OVERRIDE_ODS_BUILD_URL": build_image_url,
        "RHOAI_VERSION_XY": rhoai_version,
        "FETCH_TEST_MATRIX": fetch,
        "CLOUD_PROVIDERS_TABLE": prov_strs,
        "TEAM_NAME": team,
    }
    return JenkinsClient.getJenkinsClient().run_job(job_name, params)


@mcp.tool()
async def provision_cluster(
    cluster_name: str,
    cluster_type: str = "selfmanaged",
    config: ClusterProvisionConfig = ClusterProvisionConfig()
) -> str:
    """
    Provision a cluster for testing RHOAI.

    Args:
        cluster_name: Name of the cluster (max 15 characters)
        cluster_type: Type of cluster ("selfmanaged" or "managed")
        config: Cluster configuration (see ClusterProvisionConfig for all options)

    Returns:
        Jenkins job run URL

    Note:
        Check cluster://defaults resource for provider-specific default configurations.
    """
    if len(cluster_name) > 15:
        raise ValueError("Cluster name must be 15 characters or less")

    job_name = "devops/rhoai-test-flow"

    # Get provider defaults
    test_environment = config.test_environment
    test_environment_config = _cluster_default_configs.get(test_environment, _cluster_default_configs["AZURE"])

    # Handle OCP version format
    ocp_version = config.ocp_version
    if len(ocp_version.split('.')) == 2:
        ocp_version = f"{ocp_version}-latest"

    # Build TEST_CLUSTER_DETAILS string
    test_cluster_details = ",".join([
        config.region or test_environment_config['region'],
        config.number_of_master_nodes or test_environment_config['master_nodes'],
        config.number_of_worker_nodes or test_environment_config['worker_nodes'],
        config.master_flavor or test_environment_config['master_flavor'],
        config.worker_flavor or test_environment_config['worker_flavor'],
        ocp_version,
        config.ocp_channel,
        config.cluster_architecture,
    ])

    # Build Jenkins parameters
    params = {
        "CLUSTER_NAME": cluster_name,
        "CLUSTER_TYPE": cluster_type.lower(),
        "INSTALL_CLUSTER": True,
        "TEST_ENVIRONMENT": test_environment,
        "DEPROVISION_AFTER_INSTALL_FAILURE": True,
        "DEPLOY_RHODS_OPERATOR": False,  # temporary fixed
        "RUN_TESTS": False,  # temporary fixed
        "PUBLISH_RESULTS_TO": "",  # temporary fixed
        "TEST_CLUSTER_DETAILS": test_cluster_details,
    }

    # Add optional config parameters (using SCREAMING_SNAKE_CASE)
    if config.single_node_openshift:
        params["SINGLE_NODE_OPENSHIFT"] = config.single_node_openshift
    if config.enable_fips_in_cluster:
        params["ENABLE_FIPS_IN_CLUSTER"] = config.enable_fips_in_cluster
    if config.test_platform:
        params["TEST_PLATFORM"] = config.test_platform
    if config.cluster_action_post_execution:
        params["CLUSTER_ACTION_POST_EXECUTION"] = config.cluster_action_post_execution
    if config.team_name:
        params["TEAM_NAME"] = config.team_name

    # Use the file param method since this job has a File Parameter (EXTERNAL_KUBECONFIG_FILE)
    return JenkinsClient.getJenkinsClient().run_job_with_file_param(job_name, params, "EXTERNAL_KUBECONFIG_FILE")

async def get_cluster_info_from_build(build_number: str) -> dict:
    """
    Get the cluster info from the given build number of provisioning job.
    """
    job_name = "devops/rhoai-test-flow"
    build_info = JenkinsClient.getJenkinsClient().jenkins.get_build_info(job_name, build_number)
    return build_info['cluster_info']
