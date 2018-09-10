#!/usr/bin/python
# coding=utf-8

import os
import sys
from optparse import OptionParser 
import re

# PROTO_FILE_EXTENSION = ".proto"

S2C_KEY = "S2C"
C2S_KEY = "C2S"
KEY_INDEX_DICT = {
    "cs": S2C_KEY,
    "sc":C2S_KEY
}

def check_is_need_proto(proto_file):
    ret = re.findall(r'([cs]+)_.+.proto',proto_file)
    if len(ret) >0:
        return True ,ret[0]
    return False,None

def get_all_proto_fils(path):
    file_dict = {
        S2C_KEY:[],
        C2S_KEY:[]
    }
    for parent, _, file_names in os.walk(path):
            for file in file_names:
                if os.path.isfile(file) :
                    is_proto,key = check_is_need_proto(file)
                    if is_proto:
                        file_dict[KEY_INDEX_DICT[key]].append(os.path.join(parent, file))
    return file_dict

def parse_proto_file(file):
    id_key_tuple_list = {}
    with open(file,"r") as fp:
        context = fp.read()
        id_key_tuple_list = re.findall(r'//\s*\[(\d+)\]\s*(.+)\s+message\s+(\S+)\s+',context)
        # print id_key_tuple_list
    return id_key_tuple_list

def write_parse_result_to_lua_file(parse_result_dict,file):
    if not parse_result_dict[S2C_KEY] and not parse_result_dict[C2S_KEY]:
        return 
    lua_str = 'local Protocol = {}\n'
    lua_end_str = r''' 
--下面只是为了快速索引，无需修改
if not Protocol.C2SIdKeyT and type(Protocol.C2S) == "table" then 
    Protocol.C2SIdKeyT = {}
    for k,v in pairs(Protocol.C2S) do 
        if not v.Id or not v.Key then 
            error(string.format("Protocol.C2S  [%s] don't have Id/Key ,plase check this file",k))
            break
        end 
        if Protocol.C2SIdKeyT[v.Id] then 
            error(string.format("Protocol.C2S has same id(%d) protocol,plase check this file",v.Id))
            break
        end 
        Protocol.C2SIdKeyT[v.Id] = v.Key
    end 
end 

function Protocol.GetC2SKeyById(id)
    return Protocol.C2SIdKeyT[id]
end 


if not Protocol.S2CIdKeyT and type(Protocol.S2C) == "table" then 
    Protocol.S2CIdKeyT = {}
    for k,v in pairs(Protocol.S2C) do
        if not v.Id or not v.Key then 
            error(string.format("Protocol.S2C  [%s] don't have Id/Key ,plase check this file",k))
            break
        end  
        if Protocol.S2CIdKeyT[v.Id] then 
            error(string.format("Protocol.S2C has same id(%d) protocol,plase check this file",v.Id))
            break
        end 
        Protocol.S2CIdKeyT[v.Id] = v.Key
    end 
end 


function Protocol.GetS2CKeyById(id)
    return Protocol.S2CIdKeyT[id]
end 

return Protocol 
    '''
    s2c_str = '\nProtocol.S2C = {\n'
    c2s_str = '\nProtocol.C2S = {\n'
    with open(file,"w+") as fp:
        for key,result_list in parse_result_dict.items():
            for result_tuple in result_list:
                
                message_id = result_tuple[0]
                comment = result_tuple[1]
                message_key = result_tuple[2]

                if key == S2C_KEY:
                    s2c_str = s2c_str + ('\t%s = { Id = %s, Key = "%s"},--%s\n' % (message_key,message_id,message_key,comment))
                elif key == C2S_KEY:
                    c2s_str = c2s_str + ('\t%s = { Id = %s, Key = "%s"},--%s\n'%(message_key,message_id,message_key,comment))
        s2c_str = s2c_str + '}\n'
        c2s_str = c2s_str + '}\n'
    
        lua_str = lua_str + s2c_str + c2s_str + lua_end_str
        fp.write(lua_str)
        print 'generate %s file success'%file




def gen(pb_src,lua_file):
    
    proto_files_path = os.path.abspath(".")
    file_dict = get_all_proto_fils(pb_src)
    
    parse_result_dict = {
        S2C_KEY:[],
        C2S_KEY:[]
    }
    for key, file_list in file_dict.items():
        for file in file_list:
            parse_result_dict[key].extend(parse_proto_file(file))

    # print parse_result_dict
    write_parse_result_to_lua_file(parse_result_dict,os.path.join(proto_files_path,lua_file))





def main():
    parser = OptionParser()  
    parser.add_option("-i", "--pb_src",  help="pb files's source path", metavar="directory")  
    parser.add_option("-o", "--lua_file",  help="write to lua file", metavar="file")  
   
    (options, args) = parser.parse_args()  
    # print options,args
    if options.pb_src  and options.lua_file:
        src = os.path.abspath(options.pb_src)
        lua = os.path.abspath(options.lua_file)
        print(src)
        print lua
        is_check_args = False
        if not os.path.isdir(src):
            print 'pb src path(%s) is not a directory!!! '% src
            is_check_args = True
            is_check_args = True
        if os.path.splitext(lua)[1] != '.lua':
            print 'file extension(%s) is not a lua file !!! '% lua
            is_check_args = True

        if is_check_args == False:
            gen(src, lua)
            

    else:
        print "input args error:"
        parser.print_help()


if __name__ == '__main__':
    main()