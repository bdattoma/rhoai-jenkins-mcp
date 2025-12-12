from collections import defaultdict
from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp
from typing import Dict, Any

jenkins_client = JenkinsClient.getJenkinsClient()

cluster_default_configs = {
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
    return jenkins_client.run_job(job_name, params)


@mcp.tool()
async def provision_cluster(cluster_name: str, cluster_type: str, config: Dict[str, Any] = {}) -> str:
#async def provision_cluster(cluster_name: str, cluster_type: str, **config: Dict[str, Any]) -> str:
    """
    Provision a cluster for the given provider and config.
    Args:
        cluster_name (str) (required): The name of the cluster to provision. It MUST be long less than 15 characters.
        cluster_type (str) (optional): The type of the cluster to provision.
        config (dict) (required): The config to provision the cluster with:
            - TEST_ENVIRONMENT (required): alias for Provider, the cloud provider to provision the cluster on. Default to IBM
            - OCP_VERSION (required): the OpenShift version to provision the cluster on.
            - OCP_CHANNEL (optional): the OpenShift channel to provision the cluster on. Default to stable
            - REGION (optional): the region to provision the cluster on
            - CLUSTER_ARCHITECTURE (optional): the architecture of the cluster to provision on (amd64, arm64). Default to amd64
            - TEST_PLATFORM (optional): applicable to Managed clusters only
            - SINGLE_NODE_OPENSHIFT (optional): also known as SNO, applicable to selfmanaged clusters only. Default to False
            - ENABLE_FIPS_IN_CLUSTER (optional): enable FIPS mode
            - CLUSTER_ACTION_POST_EXECUTION (optional): the action to take after the cluster is provisioned (Retain, Delete or Hibernate)
            - TEAM_NAME (optional): The team to run the job for.
            - NUMBER_OF_MASTER_NODES (optional): the number of master nodes to provision the cluster on. If SNO, this is 1.
            - NUMBER_OF_WORKER_NODES (optional): the number of worker nodes to provision the cluster on. If SNO, this is 0.
            - MASTER_FLAVOR (optional): the flavor of the master node to provision the cluster on. Default values are defined in the cluster_default_configs dictionary.
            - WORKER_FLAVOR (optional): the flavor of the worker node to provision the cluster on. Default values are defined in the cluster_default_configs dictionary.
            - TEST_CLUSTER_DETAILS (optional): virtual machine configuration details for the cluster. Compose this field with the following format: REGION,NUMBER_OF_MASTER_NODES,NUMBER_OF_WORKER_NODES,MASTER_FLAVOR,WORKER_FLAVOR,OCP_VERSION,OCP_CHANNEL,CLUSTER_ARCHITECTURE. If SNO, this is the single node flavor.
    Returns:
        String: The jenkins job run URL.
    """
    job_name = "devops/rhoai-test-flow"

    test_environment = config.get('TEST_ENVIRONMENT', 'IBM')
    test_environment_config = cluster_default_configs.get(test_environment, cluster_default_configs["IBM"])
    ocp_version = config.get('OCP_VERSION', '4.20-latest')
    if len(ocp_version.split('.')) == 2:
        ocp_version = f"{ocp_version}-latest"
    test_cluster_details = ",".join([
        config.get('REGION', test_environment_config['region']),
        config.get('NUMBER_OF_MASTER_NODES', test_environment_config['master_nodes']),
        config.get('NUMBER_OF_WORKER_NODES', test_environment_config['worker_nodes']),
        config.get('MASTER_FLAVOR', test_environment_config['master_flavor']),
        config.get('WORKER_FLAVOR', test_environment_config['worker_flavor']),
        ocp_version,
        config.get('OCP_CHANNEL', 'stable'),
        config.get('CLUSTER_ARCHITECTURE', 'amd64'),
    ])

    params = {
        "CLUSTER_NAME": cluster_name,
        "CLUSTER_TYPE": cluster_type.lower() if cluster_type else "selfmanaged",
        "INSTALL_CLUSTER": True,
        "TEST_ENVIRONMENT": test_environment,
        "DEPROVISION_AFTER_INSTALL_FAILURE": True,
        "DEPLOY_RHODS_OPERATOR": False,  # temporary fixed
        "RUN_TESTS": False,  # temporary fixed
        "PUBLISH_RESULTS_TO": "",  # temporary fixed
        "TEST_CLUSTER_DETAILS": test_cluster_details,
    }
    #for key, value in config['config'].items():
    for key, value in config.items():
        if key not in params:   # if the param is already set it means it needs some logic first, do not override it
            params[key] = value
    if len(params.get('CLUSTER_NAME')) > 15:
        raise ValueError("Cluster name must be less or equal to 15 characters")
    #return jenkins_client.run_job(job_name, params)
    # Use the file param method since this job has a File Parameter (EXTERNAL_KUBECONFIG_FILE)
    return jenkins_client.run_job_with_file_param(job_name, params, "EXTERNAL_KUBECONFIG_FILE")

async def get_cluster_info_from_build(build_number: str) -> dict:
    """
    Get the cluster info from the given build number of provisioning job.
    """
    job_name = "devops/rhoai-test-flow"
    build_info = jenkins_client.jenkins.get_build_info(job_name, build_number)
    return build_info['cluster_info']
