from jenkins_mcp.jenkins.client import JenkinsClient
from jenkins_mcp.server import mcp

jenkins_client = JenkinsClient.getJenkinsClient()

@mcp.tool()
async def run_test_matrix(build_image_url: str) -> list:
    """
    Run the test_matrix_run job on the given build image URL.

    Returns:
        String: The jenkins job run.
    """
    # Trigger the Jenkins job with the image URL as a parameter
    job_name = "devops/test_matrix_run"
    params = {"OVERRIDE_ODS_BUILD_URL": build_image_url}
    build_info = jenkins_client.jenkins.build_job(job_name, parameters=params)
    return f"Triggered {job_name} for {build_image_url}. Build info: {build_info}"
