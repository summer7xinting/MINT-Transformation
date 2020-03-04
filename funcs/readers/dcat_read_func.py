#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging
import time
import requests
from datetime import datetime
from dateutil import parser
from typing import Union, List, Dict, Iterable
from pathlib import Path
from drepr import DRepr
from drepr.models import SemanticModel
from drepr.outputs import ArrayBackend, GraphBackend
from drepr.outputs.array_backend.lst_array_class import LstArrayClass
from drepr.outputs.graph_backend.lst_graph_class import LstGraphClass
from drepr.outputs.base_lst_output_class import BaseLstOutputClass
from drepr.outputs.base_output_class import BaseOutputClass
from drepr.outputs.base_output_sm import BaseOutputSM
import subprocess
from collections import OrderedDict
from drepr.outputs.base_record import BaseRecord
from drepr.outputs.record_id import RecordID

from dtran.argtype import ArgType
from dtran.ifunc import IFunc, IFuncType

DCAT_URL = os.environ['DCAT_URL']
DATA_CATALOG_DOWNLOAD_DIR = os.path.abspath(os.environ['DATA_CATALOG_DOWNLOAD_DIR'])
Path(DATA_CATALOG_DOWNLOAD_DIR).mkdir(exist_ok=True, parents=True)


class DcatReadFunc(IFunc):
    id = "dcat_read_func"
    description = ''' An entry point in the pipeline.
    Fetches a dataset and its metadata from the MINT Data-Catalog.
    '''
    func_type = IFuncType.READER
    friendly_name: str = "Data Catalog Reader"
    inputs = {
        "dataset_id": ArgType.String,
        "start_time": ArgType.DateTime(optional=True),
        "end_time": ArgType.DateTime(optional=True),
        "use_cache": ArgType.Boolean(optional=True)
    }
    outputs = {"data": ArgType.DataSet(None)}
    example = {"dataset_id": "05c43c58-ed42-4830-9b1f-f01059c4b96f"}
    logger = logging.getLogger(__name__)

    def __init__(self,
                 dataset_id: str,
                 start_time: datetime = None,
                 end_time: datetime = None,
                 use_cache: bool = True):
        self.dataset_id = dataset_id
        dataset_result = DCatAPI.get_instance(DCAT_URL).find_dataset_by_id(dataset_id)

        assert ('resource_repr' in dataset_result['metadata']) or ('dataset_repr' in dataset_result['metadata']), \
            "Dataset is missing both 'resource_repr' and 'dataset_repr'"
        assert not (('resource_repr' in dataset_result['metadata']) and ('dataset_repr' in dataset_result['metadata'])), \
            "Dataset has both 'resource_repr' and 'dataset_repr'"

        resource_results = DCatAPI.get_instance(DCAT_URL).find_resources_by_dataset_id(
            dataset_id, start_time, end_time)
        # self.resource_results = resource_results
        # print(len(resource_results))
        resource_ids = {}
        if 'resource_repr' in dataset_result['metadata']:
            self.repr = DRepr.parse(dataset_result['metadata']['resource_repr'])
            for resource in resource_results:
                if start_time or end_time:
                    temporal_coverage = resource['resource_metadata']['temporal_coverage']
                    temporal_coverage['start_time'] = parser.parse(temporal_coverage['start_time'])
                    temporal_coverage['end_time'] = parser.parse(temporal_coverage['end_time'])
                    if (start_time and start_time > temporal_coverage['end_time']) or \
                            (end_time and end_time < temporal_coverage['start_time']):
                        continue

                resource_ids[resource['resource_id']] = resource['resource_data_url']
            self.repr_type = 'resource_repr'
        else:
            # TODO: fix me!!
            assert len(resource_results) == 1
            resource_ids[resource_results[0]
                         ['resource_id']] = resource_results[0]['resource_data_url']
            self.repr = DRepr.parse(dataset_result['metadata']['dataset_repr'])
            self.repr_type = 'dataset_repr'

        if dataset_id == "ea0e86f3-9470-4e7e-a581-df85b4a7075d":
            self.repr = DRepr.parse_from_file(os.environ['HOME_DIR'] + "/examples/d3m/gpm.yml")
            self.logger.info("Overwrite GPM")
        elif dataset_id == "5babae3f-c468-4e01-862e-8b201468e3b5":
            self.repr = DRepr.parse_from_file(os.environ['HOME_DIR'] + "/examples/d3m/gldas.yml")
            self.logger.info("Overwrite GLDAS")

        self.logger.info(f"Found key '{self.repr_type}'")
        self.logger.info(f"Downloading {len(resource_ids)} resources ...")
        self.resources = OrderedDict()
        n_skip = 0
        n_download = 0
        for resource_id, resource_url in resource_ids.items():
            file_full_path = os.path.join(DATA_CATALOG_DOWNLOAD_DIR, f'{resource_id}.dat')
            self.resources[resource_id] = file_full_path
            if use_cache and Path(file_full_path).exists():
                self.logger.debug(f"Skipping resource {resource_id}, found in cache")
                n_skip += 1
                continue
            self.logger.debug(f"Downloading resource {resource_id} ...")
            subprocess.check_call(f'wget {resource_url} -O {file_full_path}', shell=True)
            n_download += 1

        self.logger.info(f"Download Complete. Skip {n_skip} and download {n_download} resources")

    def exec(self) -> dict:
        if self.get_preference("data") is None or self.get_preference("data") == 'array':
            backend = ArrayBackend
        else:
            backend = GraphBackend

        if self.repr_type == 'dataset_repr':
            return {"data": backend.from_drepr(self.repr, list(self.resources.values())[0])}
        else:
            dataset = ShardedBackend(len(self.resources))
            for resource in self.resources.values():
                dataset.add(backend.from_drepr(self.repr, resource, dataset.inject_class_id))
            return {"data": dataset}

    def validate(self) -> bool:
        return True


