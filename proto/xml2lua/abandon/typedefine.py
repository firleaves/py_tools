#!/usr/bin/python
# coding=utf-8

import os
import sys
# import 

#废弃

class Typedefine:
    def __init__(self,cur_type,ori_type,container_type = None):
        self.ori_type = ori_type
        self.cur_type = cur_type
        self.container_type = container_type

class TypedefineContainer:
    def __init__(self):
        self.typedefine_dict = {}

    def add_typedefine(self,typedefine):
        #默认typedefine 命名不重复，如有重复，需要修改
        self.typedefine_dict[typedefine.cur_type] = typedefine

    def get(self,type,default = None):
        return self.typedefine_dict.get(type,default)

    def get_ori_type(self,type):
        typedefine = self.get(type)
        if typedefine:
            return typedefine.ori_type,typedefine.container_type
        return None,None

    def get_all_container_type(self,type_name,container_type,name_list = None):
        '''多层容器嵌套的时候，需要查询到最底层结构名
            暂不需要，只是测试
        '''
        if not name_list:
            name_list = []
        name = self.get(type_name)
        if name and name.container_type == container_type:
            name_list.append(name.ori_type)
            return self.get_all_container_type(name.ori_type,container_type,name_list)
        else:
            return name_list


if __name__ == '__main__':
    type_container = TypedefineContainer()
    type_container.add_typedefine(Typedefine("BaseVec3","BaseVec2",1))
    type_container.add_typedefine(Typedefine("BaseVec2","BaseVec1",1))
    type_container.add_typedefine(Typedefine("BaseVec1","BaseVec",2))    
    print type_container.get_all_container_type("BaseVec3",1)