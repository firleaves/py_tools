#!/usr/bin/python
# coding=utf-8

import os
import sys
from optparse import OptionParser 
import re

try:
    import xml.etree.CElementTree as ET
except:
    import xml.etree.ElementTree as ET

from struct import StructDefine,Member,CommonStructContainner,STRUCTDEFINE_KEY
# import struct
print StructDefine
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
                if os.path.isfile(file) :
                    is_proto,key = check_is_need_xml(file)
                    if is_proto:
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
    begin_id = int(id_attrib['begin'])
    end_id = int(id_attrib['end'])

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

def xml2lua(src, lua):

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
    
    write_to_lua(parse_result_dict,lua)
    

def main():
    parser = OptionParser()  
    parser.add_option("-i", "--xml_src",  help="xml files's source path", metavar="directory")  
    parser.add_option("-o", "--lua_file",  help="write to lua file", metavar="file")  
   
    (options, args) = parser.parse_args()  
    # print options,args
    if options.xml_src  and options.lua_file:
        src = os.path.abspath(options.xml_src)
        lua = os.path.abspath(options.lua_file)

        is_check_args = False
        if not os.path.isdir(src):
            print 'pb src path(%s) is not a directory!!! '% src
            is_check_args = True
            is_check_args = True
        if os.path.splitext(lua)[1] != '.lua':
            print 'file extension(%s) is not a lua file !!! '% lua
            is_check_args = True

        if is_check_args == False:
            xml2lua(src, lua)
            

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