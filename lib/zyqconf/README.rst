=======
zyqconf
=======
配置管理系统配套的python客户端

项目描述
--------
- QConf客户端python驱动包的进一步封装，与配置管理系统配套使用
- 使用yaml对配置信息进行序列化，以便支持int和float类型
- 支持python复杂数据结构，dict和list
- 所有配置信息都是只可读，任何会改变配置信息的方法均不支持（dict和list的一些方法因此未提供支持）

项目依赖
--------
- QConf agent
- yaml

版本变更
--------
- v0.0.1
提供基本功能
- v1.0.0
增加钩子功能，方便在通过QConf获取配置失败时执行自定义函数

使用举例
--------

获取配置管理系统的配置::
    import zyqconf

    # 字典节点需要存储特殊值 `DICT_ZNODE`
    dict_conf = zyqconf.DictNode('dict_node_path')
    print dict_conf.get('conf', '')
    print dict_conf.as_dict()

    # 列表节点需要存储特殊值 `LIST_ZNODE`
    list_conf = zyqconf.ListNode('list_node_path')
    print len(list_conf)
    print list_conf.as_list()

通过钩子注册获取配置失败时执行的回调函数::
    import zyqconf

    @zyqconf.hooks.on(zyqconf.HOOK_CONF_ERROR)
    def conf_error(path, exc_info):
        # do whatever you want
        print "conf error, path: {0}\n{1}".format(path, exc_info)