class ShardedClassID(str):
    def __new__(cls, idx: int, class_id: str):
        return super().__new__(cls, class_id)

    def __init__(self, idx: int, class_id: str):
        self.idx = idx


class ShardedBackend(BaseOutputSM):
    def __init__(self, n_chunks: int):
        # list of datasets in the reverse order
        self.n_chunks = n_chunks
        self.datasets: List[BaseOutputSM] = [None] * n_chunks
        self.count = 0

    @classmethod
    def from_drepr(cls, ds_model: Union[DRepr, str],
                   resources: Union[str, Dict[str, str]]) -> BaseOutputSM:
        raise NotImplementedError("This method should never be called")

    def add(self, dataset):
        self.datasets[self.n_chunks - self.count - 1] = dataset
        self.count += 1

    def inject_class_id(self, class_id: str) -> ShardedClassID:
        return ShardedClassID(self.count, class_id)

    def iter_classes(self) -> Iterable[BaseOutputClass]:
        return (c for d in reversed(self.datasets) for c in d.iter_classes())

    def get_record_by_id(self, rid: RecordID) -> BaseRecord:
        return self.datasets[rid.class_id.idx].get_record_by_id(rid)

    def c(self, class_uri: str) -> BaseLstOutputClass:
        if isinstance(self.datasets[0], ArrayBackend):
            return LstArrayClass(
                [c for d in reversed(self.datasets) for c in d.c(class_uri).classes])
        else:
            return LstGraphClass(
                [c for d in reversed(self.datasets) for c in d.c(class_uri).classes])

    def cid(self, class_id: str) -> BaseOutputClass:
        return self.datasets[class_id.idx].cid(class_id)

    def get_sm(self) -> SemanticModel:
        return self.datasets[0].get_sm()

    def drain(self):
        """
        Iterate and remove the dataset out of the list. After this function, the list of datasets should be empty
        """
        for i in range(len(self.datasets)):
            yield self.datasets.pop()


