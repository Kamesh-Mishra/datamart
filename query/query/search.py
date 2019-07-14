from datetime import datetime
from dateutil.parser import parse
import hashlib
import logging
import os
import pickle
import shutil
import tempfile
import time
import tornado.web

from datamart_augmentation.search import \
    get_joinable_datasets, get_unionable_datasets
from datamart_core.common import Type
from datamart_profiler import process_dataset


logger = logging.getLogger(__name__)


BUF_SIZE = 128000


class ClientError(ValueError):
    """Error in query sent by client.
    """


def parse_keyword_query_main_index(query_json):
    """Parses a DataMart keyword query, turning it into an
    Elasticsearch query over 'datamart' index.
    """

    keywords_query_all = list()
    if 'keywords' in query_json and query_json['keywords']:
        if not isinstance(query_json['keywords'], list):
            raise ClientError("'keywords' must be an array")
        keywords_query = list()
        for name in query_json['keywords']:
            # description
            keywords_query.append({
                'match': {
                    'description': {
                        'query': name,
                        'operator': 'and'
                    }
                }
            })
            # name
            keywords_query.append({
                'match': {
                    'name': {
                        'query': name,
                        'operator': 'and'
                    }
                }
            })
            # keywords
            keywords_query.append({
                'nested': {
                    'path': 'columns',
                    'query': {
                        'match': {
                            'columns.name': {
                                'query': name,
                                'operator': 'and'
                            }
                        },
                    },
                },
            })
            keywords_query.append({
                'wildcard': {
                    'materialize.identifier': '*%s*' % name.lower()
                }
            })
        keywords_query_all.append({
            'bool': {
                'should': keywords_query,
                'minimum_should_match': 1
            }
        })

    return keywords_query_all


def parse_keyword_query_sup_index(query_json):
    """Parses a DataMart keyword query, turning it into an
    Elasticsearch query over 'datamart_column' and
    'datamart_spatial_coverage' indices.
    """

    keywords_query = list()
    if 'keywords' in query_json and query_json['keywords']:
        if not isinstance(query_json['keywords'], list):
            raise ClientError("'keywords' must be an array")
        for name in query_json['keywords']:
            # dataset description
            keywords_query.append({
                'filter': {
                    'match': {
                        'dataset_description': {
                            'query': name,
                            'operator': 'and'
                        }
                    }
                },
                'weight': 10
            })
            # dataset name
            keywords_query.append({
                'filter': {
                    'match': {
                        'dataset_name': {
                            'query': name,
                            'operator': 'and'
                        }
                    }
                },
                'weight': 10
            })
            # column name
            keywords_query.append({
                'filter': {
                    'match': {
                        'name': {
                            'query': name,
                            'operator': 'and'
                        }
                    }
                },
                'weight': 10
            })

    return keywords_query


def parse_query(query_json):
    """Parses a DataMart query, turning it into an Elasticsearch query
    over 'datamart' index as well as the supplementary indices
    ('datamart_columns' and 'datamart_spatial_coverage').
    """

    query_args_main = list()

    # keywords
    keywords_query_main = parse_keyword_query_main_index(query_json)
    query_args_sup = parse_keyword_query_sup_index(query_json)

    if keywords_query_main:
        query_args_main.append(keywords_query_main)

    # tabular_variables
    tabular_variables = []

    # variables
    variables_query = None
    if 'variables' in query_json:
        variables_query = parse_query_variables(
            query_json['variables'],
            tabular_variables=tabular_variables
        )

    # TODO: for now, temporal and geospatial variables are ignored
    #   for 'datamart_columns' and 'datamart_spatial_coverage' indices,
    #   since we do not have information about a dataset in these indices
    if variables_query:
        query_args_main.append(variables_query)

    return query_args_main, query_args_sup, list(set(tabular_variables))


