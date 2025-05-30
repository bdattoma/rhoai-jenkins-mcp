import argparse
import os
from jenkins_mcp.jenkins.client import JenkinsClient

def main():
    print("Connecting to Jenkins MCP Server")
    parser=argparse.ArgumentParser(description="Jenkins Server Parameters")
    parser.add_argument("--jenkins-url", help="Jenkins Server URL", required=False, dest="jenkins_url", default=os.getenv("JENKINS_URL"))
    parser.add_argument("--jenkins-user", help="Jenkins Server User", required=False, dest="jenkins_user", default=os.getenv("JENKINS_USER"))
    parser.add_argument("--jenkins-password", help="Jenkins Server Password", required=False, dest="jenkins_password", default=os.getenv("JENKINS_PASSWORD"))
    args=parser.parse_args()

    if args.jenkins_url is None or args.jenkins_user is None or args.jenkins_password is None:
        print("Jenkins Server Parameters are not set")
        return
    # rm env variables, not used
    os.environ['JENKINS_URL'] = args.jenkins_url
    os.environ['JENKINS_USER'] = args.jenkins_user
    os.environ['JENKINS_PASSWORD'] = args.jenkins_password
    print(args)
    print(f"Jenkins Server URL: {args.jenkins_url}")
    print(f"Jenkins Server User: {args.jenkins_user}")
    print(f"Jenkins Server Password: {args.jenkins_password}")

    jenkins_client = JenkinsClient(os.environ['JENKINS_URL'], os.environ['JENKINS_USER'], os.environ['JENKINS_PASSWORD'])
    
    from jenkins_mcp.server import mcp
    import jenkins_mcp.server.basic_tools


    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