class DCatAPI:
    instance = None
    logger = logging.getLogger("dcat_api")
    logger_api_resp = logging.getLogger("dcat_api.handle_response")

    def __init__(self, dcat_url: str):
        self.dcat_url = dcat_url
        self.api_key = None

    @staticmethod
    def get_instance(dcat_url: str):
        if DCatAPI.instance is None:
            DCatAPI.instance = DCatAPI(dcat_url)
        return DCatAPI.instance

    def find_resources_by_dataset_id(self,
                                     dataset_id: str,
                                     start_time: datetime = None,
                                     end_time: datetime = None,
                                     limit: int = 100000):
        """start_time and end_time is inclusive"""
        request_headers = {'Content-Type': "application/json", 'X-Api-Key': self.get_api_key()}
        query = {
            "dataset_id": dataset_id,
            "limit": limit,
        }
        if start_time is not None or end_time is not None:
            query['filter'] = {}
            if start_time is not None:
                query['filter']['start_time__gte'] = start_time.isoformat()
            if end_time is not None:
                query['filter']['end_time__lte'] = end_time.isoformat()

        resp = requests.post(f"{self.dcat_url}/datasets/dataset_resources",
                             headers=request_headers,
                             json=query)
        assert resp.status_code == 200, resp.text
        return resp.json()['resources']

    def find_dataset_by_id(self, dataset_id):
        request_headers = {'Content-Type': "application/json", 'X-Api-Key': self.get_api_key()}
        resp = requests.post(f"{self.dcat_url}/datasets/get_dataset_info",
                             headers=request_headers,
                             json={"dataset_id": dataset_id})
        assert resp.status_code == 200, resp.text
        return resp.json()

    def get_api_key(self):
        """
        :return:
        """
        if self.api_key is None or time.time() - self.api_key['time'] > 600:
            # Obtaining the API Key which allows us to make posts
            resp = requests.get(f"{self.dcat_url}/get_session_token").json()
            self.api_key = {'key': resp['X-Api-Key'], "time": time.time()}
        return self.api_key['key']

    @staticmethod
    def handle_api_response(response: requests.Response):
        """
        This is a convenience method to handle api responses
        :param response:
        :param print_response:
        :return:
        """
        parsed_response = response.json()
        DCatAPI.logger_api_resp.debug("API Response: %s", parsed_response)

        if response.status_code == 200:
            return parsed_response
        elif response.status_code == 400:
            raise Exception("Bad request: %s" % response.text)
        elif response.status_code == 403:
            msg = "Please make sure your request headers include X-Api-Key and that you are using correct url"
            raise Exception(msg)
        else:
            now = datetime.utcnow().replace(microsecond=0).isoformat()
            msg = f"""\n\n
            ------------------------------------- BEGIN ERROR MESSAGE -----------------------------------------
            It seems our server encountered an error which it doesn't know how to handle yet. 
            This sometimes happens with unexpected input(s). In order to help us diagnose and resolve the issue, 
            could you please fill out the following information and email the entire message between ----- to
            danf@usc.edu:
            1) URL of notebook (of using the one from https://hub.mybinder.org/...): [*****PLEASE INSERT ONE HERE*****]
            2) Snapshot/picture of the cell that resulted in this error: [*****PLEASE INSERT ONE HERE*****]

            Thank you and we apologize for any inconvenience. We'll get back to you as soon as possible!

            Sincerely, 
            Dan Feldman

            Automatically generated summary:
            - Time of occurrence: {now}
            - Request method + url: {response.request.method} - {response.request.url}
            - Request headers: {response.request.headers}
            - Request body: {response.request.body}
            - Response: {parsed_response}

            --------------------------------------- END ERROR MESSAGE ------------------------------------------
            \n\n
            """

            raise Exception(msg)
