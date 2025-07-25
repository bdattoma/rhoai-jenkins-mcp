# from jenkinsapi import jenkins
import jenkins
import os


class JenkinsClient:
    instance = None
    myattrib = ""


    def __new__(cls, url=None, username=None, password=None):
        if not cls.instance:
            cls.instance = super(JenkinsClient, cls).__new__(cls)
            cls.instance.url = url
            cls.instance.username = username
            cls.instance.password = password
            cls.instance.jenkins = jenkins.Jenkins(url, username, password)
            print(f"Jenkins Client created for {url}")
        else:
            print(f"Re-using existant Jenkins Client for {cls.instance.url}")
        return cls.instance
    
    def get_jobs(self):
        names = []
        for job in self.jenkins.get_jobs():
            names.append(job['name'])
        return names
    
    def get_job_info(self, job_name):
        return self.jenkins.get_job_config(job_name)

    def getJenkinsClient():
        return JenkinsClient()

    def run_job(self, job_name, params):
        queue_number = self.jenkins.build_job(job_name, parameters=params)
        queue_item = self.jenkins.get_queue_item(queue_number)
        if queue_item and queue_item.get('executable', {}).get('url', None):
            build_url = queue_item['executable']['url']
            msg = f"{job_name} triggered. Build URL: {build_url}"
        else:
            build_url = None
            msg = f"{job_name} waiting to be scheduled. Queue number: {queue_number}"
        return msg

