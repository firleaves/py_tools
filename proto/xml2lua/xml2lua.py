#!/usr/bin/python
# coding=utf-8

import os
# import sys
from optparse import OptionParser 
import re

# import xml.etree.ElementTree as ET
try:
    import xml.etree.CElementTree as ET
except:
    import xml.etree.ElementTree as ET
import copy

CONTAINER_KEY = "ContainerInfo"
STRUCTDEFINE_KEY = "structDefine"
TYPEDEFINE_KEY = "stlDefine"
VECTOR_FLAG = '1'
MAP_FLAG = '2'
BEGIN_KEY = 'begin'
END_KEY ="end"

SC_TYPE = {
    "INT8":"byte",
    "UINT8":"char",
    "INT16":"short",
    "UINT16":"ushort",
    "INT32":"int",
    "UINT32":"uint",
    "INT64":"long",
    "UINT64":"ulong",
    "STRING":"string"
}

TAB_APSCE = 2

def can_trans_type(type_des):
    type_upper = type_des.upper()
    # type_upper = type_des
    for server_type,client_type in SC_TYPE.items():
        if server_type == type_upper:
            return True,client_type
    
    return False,None

def get_tab_str(tab_count):
    tab_str = ''
    if tab_count < 1:
        return tab_str 
    
    for i in range(0,tab_count):
        tab_str += '\t'
    return tab_str


class MemberTypeEnum:
    NoneType = 0
    BaseType = 1
    StructType = 2
    ContainerType = 3

# class BaseMember:
#     '''最基础类型成员'''
#     def __init__(self,name,type_des,desc=''):
#         self.name = name 
#         self.type = type_des
#         self.desc = desc
#         self.member_type = MemberTypeEnum.NoneType
#         #默认从2个tab开始
#         self.tab_count = 2

#     def serialize_lua_str(self):
#         pass

#     def analyze_members(self,typedefine_container,common_struct_container):
#         pass


#vector="1" map="2" set="3"
class Member():
    def __init__(self,name,type_des,container_type,desc=''):
        # BaseMember.__init__(self,name,type_des,desc)
        self.name = name 
        self.type = type_des
        
        self.desc = desc
        self.container_type = container_type

        self.tab_count = 3
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
                #
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
                self.child_member_list =  copy.deepcopy(common_struct_container.get_struct(self.type).member_list)
                # self.child_member_list = .child_member_list
                # self.member_list.extend()
        else:
            #结构体
            if not is_base_type:
                self.member_type = MemberTypeEnum.StructType

                # print struct
                self.child_member_list = copy.deepcopy(common_struct_container.get_struct(self.type).member_list)

            else:
                #基础类型结构
                self.member_type = MemberTypeEnum.BaseType
                self.client_type = client_type


        #刷新内部成员tab数量
        self.analyze_members_tab_count()



    def analyze_members_tab_count(self,parent_member_type= None):
        if self.member_type == MemberTypeEnum.StructType and parent_member_type == MemberTypeEnum.ContainerType:
            for member in self.child_member_list:
                member.tab_count = self.tab_count
                member.analyze_members_tab_count(self.member_type)

        if self.member_type == MemberTypeEnum.ContainerType:
            for member in self.child_member_list:
                member.tab_count = self.tab_count+TAB_APSCE
                member.analyze_members_tab_count(self.member_type)
            
    def serialize_base_type(self,name,base_type,desc,tab_count):
        tab_str = get_tab_str(tab_count)
        lua_str = '%s{ name = "%s", type = "%s" },'%(tab_str,name,base_type)
        if desc.strip():
            lua_str+= '--%s'%(desc)
        lua_str += '\n'
        return lua_str 


    def serialize_lua_str(self):
       
        if self.member_type == MemberTypeEnum.BaseType:
            return self.serialize_base_type(self.name,self.client_type,self.desc,self.tab_count)

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
            
            tab_str = get_tab_str(self.tab_count)
            tab_str2 = get_tab_str(self.tab_count+1)
            # print ("name = %s,tab_count = %d,|%s|"%(self.name,self.tab_count,tab_str))
            lua_str =  '%s{ name = "%s", type = "%s" ,struct ='%(tab_str,self.name,type_name)
            if self.desc.strip():
                lua_str += '--%s'%(self.desc)
            member_lua_str_list = []
            lua_str += '\n%s{\n'%(tab_str2)
            for member in self.child_member_list:
                member_lua_str_list.append(member.serialize_lua_str())

            lua_str +=''.join(member_lua_str_list)+'%s}\n%s},\n'%(tab_str2,tab_str)
    
            return lua_str
        else:
            print 'type is none  name = %s  ,type =%s '%(self.name,self.type)

