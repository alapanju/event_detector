import xml.etree.ElementTree as ET
import pickle, re, sys, os
from lxml import etree
import xml_parse
from xml.dom import minidom

'''
EVENT_MAP={'None': 0, 'personnel.nominate': 1, 'contact.phonewrite': 27, 'business.declarebankruptcy': 3,
           'justice.releaseparole': 4, 'justice.extradite': 5, 'personnel.startposition': 22,
           'justice.fine': 7, 'transaction.transfermoney': 8, 'personnel.endposition': 9,
           'justice.acquit': 10, 'life.injure': 11, 'conflict.attack': 12, 'justice.arrestjail': 13,
           'justice.pardon': 14, 'justice.chargeindict': 15, 'conflict.demonstrate': 16,
           'contact.meet': 17, 'business.endorg': 18, 'life.beborn': 19, 'personnel.elect': 20, 
           'justice.trialhearing': 21, 'life.divorce': 6, 'justice.sue': 23, 'justice.appeal': 24,
           'business.mergeorg': 32, 'life.die': 26, 'business.startorg': 2, 'justice.convict': 28,
           'movement.transport': 29, 'life.marry': 30, 'unknown': 34, 'justice.sentence': 31,
           'justice.execute': 25, 'transaction.transferownership': 33}'''

N_EVENT_MAP={'None': 0, 'business.declarebankruptcy': 1, 'business.endorg': 2, 'business.mergeorg': 3, 'business.startorg': 4, 'conflict.attack': 5, 'conflict.demonstrate': 6, 'contact.broadcast': 7, 'contact.contact': 8, 'contact.correspondence': 9, 'contact.meet': 10, 'justice.acquit': 11, 'justice.appeal': 12, 'justice.arrestjail': 13, 'justice.chargeindict': 14, 'justice.convict': 15, 'justice.execute': 16, 'justice.extradite': 17, 'justice.fine': 18, 'justice.pardon': 19, 'justice.releaseparole': 20, 'justice.sentence': 21, 'justice.sue': 22, 'justice.trialhearing': 23, 'life.beborn': 24, 'life.die': 25, 'life.divorce': 26, 'life.injure': 27, 'life.marry': 28, 'manufacture.artifact': 29, 'movement.transportartifact': 30, 'movement.transportperson': 31, 'personnel.elect': 32, 'personnel.endposition': 33, 'personnel.nominate': 34, 'personnel.startposition': 35, 'transaction.transaction': 36, 'transaction.transfermoney': 37, 'transaction.transferownership': 38}

ace_path = "../ace_2005_td_v7/data/English/"
# tests = "../nw/source/NYT_ENG_20131130.0062.xml"

def read_file(source_path, ere_path):
    apf_tree = ET.parse(ere_path)
    root = apf_tree.getroot()
    
    event_start = {}
    event_end = {}

    event_ident = {}
    event_map = {}
    event = dict()

    for events in root.iter("hopper"):
        for mention in events.iter("event_mention"):
            ev_type = mention.attrib["type"] + "." + mention.attrib["subtype"]
            ev_id = mention.attrib["id"]
            trigger = mention.find("trigger")
            start = int(trigger.attrib["offset"])
            end = int(trigger.attrib["length"]) + 2 + start
            text = re.sub(r"\n", r"", trigger.text)
            event_tupple = (ev_type, start, end, text)
            if event_tupple in event_ident:
                sys.stderr.write("duplicate event {}\n".format(ev_id))
                event_map[ev_id] = event_ident[event_tupple]
                continue
            event_ident[event_tupple] = ev_id
            event[ev_id] = [ev_id, ev_type, start, end, text]
            event_start[start] = ev_id
            event_end[end] = ev_id

    if "ENG_NW" in source_path:
        #print("Entered nw")
        source_tree = ET.parse(source_path)
        source_root = source_tree.getroot()
        doc_id = source_root.attrib["id"]
        # doc_type, date_time, fields can be missing
        doc_type= ""
        date_time = source_root.find("DATE_TIME").text
        text = source_root.find("TEXT").text.replace("\n", " ")

        try:
            head_line = source_root.find("HEADLINE").replace("\n", " ")
            sub = len(doc_id) + len(doc_type) + len(date_time) + len(head_line) + 8
        except:
            sub = len(doc_id) + len(doc_type) + len(date_time) + 6
        tokens, anchors = read_document(text, sub,event_start, 
                                        event_end, event_ident, event_map, event)
        return [tokens], [anchors]

    elif "NYT_ENG" in source_path:
        #print("Entered nw")
        source_tree = ET.parse(source_path)
        source_root = source_tree.getroot()
        doc_id = source_root.attrib["id"]
        doc_type = source_root.attrib["type"]
        date_time = ""
        text=""
        for item in source_root.iter("P"):
            text += item.text
        text = text.replace("\n", " ")

        #text = source_root.find("TEXT").text.replace("\n", " ")

        try:
            head_line = source_root.find("HEADLINE").replace("\n", " ")
            sub = len(doc_id) + len(doc_type) + len(date_time) + len(head_line) + 8
        except:
            sub = len(doc_id) + len(doc_type) + len(date_time) + 6
        tokens, anchors = read_document(text, sub,event_start,
                                        event_end, event_ident, event_map, event)
        return [tokens], [anchors]


