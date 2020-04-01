from __future__ import print_function

import logging

import airflow

from airflow.contrib.operators.emr_add_steps_operator import EmrAddStepsOperator
from airflow.contrib.operators.emr_create_job_flow_operator import EmrCreateJobFlowOperator
from airflow.contrib.operators.emr_terminate_job_flow_operator import EmrTerminateJobFlowOperator
from airflow.contrib.sensors.emr_step_sensor import EmrStepSensor
from airflow.hooks.S3_hook import S3Hook


from airflow.operators.python_operator import PythonOperator


execution_date = None

def my_custom_function(ts,**kwargs):

    nonlocal execution_date
    print("execution_date", execution_date)
    execution_date = ts
    print({ts})
    print(execution_date)




tn = PythonOperator(
            task_id='pre_process',
            python_callable=my_custom_function,  # make sure you don't include the () of the function
            op_kwargs={'task_number': task},
            provide_context=True
        )


# Todo setup start time and repeat time
args = {
    'owner': 'airflow',
    'start_date': airflow.utils.dates.days_ago(7),
    'provide_context': True,
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

dag = airflow.DAG(
    'econect_data_extraction',
    schedule_interval='@once',
    default_args=args,
    max_active_runs=1)

# https://docs.aws.amazon.com/emr/latest/APIReference/API_RunJobFlow.html
default_emr_settings = {"Name": "My cluster",
                        "LogUri": "s3n://aws-logs-355521354617-us-east-1/elasticmapreduce/",  # todo: Looks weired
                        "ReleaseLabel": "emr-5.29.0",
                        "Instances": {
                            "InstanceGroups": [
                                {
                                    "Name": "Master nodes",
                                    "Market": "ON_DEMAND",
                                    "EbsConfiguration":{
                                             "EbsBlockDeviceConfigs":[
                                                {
                                                   "VolumeSpecification":{
                                                      "SizeInGB":32,
                                                      "VolumeType":"gp2"
                                                   },
                                                   "VolumesPerInstance":2
                                                }
                                             ]
                                          },
                                    "InstanceRole": "MASTER",
                                    "InstanceType": "m5.xlarge",
                                    "InstanceCount": 1
                                },
                                {
                                    "Name": "Slave nodes",
                                    "EbsConfiguration":{
                                             "EbsBlockDeviceConfigs":[
                                                {
                                                   "VolumeSpecification":{
                                                      "SizeInGB":32,
                                                      "VolumeType":"gp2"
                                                   },
                                                   "VolumesPerInstance":2
                                                }
                                             ]
                                          },
                                    "Market": "ON_DEMAND",
                                    "InstanceRole": "CORE",
                                    "InstanceType": "m5.xlarge",
                                    "InstanceCount": 2
                                }
                            ],
                            "Ec2KeyName": "ec2johnp",
                            "KeepJobFlowAliveWhenNoSteps": True, # todo not sure
                            'EmrManagedMasterSecurityGroup': 'sg-0b7bafb89a5caca6f',
                            'EmrManagedSlaveSecurityGroup': 'sg-09833008bb602825e',
                            'Placement': {
                                'AvailabilityZone': 'us-east-1',
                            },

                        },
                        # "BootstrapActions": [
                        #     {
                        #         'Name': 'pre-process work',
                        #         'ScriptBootstrapAction': {
                        #             'Path': 's3://emma-emr-example/bootstrap_script/bootstrap_cluster.sh' # todo correct place to run code
                        #         }
                        #     }
                        # ],

                        "Applications": [
                            {"Name": "Spark"}, #todo is it required?
                            {"Name": "Hadoop"},
                        ],
                        "VisibleToAllUsers": False, # todo not found
                        "JobFlowRole": "EMR_EC2_DefaultRole", # todo called InstanceProfile?
                        "ServiceRole": "EMR_DefaultRole",
                        # "Tags": [
                        #     {
                        #         "Key": "app",
                        #         "Value": "analytics"
                        #     },
                        #     {
                        #         "Key": "environment",
                        #         "Value": "development"
                        #     }
                        # ]
                        }
# todo: need to be modified
def issue_step(name, args):
    print("issue_step")
    return [
        {
            "Name": name,
            "ActionOnFailure": "CONTINUE",
            "HadoopJarStep": {
                "Jar": "command-runner.jar", # todo https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-commandrunner.html
                "Args": args
            }
        }
    ]

# def check_data_exists():
#     logging.info('checking that data exists in s3')
#     source_s3 = S3Hook()
#     keys = source_s3.list_keys(bucket_name='deutsche-boerse-eurex-pds',
#                                prefix='2018-11-18/')
#     logging.info('keys {}'.format(keys))
#
# check_data_exists_task = PythonOperator(task_id='check_data_exists',
#                                         python_callable=check_data_exists,
#                                         provide_context=False,
#                                         dag=dag)


create_job_flow_task = EmrCreateJobFlowOperator(
    task_id='create_job_flow',
    # emr_conn_id='emr_default',
    job_flow_overrides=default_emr_settings,
    dag=dag
)

run_step = issue_step('spark_run', ["spark-submit", "--deploy-mode", "client",
                                    "--conf", "spark.default.parallelism=6",
                                    "--conf", "spark.driver.cores=4",
                                    "--conf","spark.dynamicAllocation.enabled=true",
                                    "--conf", "spark.shuffle.service.enabled=true",
                                    "--conf", "spark.maxResultSize=8G",
                                    "--conf", "spark.driver.memory=8G",
                                    "--conf", "spark.driver.memoryOverhead=2G",
                                    "--conf", "spark.dynamicAllocation.minExecutors=3",
                                    "--conf", "spark.dynamicAllocation.maxExecutors=9",
                                    "--conf", "spark.executor.memory=8G",
                                    "--conf", "spark.executor.memoryOverhead=2G",
                                    "s3://econet-data-engineering-code/pyspark/econet_data_engineering.py"
                                    "--source", "s3://rheemconnectrawdata/history/",
                                    "--destination_bucket", "s3://rheemconnectrawparquet/polling/"
                                    ])


add_step_task = EmrAddStepsOperator(
    task_id='add_step',
    job_flow_id="{{ task_instance.xcom_pull('create_job_flow', key='return_value') }}",
    # aws_conn_id='aws_default',
    steps=run_step,
    dag=dag
)

watch_prev_step_task = EmrStepSensor(
    task_id='watch_prev_step',
    job_flow_id="{{ task_instance.xcom_pull('create_job_flow', key='return_value') }}",
    step_id="{{ task_instance.xcom_pull('add_step', key='return_value')[0] }}",
    # aws_conn_id='aws_default',
    dag=dag
)

terminate_job_flow_task = EmrTerminateJobFlowOperator(
    task_id='terminate_job_flow',
    job_flow_id="{{ task_instance.xcom_pull('create_job_flow', key='return_value') }}",
    # aws_conn_id='aws_default',
    trigger_rule="all_done",
    dag=dag
)

tn >> create_job_flow_task
#check_data_exists_task >> create_job_flow_task
# create_job_flow_task >> add_step_task
# add_step_task >> watch_prev_step_task
# watch_prev_step_task >> terminate_job_flow_task