class StructDefine:
    def __init__(self,id,name,desc=''):
        self.id = id
        self.name = name 
        self.desc = desc 
        self.member_list = []
        self.tab_count = 1
    
    def add_member(self,member):
        self.member_list.append(member)


    def analyze_members(self,common_struct_container,typedefine_container= None):

        for member in self.member_list:
            member.analyze_members(common_struct_container,typedefine_container)


    def serialize_lua_str(self):
        tab_str = get_tab_str(self.tab_count)
        tab_str2 = get_tab_str(self.tab_count+1)
        if self.member_list:
            lua_str = '%s%s = --%s\n%s{\n%sid = %d,\n%sstruct = \n%s{\n'%(tab_str,self.name,self.desc,tab_str,tab_str2,self.id,tab_str2,tab_str2)
            for member in self.member_list:
                lua_str += member.serialize_lua_str()

            lua_str += '%s}\n%s}'%(tab_str2,tab_str)
        else:
            lua_str = '%s%s = --%s\n%s{\n%sid = %d,\n%sstruct = {}\n%s}'%(tab_str,self.name,self.desc,tab_str,tab_str2,self.id,tab_str2,tab_str)
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

S2C_KEY = "S2C"
C2S_KEY = "C2S"
KEY_INDEX_DICT = {
    "cs": C2S_KEY,
    "sc":S2C_KEY
}


def check_is_need_xml(proto_file):
    ret = re.findall(r'([cs]+)_.+.xml',proto_file)
    if len(ret) >0:
        return True ,ret[0]
    return False,None

def get_xml_fils(path):
    file_dict = {
        S2C_KEY:[],
        C2S_KEY:[]
    }
    for parent, _, file_names in os.walk(path):
            for file in file_names:
                if os.path.isfile(os.path.join(parent,file)) :
                    is_proto,key = check_is_need_xml(file)
                    # print file,is_proto,key
                    if is_proto:
                        # print file
                        file_dict[KEY_INDEX_DICT[key]].append(os.path.join(parent, file))
    return file_dict


def parse_common(src):
    xmlFilePath = os.path.join(src,"CommonData.xml")
    try:
        tree = ET.parse(xmlFilePath)
        root = tree.getroot()
    except Exception as e:  #捕获除与程序退出sys.exit()相关之外的所有异常
        raise Exception('parse %s fail! error:%s'%(xmlFilePath,e.message))

    common_containner = CommonStructContainner()
    # typedefine_containner = TypedefineContainer()
    for child in root:
        if child.tag == STRUCTDEFINE_KEY: 
            for struct_info in child:
                # print struct_info.attrib
                name = struct_info.attrib['name']
                desc = struct_info.attrib.get('desc','')
                struct = StructDefine(0,name,desc)
                for node in struct_info:
                    container_type = node.attrib.get("container")         
                    member_name = node.attrib['name']
                    member_type = node.attrib['type']
                    member_desc = node.attrib.get('desc')
                    member = Member(member_name,member_type,container_type,member_desc)
                    struct.add_member(member) 
 
                common_containner.add_struct(struct)
    common_containner.analyze()
    return common_containner