def read_document(doc, sub, event_start, event_end, event_ident, event_map, event):
    regions = []
    tokens = []
    anchors = []
    check= 0
    offset = 0
    current = 0
    for i in range(len(doc)):
        if i+sub in event_start:
            inc = 0
            new = clean_str(doc[current:i])
            regions.append(new)
            tokens += new.split()
            check = 1
            anchors += [0 for _ in range(len(new.split()))]
            inc = 0
            current = i
            ent = event_start[i+sub]
            event[ent][2] += offset + inc
        if i+sub in event_end:
            ent = event_end[i+sub]
            event[ent][3] += offset
            new = clean_str(doc[event[ent][2]-sub : event[ent][3]-sub])
            assert new.replace(" ", "") == event[ent][4] or new == event[ent][4] or new.replace(" ","_")\
            ,"loi text: " + new + " ," + event[ent][4] +" " + str(event[ent][2]-sub) + " " + str(event[ent][3]-sub)
            regions.append(new)
            tokens += [new.replace(" ", "")]

            try:
                anchors += [N_EVENT_MAP[event[ent][1]]]
            except KeyError:
                print("KeyError for : ", event[ent][1]) 
                anchors += [N_EVENT_MAP["None"]]
            offset += inc
            current = i 

    new = clean_str(doc[current : ])
    regions.append(new)
    tokens += new.split()
    anchors += [0 for _ in range(len(new.split()))]
    #print(anchors)
    doc = "".join(regions)
    assert len(tokens) == len(anchors),"Anchors length not equal to Tokens length"
    return tokens, anchors

def encode_corpus(folder_path):
    file_list_path = os.path.join(folder_path, "source")
    files = os.listdir(file_list_path)
    files = [item[:-4] for item in files]

    # Printing the list of the files in the directory
    with  open("dir_list_of_ids.txt", "w") as files_dir_list:
        for file_name in files:
            files_dir_list.write("%s\n" % file_name)

    return files

def read_corpus(folder_path):
    count = 0
    file_list = encode_corpus(folder_path)
    tokens, anchors = [], []
    # For testing purpose, limiting to 5
    for file in file_list:
        source_path = os.path.join(folder_path, 'source', file)
        ere_path = os.path.join(folder_path, 'ere', file)
        # tok, anc = read_file(file_path + ".apf.xml", file_path + ".sgm")
        tok, anc = read_file(source_path + ".xml", ere_path + ".rich_ere.xml")
        count += 1
        tokens += tok
        anchors += anc
    #print(count, len(event_type))
    return tokens, anchors

def clean_str(string, TREC=False):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Every dataset is lower cased except for TREC
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)  
    string = re.sub(r"\'m", r" 'm", string)
    string = re.sub(r"\'s", " \'s", string) 
    string = re.sub(r"\'ve", " \'ve", string) 
    string = re.sub(r"n\'t", " n\'t", string) 
    string = re.sub(r"\'re", " \'re", string) 
    string = re.sub(r"\'d", " \'d", string) 
    string = re.sub(r"\'ll", " \'ll", string) 
    string = re.sub(r"\.", " <dot>", string)
    string = re.sub(r"\,", r" <dot> ", string) 
    string = re.sub(r"!", " <dot> ", string) 
    string = re.sub(r"\(", " <dot> ", string) 
    string = re.sub(r"\)", " <dot> ", string) 
    string = re.sub(r"\?", " <dot> ", string) 
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip() if TREC else string.strip().lower()

if __name__ == "__main__":
    #test = r"/home/jeovach/PycharmProjects/ed_ace/ace_2005_td_v7/data/English/nw/fp2/AFP_ENG_20030630.0741"
    #read_file(test+".apf.xml", test+".sgm", event_type = [])
    #tokens, anchors  = read_corpus("../ace_2005_td_v7/data/English/bn")
    tokens, anchors = read_corpus("../nw")
    #print(tokens)
    #tokens += t
    #anchors += a
    pickle.dump(tokens, open("../tokens1.bin","wb"))
    pickle.dump(anchors, open("../anchors1.bin", "wb"))

    """
    t, a = read_corpus(
        "../ace_2005_td_v7/data/English/bc")
    tokens = t
    anchors = a
    pickle.dump(tokens, open("tokens2.bin","wb"))
    pickle.dump(anchors, open("anchors2.bin", "wb"))

    t, a = read_corpus(
        "../ace_2005_td_v7/data/English/cts")
    tokens = t
    anchors = a
    pickle.dump(tokens, open("tokens3.bin","wb"))
    pickle.dump(anchors, open("anchors3.bin", "wb"))
    t, a = read_corpus(
        "../ace_2005_td_v7/data/English/wl")
    tokens = t
    anchors = a
    pickle.dump(tokens, open("../tokens2.bin","wb"))
    pickle.dump(anchors, open("../anchors2.bin", "wb"))"""

