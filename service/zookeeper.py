#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2014,掌阅科技
All rights reserved.

摘    要: zookeeper.py
创 建 者: zhuangshixiong
创建日期: 2015-06-12
说明:     对zookeeper数据操作的简单封装
'''
from kazoo.client import KazooClient
from kazoo.handlers.threading import KazooTimeoutError
from model.db.zd_zookeeper import ZdZookeeper
from conf import log


ZOO_CLIENTS = dict()


class ZookeeperConfError(Exception):
    pass


def get_zoo_client(cluster_name="qconf"):
    """get zoo client by cluster_name
    """
    global ZOO_CLIENTS

    if cluster_name not in ZOO_CLIENTS:
        # get zookeeper hosts info
        zookeeper = ZdZookeeper.one(cluster_name=cluster_name, deleted="0")
        if not zookeeper:
            raise ZookeeperConfError("Zookeeper not configured for cluster: {}!".format(cluster_name))
        # connect to zookeeper
        try:
            client = KazooClient(hosts=zookeeper.hosts,
                                 connection_retry={"max_tries": 3, "backoff": 2})
            client.start(timeout=3)
            ZOO_CLIENTS[cluster_name] = client
        except KazooTimeoutError as exc:
            log.error('Failed to connnect zookeeper, %s', str(exc))
            return

    # check connection's state, if not connected, reconect
    zoo_client = ZOO_CLIENTS[cluster_name]
    if not zoo_client.connected:
        zoo_client.start()
    return zoo_client


def exists(cluster_name, path):
    """check if path node exists
    """
    zoo_client = get_zoo_client(cluster_name)
    return zoo_client.exists(path)


def get(cluster_name, path):
    """get znode in zookeeper
    """
    zoo_client = get_zoo_client(cluster_name)
    data, _ = zoo_client.get(path)
    return data


def get_children(cluster_name, path):
    """get children node in zookeeper with given path
    """
    zoo_client = get_zoo_client(cluster_name)
    return zoo_client.get_children(path)


def delete(cluster_name, path, recursive=False):
    """delete znode on zookeeper
    """
    zoo_client = get_zoo_client(cluster_name)
    zoo_client.delete(path, version=-1, recursive=recursive)


def set_or_create(cluster_name, path, value):
    """set or create znode in zookeepe
    """
    zoo_client = get_zoo_client(cluster_name)
    value = str(value)
    if not zoo_client.exists(path):
        zoo_client.create(path, value)
    else:
        zoo_client.set(path, value)


def get_stat(host):
    """get status of a single node in zookeeper cluster
    """
    cluster_info = dict()
    try:
        zoo_client = KazooClient(
            hosts=host,
            connection_retry={"max_tries": 1, "backoff": 1}
        )
        zoo_client.start(timeout=3)
        cluster_info[host] = zoo_client.command("mntr")
    except KazooTimeoutError as exc:
        log.error('Failed to connnect zookeeper, %s', str(exc))
        cluster_info[host] = str(exc)
    return cluster_info


if __name__ == '__main__':
    pass