def parse_query_variables(data, tabular_variables=None):
    """Parses the variables of a DataMart query, turning it into an
    Elasticsearch query over 'datamart' index
    """

    output = list()

    if not data:
        return output

    for variable in data:
        if 'type' not in variable:
            raise ClientError("variable is missing property 'type'")
        variable_query = list()

        # temporal variable
        # TODO: handle 'granularity'
        if 'temporal_variable' in variable['type']:
            variable_query.append({
                'nested': {
                    'path': 'columns',
                    'query': {
                        'match': {'columns.semantic_types': Type.DATE_TIME},
                    },
                },
            })
            start = end = None
            if 'start' in variable and 'end' in variable:
                try:
                    start = parse(variable['start']).timestamp()
                    end = parse(variable['end']).timestamp()
                except (KeyError, ValueError, OverflowError):
                    pass
            elif 'start' in variable:
                try:
                    start = parse(variable['start']).timestamp()
                    end = datetime.now().timestamp()
                except (KeyError, ValueError, OverflowError):
                    pass
            elif 'end' in variable:
                try:
                    start = 0
                    end = parse(variable['end']).timestamp()
                except (KeyError, ValueError, OverflowError):
                    pass
            else:
                pass
            if start and end:
                variable_query.append({
                    'nested': {
                        'path': 'columns.coverage',
                        'query': {
                            'range': {
                                'columns.coverage.range': {
                                    'gte': start,
                                    'lte': end,
                                    'relation': 'intersects'
                                }
                            }
                        }
                    }
                })

        # geospatial variable
        # TODO: handle 'granularity'
        elif 'geospatial_variable' in variable['type']:
            if ('latitude1' not in variable or
                    'latitude2' not in variable or
                    'longitude1' not in variable or
                    'longitude2' not in variable):
                continue
            longitude1 = min(
                float(variable['longitude1']),
                float(variable['longitude2'])
            )
            longitude2 = max(
                float(variable['longitude1']),
                float(variable['longitude2'])
            )
            latitude1 = max(
                float(variable['latitude1']),
                float(variable['latitude2'])
            )
            latitude2 = min(
                float(variable['latitude1']),
                float(variable['latitude2'])
            )
            variable_query.append({
                'nested': {
                    'path': 'spatial_coverage.ranges',
                    'query': {
                        'bool': {
                            'filter': {
                                'geo_shape': {
                                    'spatial_coverage.ranges.range': {
                                        'shape': {
                                            'type': 'envelope',
                                            'coordinates':
                                                [[longitude1, latitude1],
                                                 [longitude2, latitude2]]
                                        },
                                        'relation': 'intersects'
                                    }
                                }
                            }
                        }
                    }
                }
            })

        # tabular variable
        # TODO: handle 'relationship'
        #  for now, it assumes the relationship is 'contains'
        elif 'tabular_variable' in variable['type']:
            if 'columns' in variable:
                for column_index in variable['columns']:
                    tabular_variables.append(column_index)

        if variable_query:
            output.append({
                'bool': {
                    'must': variable_query,
                }
            })

    if output:
        return {
            'bool': {
                'must': output
            }
        }
    return {}


def get_augmentation_search_results(es, data_profile,
                                    query_args_main, query_args_sup,
                                    tabular_variables, score_threshold,
                                    dataset_id=None, join=True, union=True):
    join_results = []
    union_results = []

    if join:
        logger.info("Looking for joins...")
        start = time.perf_counter()
        join_results = get_joinable_datasets(
            es=es,
            data_profile=data_profile,
            dataset_id=dataset_id,
            query_args=query_args_sup,
            tabular_variables=tabular_variables
        )
        logger.info("Found %d join results in %.2fs",
                    len(join_results), time.perf_counter() - start)
    if union:
        logger.info("Looking for unions...")
        start = time.perf_counter()
        union_results = get_unionable_datasets(
            es=es,
            data_profile=data_profile,
            dataset_id=dataset_id,
            query_args=query_args_main,
            tabular_variables=tabular_variables
        )
        logger.info("Found %d union results in %.2fs",
                    len(union_results), time.perf_counter() - start)

    min_size = min(len(join_results), len(union_results))
    results = list(zip(join_results[:min_size], union_results[:min_size]))
    results = [elt for sublist in results for elt in sublist]

    if len(join_results) > min_size:
        results += join_results[min_size:]
    if len(union_results) > min_size:
        results += union_results[min_size:]

    for result in results:
        result['supplied_id'] = None
        result['supplied_resource_id'] = None

    return results[:50] # top-50


def get_profile_data(filepath, metadata=None):
    # hashing data
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    hash_ = sha1.hexdigest()

    # checking for cached data
    cached_data = os.path.join('/cache', hash_)
    if os.path.exists(cached_data):
        logger.info("Found cached profile_data")
        with open(cached_data, 'rb') as fp:
            return pickle.load(fp)

    # profile data and save
    logger.info("Profiling...")
    start = time.perf_counter()
    data_profile = process_dataset(filepath, metadata)
    logger.info("Profiled in %.2fs", time.perf_counter() - start)
    with open(cached_data, 'wb') as fp:
        pickle.dump(data_profile, fp)
    return data_profile


class ProfilePostedData(tornado.web.RequestHandler):
    temp_data_path = None

    def handle_data_parameter(self, data):
        """
        Handles the 'data' parameter.

        :param data: the input parameter
        :return: (data_path, data_profile)
          data_path: path to the input data
          data_profile: the profiling (metadata) of the data
        """

        if not isinstance(data, (str, bytes)):
            raise ClientError("The parameter 'data' is in the wrong format")

        if not os.path.exists(data):
            # data represents the entire file
            logger.info("Data is not a path")

            temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
            temp_file.write(data)
            temp_file.close()

            self.temp_data_path = data_path = temp_file.name
            data_profile = get_profile_data(data_path)
        else:
            # data represents a file path
            logger.info("Data is a path")
            if os.path.isdir(data):
                # path to a D3M dataset
                data_file = os.path.join(data, 'tables', 'learningData.csv')
                if not os.path.exists(data_file):
                    raise ClientError("%s does not exist" % data_file)
                else:
                    data_path = data_file
                    data_profile = get_profile_data(data_file)
            else:
                # path to a CSV file
                data_path = data
                data_profile = get_profile_data(data)

        return data_path, data_profile

    def on_finish(self):
        super(ProfilePostedData, self).on_finish()

        if self.temp_data_path is not None:
            os.remove(self.temp_data_path)
