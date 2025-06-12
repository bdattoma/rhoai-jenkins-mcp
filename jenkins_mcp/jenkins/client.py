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

    def getJenkinsClient():
        return JenkinsClient()

