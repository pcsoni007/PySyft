# stdlib
import json
from typing import Optional

# third party
from oblv import OblvClient
from oblv.models import CreateDeploymentInput
import yaml

# relative
from ..core.node.common.exceptions import OblvKeyNotFoundError
from .constants import *
from .model import Client
from .model import DeploymentClient
from .oblv_proxy import create_oblv_key_pair
from .oblv_proxy import get_oblv_public_key

SUPPORTED_REGION_LIST = ["us-east-1",
    "us-west-2",
    "eu-central-1",
    "eu-west-2"]

SUPPORTED_INFRA = ["c5.xlarge","m5.xlarge","r5.xlarge","c5.2xlarge","m5.2xlarge"]

def create_deployment(client: OblvClient, domain_clients: list, deployment_name: Optional[str] = None, key_name: str = "", infra: str = "m5.2xlarge", region: str = "us-east-1") -> str:
    """Creates a new deployment with predefined codebase
    Args:
        client : Oblivious Client.
        domain_clients: List of domain_clients.
        deployment_name: Unique name for the deployment.
        key_name: User's key to be used for deployment creation.
        infra: Represent the AWS infrastructure to be used. Default is "m5.2xlarge". The available options are\n
                - "c5.xlarge" {'CPU':4, 'RAM':8, 'Total/hr':0.68}\n
                - "m5.xlarge" {'CPU':4, 'RAM':16, 'Total/hr':0.768}\n
                - "r5.xlarge" {'CPU':4, 'RAM':32, 'Total/hr':1.008}\n
                - "c5.2xlarge" {'CPU':8, 'RAM':16, 'Total/hr':1.36}\n
                - "m5.2xlarge" {'CPU':8, 'RAM':32, 'Total/hr':1.536}\n
                As of now, PySyft only works with RAM >= 32
        region: AWS Region to be deployed in. Default is "us-east-1". The available options are \n
                - "us-east-1" : "US East (N. Virginia)",\n
                - "us-west-2" : "US West (Oregon)",\n
                - "eu-central-1" : "Europe (Frankfurt)",\n
                - "eu-west-2" : "Europe (London)"
            
    Returns:
        resp: Deployment Client Object
    """
    
    if deployment_name == None:
        deployment_name = input("Kindly provide deployment name")
    if key_name == "":
        key_name = input("Please provide your key name")
        
    while not SUPPORTED_INFRA.__contains__(infra):
        infra = input("Provide infra from one of the following - {}".format(",".join(SUPPORTED_INFRA)))
    while not SUPPORTED_REGION_LIST.__contains__(region):
        region = input("Provide region from one of the following - {}".format(",".join(SUPPORTED_REGION_LIST)))
    try:
        user_public_key = get_oblv_public_key(key_name)
        print("passed ",user_public_key)
    except FileNotFoundError:
        print("creating new one")
        user_public_key = create_oblv_key_pair(key_name)
        print(user_public_key)
    except Exception as e:
        raise Exception(e)
    build_args = {
        "auth": {},
        "users": {
            "domain": [],
            "user": []
        },
        "additional_args": {},
        "infra_reqs": infra,
        "runtime_args": ""
    }
    users = []
    result_client=[]
    runtime_args = []
    for k in domain_clients:
        try:
            users.append({"user_name": k.name, "public key": k.oblv.get_key()})
        except OblvKeyNotFoundError:
            print("Oblv public key not found for {}".format(k.name))
            return
        result_client.append(Client(login=k,datasets=[]))
    build_args["runtime_args"] = yaml.dump({"outbound" : runtime_args})
    build_args["users"]["domain"]=users
    profile = client.user_profile()
    users = [{"user_name": profile.oblivious_login, "public key": user_public_key}]
    build_args["users"]["user"]=users
    depl_input = CreateDeploymentInput(REPO_OWNER, REPO_NAME, VCS,
                                  REF, region, deployment_name, VISIBILITY, True, [], build_args)
    #By default the deployment is in PROD mode
    res = client.create_deployment(depl_input)
    result = DeploymentClient(deployment_id=res.deployment_id, oblv_client = client, domain_clients=domain_clients,user_key_name=key_name)
    return result