def parse_proto_xml(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
    except Exception as e:  #捕获除与程序退出sys.exit()相关之外的所有异常
        raise Exception('parse %s fail! error:%s'%(file,e.message))

    id_attrib = root.find("protoId").attrib
    begin_id = int(id_attrib[BEGIN_KEY])
    end_id = int(id_attrib[END_KEY])

    cur_message_id = begin_id
    message_list = []
    for proto in root.iter("proto"):
        name = proto.attrib['name']
        desc = proto.attrib.get('desc')
        # print proto.attrib
        struct = StructDefine(cur_message_id,name,desc)
        for node in proto:
            
            container_type = node.attrib.get("container")
            member_name = node.attrib['name']
            member_type = node.attrib['type']
            member_desc = node.attrib.get('desc')
            member = Member(member_name,member_type,container_type,member_desc)
            struct.add_member(member) 

        message_list.append(struct)
        cur_message_id +=1

    if cur_message_id >= end_id:
        raise Exception("%s  message id(%d) out of range(%d-%d) "%(cur_message_id,begin_id,end_id))

    return message_list

def write_to_lua(parse_result_dict,file):

    lua_str = 'local Protocol = {}\n'
    s2c_str = '\nProtocol.S2C = \n{\n'
    c2s_str = '\nProtocol.C2S = \n{\n'
    
    for key,proto_list in parse_result_dict.items():
        for proto in proto_list:
            if key == S2C_KEY:
                s2c_str += proto.serialize_lua_str()+',\n'
            elif key == C2S_KEY:
                c2s_str += proto.serialize_lua_str()+',\n'
    s2c_str = s2c_str + '}\n'
    c2s_str = c2s_str + '}\n'
    
    lua_str +=  s2c_str + c2s_str + "\n return Protocol"
    with open(file,"w+") as fp:
        fp.write(lua_str.encode('utf-8'))
    
    print "proto xml to lua success!!!"


def parse_error_code(src,file):
    xmlFilePath = os.path.join(src,"Enum_ErrorCode.xml")
    try:
        tree = ET.parse(xmlFilePath)
        root = tree.getroot()
    except Exception as e:  #捕获除与程序退出sys.exit()相关之外的所有异常
        raise Exception('parse %s fail! error:%s'%(file,e.message))

    cur_error_id = 0

    # error_dict = {}
    lua_str = 'local ErrorCdoe = {\n '
    for error_message in root.iter("member"):
        error_name = error_message.attrib["name"]
        error_id = error_message.attrib.get("value",None)
        if error_id:
            cur_error_id = int(error_id)
        error_desc = error_message.attrib.get("desc",'')

        lua_str += '\t[%d] = "%s", --%s\n'%(cur_error_id,error_desc,error_name)
        cur_error_id += 1 

    lua_str +=  "}\n\n return ErrorCdoe"
    with open(file,"w+") as fp:
        fp.write(lua_str.encode('utf-8'))
    
    print "proto error_code to lua success!!!"


def xml2lua(src, protocol_lua,error_code_lua):
    #解析生成错误码
    parse_error_code(src,error_code_lua)


    #第一个解析common
    common_containner = parse_common(src)
    # common_containner.dump()

    xml_file_dict = get_xml_fils(src)
    parse_result_dict = {
        S2C_KEY:[],
        C2S_KEY:[]
    }
    for key, file_list in xml_file_dict.items():
        for file in file_list:
            parse_result_dict[key].extend(parse_proto_xml(file))

    for key,proto_list in parse_result_dict.items():
        for proto in proto_list:
            proto.analyze_members(common_containner)
    
    write_to_lua(parse_result_dict,protocol_lua)
    

def main():
    parser = OptionParser()  
    parser.add_option("-i", "--xml_src",  help="xml files's source path", metavar="directory")  
    parser.add_option("-p", "--proto_file",  help="write to lua file", metavar="file")  
    parser.add_option("-e", "--error_file",  help="write to lua file", metavar="file")  
   
    (options, args) = parser.parse_args()  
    print options,args
    if options.xml_src  and options.proto_file and options.error_file:
        src = os.path.abspath(options.xml_src)
        protocol_lua = os.path.abspath(options.proto_file)
        error_code_lua = os.path.abspath(options.error_file)

        is_check_args = False
        if not os.path.isdir(src):
            print 'pb src path(%s) is not a directory!!! '% src
            is_check_args = True
        if os.path.splitext(protocol_lua)[1] != '.lua':
            print 'file extension(%s) is not a lua file !!! '% protocol_lua
            is_check_args = True
        if os.path.splitext(error_code_lua)[1] != '.lua':
            print 'file extension(%s) is not a lua file !!! '% error_code_lua
            is_check_args = True

        if is_check_args == False:
            xml2lua(src, protocol_lua,error_code_lua)
            

    else:
        print "input args error:"
        parser.print_help()


if __name__ == '__main__':
    main()
    # try:
    #     tree = ET.parse(os.path.abspath("./cs_hall.xml"))
    #     root = tree.getroot()
    # except Exception as e:  #捕获除与程序退出sys.exit()相关之外的所有异常
    #     raise Exception('parse %s fail! error:%s'%(file,e.message))

    # for proto in root.iter("proto"):
    #     print proto.attrib 

    # print len(parse_proto_xml(os.path.abspath("./cs_hall.xml")))