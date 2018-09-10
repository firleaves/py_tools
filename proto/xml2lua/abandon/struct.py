#!/usr/bin/python
# coding=utf-8

import os
# import sys
from typedefine import TypedefineContainer,Typedefine
# import xml.etree.ElementTree as ET
try:
    import xml.etree.CElementTree as ET
except:
    import xml.etree.ElementTree as ET

from common import can_trans_type,STRUCTDEFINE_KEY,TYPEDEFINE_KEY,TYPEDEFINE_KEY,VECTOR_FLAG,MAP_FLAG


class MemberTypeEnum:
    NoneType = 0
    BaseType = 1
    StructType = 2
    ContainerType = 3

class BaseMember:
    '''最基础类型成员'''
    def __init__(self,name,type_des,desc=''):
        self.name = name 
        self.type = type_des
        self.desc = desc
        self.member_type = MemberTypeEnum.None

    def serialize_lua_str(self):
        pass

    def analyze_members(self,typedefine_container,common_struct_container):
        pass


#vector="1" map="2" set="3"
class Member():
    def __init__(self,name,type_des,container_type,desc=''):
        # BaseMember.__init__(self,name,type_des,desc)
        self.name = name 
        self.type = type_des
        
        self.desc = desc
        self.container_type = container_type


        self.member_type = MemberTypeEnum.NoneType
        self.child_member_list = []
        self.client_type = None
        
    def analyze_members(self,common_struct_container,typedefine_container = None):
        ''' 分析出内部所有成员'''
       
        is_base_type,client_type = can_trans_type(self.type)
        
        if self.container_type:
            self.member_type = MemberTypeEnum.ContainerType
            #容器类型
            if is_base_type:
                #是基础类型容器
                member = Member("value",self.type,None)
                member.member_type = MemberTypeEnum.BaseType
                member.client_type = client_type
                self.child_member_list = [member]
            else:
                #结构体容器类型 ,不需要stldefine里面内容
                # type_name,container_type = typedefine_container.get_ori_type(self.name)
                # if type_name:
                #     if container_type == None:
                #         #普通的结构体，直接从common里面寻找复制过来即可
                #         self.member_list =  common_struct_container.get_struct(self.name).member_list
                        
                #     else:
                #         #容器类
                #         self.container_type = container_type
                self.child_member_list =  common_struct_container.get_struct(self.type).member_list
                # self.child_member_list = .child_member_list
                # self.member_list.extend()
        else:
            #结构体
            if not is_base_type:
                self.member_type = MemberTypeEnum.StructType

                # print struct
                self.child_member_list = common_struct_container.get_struct(self.type).member_list

            else:
                #基础类型结构
                self.member_type = MemberTypeEnum.BaseType
                self.client_type = client_type

                
    
            
            
    def serialize_base_type(self,name,base_type,desc):
        lua_str = '\t\t{name = "%s", type = "%s"},'%(name,base_type)
        if desc.strip():
            lua_str+= '--%s'%(desc)
        lua_str += '\n'
        return lua_str 


    def serialize_lua_str(self):
        if self.member_type == MemberTypeEnum.BaseType:
            return self.serialize_base_type(self.name,self.client_type,self.desc)

        elif self.member_type == MemberTypeEnum.StructType:
            #struct直接返回成员继续，无需用table包裹
            lua_str_list = []
            for member in self.child_member_list:
                lua_str_list.append(member.serialize_lua_str())
            return ''.join(lua_str_list)

        elif self.member_type == MemberTypeEnum.ContainerType:
            type_name = ''
            if self.container_type == VECTOR_FLAG:
                type_name = 'vector'
            elif self.container_type == MAP_FLAG:
                type_name = 'map'
            
            lua_str =  '\t{ name = "%s", type = "%s" ,struct =\n\t\t{'%(self.name,type_name)
            if self.desc.strip():
                lua_str += '--%s'%(self.desc)



            member_lua_str_list = []
            lua_str += '\n'
            for member in self.child_member_list:
                member_lua_str_list.append('\t\t\t'+member.serialize_lua_str())

            lua_str +=''.join(member_lua_str_list)+'\t\t}\n\t},\n'
    
            return lua_str
        else:
            print 'type is none  name = %s  ,type =%s '%(self.name,self.type)
           

        if self.container_type == "1":
            type_name = "vector" 





class StructDefine:
    def __init__(self,id,name,desc=''):
        self.id = id
        self.name = name 
        self.desc = desc 
        self.member_list = []
    
    def add_member(self,member):
        self.member_list.append(member)


    def analyze_members(self,common_struct_container,typedefine_container= None):

        for member in self.member_list:
            member.analyze_members(common_struct_container,typedefine_container)


    def serialize_lua_str(self):
        if self.member_list:
            lua_str = '%s = --%s\n{\n\tid = %d,\n\tstruct = \n\t{\n'%(self.name,self.desc,self.id)
            for member in self.member_list:
                lua_str += member.serialize_lua_str()

            lua_str += '\t}\n}'
        else:
            lua_str = '%s = --%s\n{\n\tid = %d,\n\tstruct = {}\n}'%(self.name,self.desc,self.id)
        return lua_str



class CommonStructContainner:
    def __init__(self):
        self.dict = {}

    def add_struct(self,struct):
        self.dict[struct.name] = struct

    def analyze(self,typedefine_container=None):

        for key, struct in self.dict.items():
            # print struct.__class__
            struct.analyze_members(self,typedefine_container)

    def get_struct(self,name):
        return self.dict.get(name,None)

    def dump(self):
        for key,struct in self.dict.items():
            print (struct.id,struct.name)

if __name__ == '__main__':
    # test()
    xmlFilePath = os.path.abspath("./CommonData.xml")
    try:
        tree = ET.parse(xmlFilePath)
        root = tree.getroot()
    except Exception as e:  #捕获除与程序退出sys.exit()相关之外的所有异常
        raise Exception('parse %s fail! error:%s'%(xmlFilePath,e.message))

    common_containner = CommonStructContainner()
    typedefine_containner = TypedefineContainer()
    for child in root:
        if child.tag == STRUCTDEFINE_KEY: 
            for struct_info in child:
                name = struct_info.attrib['name']
                desc = struct_info.attrib.get('desc','')
                struct = StructDefine(0,name,desc)
                for node in struct_info:
                    containerType = node.attrib.get("container")         
                    member_name = node.attrib['name']
                    member_type = node.attrib['type']
                    member_desc = node.attrib['desc']
                    member = Member(member_name,member_type,containerType,member_desc)
                    struct.add_member(member) 
 
                common_containner.add_struct(struct)
        # elif child.tag == TYPEDEFINE_KEY:
        #     for member_info in child:
        #         name = member_info.attrib['name']
        #         desc = member_info.attrib.get('desc','')
        #         type_name = member_info.attrib['type']
        #         container = member_info.attrib.get('container',None)
        #         typedefine = Typedefine(name,type_name,container)
        #         typedefine_containner.add_typedefine(typedefine)

    common_containner.analyze()

    # print common_containner.dict
    lua_str= common_containner.get_struct("PlayerBaseInfo").serialize_lua_str()
    lua_str+= '\n'+common_containner.get_struct("QuestInfo").serialize_lua_str()
    lua_str+='\n'+ common_containner.get_struct("PlayerBaseInfo").serialize_lua_str()
    with open('./struct_test.lua','w+') as fp:
        fp.write(lua_str.encode('utf-8'))