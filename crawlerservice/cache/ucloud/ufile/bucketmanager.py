# -*- coding: utf-8 -*-

from ucloud.logger import logger
from ucloud.auth import Auth
from ucloud.util import _check_dict
from ucloud.ufile import config
from ucloud.ufile.config import UCLOUD_API_URL
from ucloud.ufile.httprequest import _bucket_request, ResponseInfo
from ucloud.compact import s

class BucketManager(object):
    """
    UCloud UFile 空间管理类
    """


    def __init__(self, public_key, private_key):
        """
        初始化 BucketManager 实例

        @param public_key: string类型， 账户API公私钥的公钥
        @param private_key: string类型，账户API公私钥的私钥
        @return None，如果为非法的公私钥则抛出ValueError异常
        """
        self.__auth = Auth(public_key, private_key)


    def set_keys(self, public_key, private_key):
        """
        重新设置账户API公私钥

        @param public_key: string类型， 账户API公私钥的公钥
        @param private_key: string类型，账户API公私钥的私钥
        @return None，如果为非法的公私钥则抛出ValueError异常
        """
        self.__auth.set_keys(public_key, private_key)


    def createbucket(self, bucket, buckettype='private', domainlist=None, header=None):
        """
        创建新的空间

        @param bucket: string类型，空间名称
        @param buckettype: string类型，'private' 或者 'public'
        @param domainlist: list 类型， 要绑定的域名列表
        @param header: dict类型，http 请求header，键值对类型分别为string，比如{'User-Agent': 'Google Chrome'}
        @return ret: 如果http状态码为[200, 204, 206]之一则返回None，否则如果服务器返回json信息则返回dict类型，键值对类型分别为string, unicode string类型，否则返回空的dict
        @return  ResponseInfo: 响应的具体信息，UCloud UFile 服务器返回信息或者网络链接异常
        """

        if header is None:
            header = dict()
        else:
            _check_dict(header)
        if 'User-Agent' not in header:
            header['User-Agent'] = config.get_default('user_agent')
        param = dict()
        param['Action'] = 'CreateBucket'
        param['BucketName'] = bucket
        param['Type'] = buckettype
        if domainlist is None:
            domainlist = []
        for number, item in enumerate(domainlist):
            param['Domain.{0}'.format(number)] = item
        signature = self.__auth.bucket_signature(param)
        param['Signature'] = signature
        logger.info('start create bucket {0}'.format(bucket))
        return _bucket_request(UCLOUD_API_URL, param, header)


    def describebucket(self, bucket=None, offset=0, limit=10, header=None):
        """
        获取空间的信息，如果不提供空间名称，则获取所有空间的信息

        @param bucketname: string类型, 空间名称
        @param offset: integer类型, 起始空间编码，当提供空间名时无效
        @param limit: integer类型，获取空间数量，当提供具体空间名时无效
        @param header: dict类型，http 请求header，键值对类型分别为string，比如{'User-Agent': 'Google Chrome'}
        @return ret: 如果http状态码为[200, 204, 206]之一则返回None，否则如果服务器返回json信息则返回dict类型，键值对类型分别为string, unicode string类型，否则返回空的dict
        @return  ResponseInfo: 响应的具体信息，UCloud UFile 服务器返回信息或者网络链接异常
        """

        if header is None:
            header = dict()
        else:
            _check_dict(header)
        if 'User-Agent' not in header:
            header['User-Agent'] = config.get_default('user_agent')

        param = dict()
        param['Action'] = 'DescribeBucket'
        if bucket is not None:
            param['BucketName'] = bucket
        param['Offset'] = s(str(offset))
        param['Limit'] = s(str(limit))

        signature = self.__auth.bucket_signature(param)
        param['Signature'] = signature
        logger.info('start request the bucket {0} details'.format(bucket))
        return _bucket_request(UCLOUD_API_URL, param, header)

    def updatebucket(self, bucket, buckettype, header=None):
        """
        更新空间的属性

        @param bucket: string类型，空间名称
        @param buckettype: string类型， 'private' 或者 'string'
        @param header: dict类型，http 请求header，键值对类型分别为string，比如{'User-Agent': 'Google Chrome'}
        @return ret: 如果http状态码为[200, 204, 206]之一则返回None，否则如果服务器返回json信息则返回dict类型，键值对类型分别为string, unicode string类型，否则返回空的dict
        @return  ResponseInfo: 响应的具体信息，UCloud UFile 服务器返回信息或者网络链接异常
        """
        if header is None:
            header = dict()
        else:
            _check_dict(header)
        if 'User-Agent' not in header:
            header['User-Agent'] = config.get_default('user_agent')

        param = dict()
        param['Action'] = 'UpdateBucket'
        param['BucketName'] = bucket
        param['Type'] = buckettype

        signature = self.__auth.bucket_signature(param)
        param['signature'] = signature

        return _bucket_request(UCLOUD_API_URL, param, header)

    def deletebucket(self, bucket, header=None):
        """
        删除空间

        @param bucket: string类型，空间名称
        @param header: dict类型，http 请求header，键值对类型分别为string，比如{'User-Agent': 'Google Chrome'}
        @return ret: 如果http状态码为[200, 204, 206]之一则返回None，否则如果服务器返回json信息则返回dict类型，键值对类型分别为string, unicode string类型，否则返回空的dict
        @return  ResponseInfo: 响应的具体信息，UCloud UFile 服务器返回信息或者网络链接异常
        """
        if header is None:
            header = dict()
        else:
            _check_dict(header)
        if 'User-Agent' not in header:
            header['User-Agent'] = config.get_default('user_agent')

        param = dict()
        param['Action'] = 'DeleteBucket'
        param['BucketName'] = bucket

        signature = self.__auth.bucket_signature(param)
        param['Signature'] = signature
        logger.info('start delete bucket {0}'.format(bucket))
        return _bucket_request(UCLOUD_API_URL, param, header)

    def getfilelist(self, bucket, offset=0, limit=20, header=None):
        """
        获取空间中文件列表

        @param bucket: string类型,空间名称
        @param offset: integer类型，文件列表偏移位置
        @param limit: integer类型，返回文件数量
        @return ret: 如果http状态码为[200, 204, 206]之一则返回None，否则如果服务器返回json信息则返回dict类型，键值对类型分别为string, unicode string类型，否则返回空的dict
        @return  ResponseInfo: 响应的具体信息，UCloud UFile 服务器返回信息或者网络链接异常
        """

        if header is None:
            header = dict()
        else:
            _check_dict(header)
        if 'User-Agent' not in header:
            header['User-Agent'] = config.get_default('user_agent')

        param = dict()
        param['Action'] = 'GetFileList'
        param['BucketName'] = bucket
        param['Offset'] = s(str(offset))
        param['Limit'] = s(str(limit))
        signature = self.__auth.bucket_signature(param)
        param['Signature'] = signature
        logger.info('start request the file list of bucket {0}'.format(bucket))
        return _bucket_request(UCLOUD_API_URL, param, header)
