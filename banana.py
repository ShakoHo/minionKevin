__author__ = 'shako'
import os
import datetime
from jenkinsapi.jenkins import Jenkins

class bananaGenerator(object):
    JENKINS_URL = "http://localhost:8080"
    INSPECT_JOB_NAME = "flamekk.vmaster.moztwlab01.512"
    NODE_NAME = "moztwlab-01"
    CONSOLE_LOG_DIR = os.path.join(os.path.sep, "var", "lib", "jenkins", "jobs", INSPECT_JOB_NAME, 'configurations',
                                   'axis-label', NODE_NAME, 'builds')
    SHIFT_DAY = 2
    job_detail = {}

    def __init__(self):
        self.jenkinsObj = Jenkins(self.JENKINS_URL)

    def run(self):
        self.get_build_detail()
        self.get_device_info()
        print self.job_detail

    def get_device_info(self):
        for build_id in self.job_detail.keys():
            console_log_path = os.path.join(self.CONSOLE_LOG_DIR, build_id, "log")
            with open(console_log_path) as console_log_file_obj:
                file_ctnt = console_log_file_obj.readlines()
                build_id_list = [line.strip() for line in file_ctnt if "Build ID" in line]
                if len(build_id_list) == 1:
                    tmp_str = build_id_list[0]
                    if tmp_str.find("Build ID") >= 0:
                        if tmp_str.find("Build ID")+23 <= len(tmp_str):
                            build_id = tmp_str[tmp_str.find("Build ID")+9:tmp_str.find("Build ID")+23]
                        else:
                            build_id = tmp_str[tmp_str.find("Build ID")+9:]
                        self.job_detail[build_id]['build_id'] = build_id

    def get_build_detail(self):
        expected_date = datetime.datetime.today() - datetime.timedelta(days=self.SHIFT_DAY)
        for build_id in self.jenkinsObj[self.INSPECT_JOB_NAME]:
            build_obj = self.jenkinsObj[self.INSPECT_JOB_NAME].get_build(build_id)
            build_date = build_obj.get_timestamp().strftime('%Y-%m-%d')
            if build_date == expected_date.strftime('%Y-%m-%d'):
                if build_id not in self.job_detail.keys():
                    if build_obj.is_running() == False:
                        build_running_secs = build_obj.get_duration().total_seconds()
                        self.job_detail[build_id] = {'running_secs':build_running_secs, 'crash_no':1}



def main():
    bg_obj = bananaGenerator()
    bg_obj.run()

if __name__ == "__main__":
    main()
