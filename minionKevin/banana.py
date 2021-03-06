__author__ = 'shako'
import os
import json
import copy
import time
import commands
import datetime
import argparse
from argparse import ArgumentDefaultsHelpFormatter
from jenkinsapi.jenkins import Jenkins

class BananaGenerator(object):
    JENKINS_URL = "http://localhost:8080"
    SERIES_NAME = "mtbf"
    INSPECT_JOB_NAME = "flamekk.vmaster.moztwlab01.512"
    NODE_NAME = "moztwlab-01"
    CONSOLE_LOG_DIR = os.path.join(os.path.sep, "var", "lib", "jenkins", "jobs", INSPECT_JOB_NAME, 'configurations',
                                   'axis-label', NODE_NAME, 'builds')
    OUTPUT_JSON_DIR = "output"
    SHIFT_DAY   = 3
    EXPECTED_DATE = None

    def __init__(self):


        self.arg_parser = argparse.ArgumentParser(description='Generate raptor json data and upload it',
                                                  formatter_class=ArgumentDefaultsHelpFormatter)
        self.arg_parser.add_argument('-o', '--raptor-host-name', action='store', dest='raptor_host_name', default=None,
                                     help='raptor host name', required=True)

        self.arg_parser.add_argument('-p', '--raptor-port-no', action='store', dest='raptor_port_no', default=None,
                                     help='raptor port no', required=True)

        self.arg_parser.add_argument('-u', '--raptor-user-name', action='store', dest='raptor_user', default=None,
                                     help='raptor user name', required=True)

        self.arg_parser.add_argument('-d', '--raptor-user-pwd', action='store', dest='raptor_pwd', default=None,
                                     help='raptor user password', required=True)

        self.arg_parser.add_argument('-b', '--raptor-database', action='store', dest='raptor_db', default=None,
                                     help='raptor database', required=True)

        self.args = self.arg_parser.parse_args()

        self.r_host_name = self.args.raptor_host_name

        self.r_port_no = self.args.raptor_port_no

        self.r_user = self.args.raptor_user

        self.r_pwd = self.args.raptor_pwd

        self.r_db = self.args.raptor_db

        self.jenkinsObj = Jenkins(self.JENKINS_URL)

    def get_expected_date(self):
        self.EXPECTED_DATE = datetime.datetime.today() - datetime.timedelta(days=self.SHIFT_DAY)

    def upload_raptor_data(self, upload_data_path_list, host_name, port_no, user_name, pwd, database_name):
        cmd_format = "raptor submit %s --host %s --port %s --username %s --password %s --database %s --protocol https"
        for upload_data_path in upload_data_path_list:
            cmd_str = cmd_format % (upload_data_path, host_name, port_no, user_name, pwd, database_name)
            result = commands.getstatusoutput(cmd_str)
            if result[0] != 0:
                print "upload raptor data error: %s %s" % result
            else:
                print "upload raptor data successfully!"

    def run(self):
        self.get_expected_date()
        job_detail = self.get_build_detail()
        job_detail = self.get_device_info(job_detail)
        raptor_data = self.convert_to_raptor_data(job_detail)
        if len(raptor_data) > 0:
            output_file_path = self.dump_raptor_data_to_json_file(raptor_data)
            self.upload_raptor_data(output_file_path, self.r_host_name, self.r_port_no, self.r_user, self.r_pwd, self.r_db)

    def dump_raptor_data_to_json_file(self, raptor_data):
        result = []
        for data_type in raptor_data.keys():
            output_file_name = self.EXPECTED_DATE.strftime('%Y%m%d') + "_" + data_type + ".json"
            output_dir = os.path.join(os.getcwd(), self.OUTPUT_JSON_DIR)
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            output_file_path = os.path.join(output_dir, output_file_name)
            result.append(output_file_path)
            with open(output_file_path, "w") as json_output_file:
                json.dump(raptor_data[data_type], json_output_file)
        return result

    def convert_to_raptor_data(self, job_detail):
        build_configuration = self.INSPECT_JOB_NAME.split(".")
        result = {'data':[], 'event':[]}
        create_event_flag = False
        for build_id in job_detail.keys():
            insert_dict = {'key': self.SERIES_NAME}
            insert_dict['timestamp'] = self.convert_datetime_to_timestamp(job_detail[build_id]['build_id'])

            insert_dict['fields'] = {}
            insert_dict['fields']['value'] = job_detail[build_id]['running_secs'] / 60.0 / 60.0
            insert_dict['fields']['failures'] = job_detail[build_id]['crash_no']

            insert_dict['tags'] = {}
            insert_dict['tags']['branch'] = build_configuration[1].replace("vmaster","master")
            insert_dict['tags']['device'] = build_configuration[0].replace("flamekk","flame-kk")
            insert_dict['tags']['deviceId'] = job_detail[build_id]['device_id']
            insert_dict['tags']['memory'] = build_configuration[3]
            insert_dict['tags']['node'] = build_configuration[2]
            if create_event_flag is False and insert_dict['tags']['deviceId'] != 0:
                event_data = {}
                event_data['timestamp'] = insert_dict['timestamp']
                event_data['key'] = "annotation"
                event_data['fields'] = {}
                event_data['fields']['text'] = job_detail[build_id]['build_id']
                event_data['tags'] = {}
                event_data['tags']['title'] = "BuildId"
                event_data['tags']['test'] = "mtbf"
                event_data['tags']['branch'] = insert_dict['tags']['branch']
                event_data['tags']['device'] = insert_dict['tags']['device']
                event_data['tags']['memory'] = insert_dict['tags']['memory']
                result['event'].append(event_data)
                create_event_flag = True
            result['data'].append(insert_dict)
        return result

    def convert_datetime_to_timestamp(self, input_str, datetime_format="%Y%m%d%H%M%S"):
        datetime_obj = datetime.datetime.strptime(input_str, datetime_format)
        timestamp_obj = str((int(time.mktime(datetime_obj.timetuple()) * 1000) * 1000000) + 1)
        return timestamp_obj

    def get_device_crash_no(self,file_path):
        return_crash_no = 0
        with open(file_path) as console_log_file_obj:
            file_ctnt = console_log_file_obj.readlines()
            dev_build_id_list = [line.strip() for line in file_ctnt if "CrashReportFound" in line]
            if len(dev_build_id_list) == 1:
                tmp_str = dev_build_id_list[0]
                if tmp_str.find("CrashReportFound") >= 0:
                    if tmp_str.find("CrashReportFound")+65 <= len(tmp_str):
                        crash_no = tmp_str[tmp_str.find("has")+4:tmp_str.find("crashes")]
                    else:
                        crash_no = tmp_str[tmp_str.find("has")+4:tmp_str.find("crashes")]
                    return_crash_no = int(crash_no.strip())
        return return_crash_no

    def get_build_id(self, file_path):
        dev_build_id = "0"
        with open(file_path) as console_log_file_obj:
            file_ctnt = console_log_file_obj.readlines()
            dev_build_id_list = [line.strip() for line in file_ctnt if "Build ID" in line]
            if len(dev_build_id_list) == 1:
                tmp_str = dev_build_id_list[0]
                if tmp_str.find("Build ID") >= 0:
                    if tmp_str.find("Build ID") + 24 <= len(tmp_str):
                        dev_build_id = tmp_str[tmp_str.find("Build ID") + 10:tmp_str.find("Build ID") + 24]
                    else:
                        dev_build_id = tmp_str[tmp_str.find("Build ID") + 10:]
        return dev_build_id

    def get_device_id(self, file_path):
        device_id = "0"
        with open(file_path) as console_log_file_obj:
            file_ctnt = console_log_file_obj.readlines()
            device_id_list = [line.strip() for line in file_ctnt if "Get device with serial" in line]
            if len(device_id_list) == 1:
                tmp_str = device_id_list[0]
                if tmp_str.find("serial") >= 0:
                    if tmp_str.find("serial") + 25 <= len(tmp_str):
                        device_id = tmp_str[tmp_str.find("[") + 1:tmp_str.find("]")]
                    else:
                        device_id = tmp_str[tmp_str.find("[") + 1:tmp_str.find("]")]
        return device_id

    def get_device_info(self, job_detail):
        result = copy.deepcopy(job_detail)
        for build_id in job_detail.keys():
            console_log_path = os.path.join(self.CONSOLE_LOG_DIR, str(build_id), "log")
            result[build_id]['device_id'] = self.get_device_id(console_log_path)
            result[build_id]['build_id'] = self.get_build_id(console_log_path)
            result[build_id]['crash_no'] += self.get_device_crash_no(console_log_path)
            if result[build_id]['device_id'] == "0" or result[build_id]['build_id'] == "0":
                result.pop(build_id)
        return result

    def get_build_detail(self):
        job_detail = {}
        for build_id in self.jenkinsObj[self.INSPECT_JOB_NAME].get_build_ids():
            build_obj = self.jenkinsObj[self.INSPECT_JOB_NAME].get_build(build_id)
            build_date = build_obj.get_timestamp().strftime('%Y-%m-%d')
            if build_date == self.EXPECTED_DATE.strftime('%Y-%m-%d'):
                if build_id not in job_detail.keys():
                    if build_obj.is_running() is False:
                        build_running_secs = build_obj.get_duration().total_seconds()
                        job_detail[build_id] = {'running_secs': build_running_secs, 'crash_no': 1}
        return job_detail



def main():
    bg_obj = BananaGenerator()
    bg_obj.run()

if __name__ == "__main__":
    main()

