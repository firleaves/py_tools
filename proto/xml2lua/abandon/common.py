#!/usr/bin/python
# coding=utf-8
CONTAINER_KEY = "ContainerInfo"
STRUCTDEFINE_KEY = "structDefine"
TYPEDEFINE_KEY = "stlDefine"
VECTOR_FLAG = '1'
MAP_FLAG = '2'

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



def can_trans_type(type_des):
    type_upper = type_des.upper()
    # type_upper = type_des
    for server_type,client_type in SC_TYPE.items():
        if server_type == type_upper:
            return True,client_type
    
    return False,None