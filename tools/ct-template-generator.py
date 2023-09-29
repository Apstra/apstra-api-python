#
# 2023 Per Abildgaard Toft <p@t1.dk
# Tool to parse and replace uuids from apstra ct template
#
import json
import re
import pprint

TEMPLATE = "templates/k666_ct.json"

uuid_index = 0
id_table = dict()
path = []

def get_uuid_index(id):
    global uuid_index
    global id_ta
    if not id in id_table:
        id_table[id] = "{{" + f"uuid_idx{uuid_index}" + "}}"
        #Increment counter
        uuid_index += 1
    return id_table[id]


def find_id(json):
    if isinstance(json,dict):
        for k,v in json.items():
            path.append(k)
            if k == "id":
                #print(f"Found an ID json path: {str(path)} value: {v}")
                json[k] = get_uuid_index(v)
            if k == "vn_node_id":
                json[k] = "{{vn_node_id}}"
            if k == "rp_to_attach":
                json[k] = "{{rp_to_attach}}"
            find_id(json[k])
            path.pop()
    elif isinstance(json,list):
        for i in json:
            find_id(i)
    # elif isinstance(json, (str,bool,int) ) :
    #     print(f'\t {json}')

if __name__ == '__main__':
    fp = open(TEMPLATE,"r")
    data_json = json.load(fp)
    find_id(data_json)
    fp.close()
    data_str = json.dumps(data_json,indent=2)

    for i in id_table:
        data_str = re.sub(str(i),id_table[i],data_str,count=0, flags=0)

    print("IDs have been replaced with the following uuid tokens")
    for j in id_table.values():
        print(j)

    fp_out = open(TEMPLATE+"_new","w")
    fp_out.write(data_str)
    fp_out.close()