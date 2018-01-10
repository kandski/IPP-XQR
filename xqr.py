#!/usr/bin/python3
import sys
import argparse
import xml.dom.minidom as mdom
import re
import operator

parser = argparse.ArgumentParser(prog='XQR', add_help=False)
parser.add_argument('--help', action='store_true', help='print help')
parser.add_argument('--input', help='input filename')
parser.add_argument('--output', help='output filename')
parser.add_argument('--query', help='input query')
parser.add_argument('--qf', help='file with query')
parser.add_argument('-n', action='store_true', help='do not print xml header')
parser.add_argument('--root', help='name of root element')
# -------------------------ARGUMENTS---------------------
try:
    args = parser.parse_args()
except SystemExit:
    sys.stderr.write("ERROR WHEN PARSING ARGUMENTS.")
    sys.exit(1)

f_out = sys.stdout
f_input = sys.stdin
query_cmd = None
# PRINT HELP
if args.help:
    if len(sys.argv) > 2:
        sys.stderr.write("HELP should be the only entered argument.")
        sys.exit(1)
    print("IPP: Project 2 in Python 3.6 - xkanda00\n"
          "Script for processing query similar to SQL query.\n"
          "Input is XML file.\n"
          "Output is filtered XML file.\n"
          "\n"
          "Arguments:\n"
          "--help - shows this help\n"
          "--input=filename - name of XML input file\n"
          "--output=filename - name of XML output file to be created\n"
          "--query=\'dotaz\' - SQL-like query to process\n"
          "--qf=filename - name of file with SQL-like query\n"
          "-n - script will not generate XML header\n"
          "--root=element - name of root element which is whole output from filtering bounded\n")
    sys.exit(0)
# determine if QUERY and QUERY FILE was not entered at same time
if args.query is not None and args.qf is not None:
    sys.stderr.write(  # Ignore PEP8Bear  # Ignore PEP8Bear
        "ERROR: Query should be used in file --qf or --query=query_string.")
    sys.exit(1)

# open input file
if args.input is not None:
    try:
        f_input = open(args.input, 'r')
    except:
        sys.stderr.write("ERROR when opening input file")
        sys.exit(2)
# open output file
if args.output is not None:
    try:
        f_out = open(args.output, 'w')
    except:
        sys.stderr.write("ERROR when opening output file")
        sys.exit(3)
if args.query == '':
    sys.stderr.write("QUERY MISSING")
    sys.exit(80)
if args.qf == '' or args.query == '':
    sys.stderr.write("QUERY MISSING")
    sys.exit(80)

# open query file
if args.qf is not None:
    try:
        f_qf = open(args.qf, 'r')
    except:
        sys.stderr.write("ERROR with opening query file")
        sys.exit(80)
    query_cmd = f_qf.read()
    if query_cmd == "":
        sys.stderr.write("EMPTY QUERY FILE")
        sys.exit(2)

if args.query is not None:
    query_cmd = args.query
if args.query is None and args.qf is None:
    sys.stderr.write("NO QUERY.")
    sys.exit(80)
if not query_cmd.endswith('\n'):
    query_cmd += "\n"
# --------------------------REGULLAR EXPRESSION for parsing query-----------------
regex = r"SELECT\s+(?P<select>\S+)\s+(FROM\s*(?P<from>\S+?([^WHERE])|([^LIMIT])|(\s+?)|([^ORDER BY]))?)\s+?(?P<wh>WHERE\s+?(?P<where>.+?(?=(LIMIT|\n|ORDER)))?)?(ORDER BY\s+(?P<order>\S+)\s+(?P<order_flow>(\bASC\b|\bDESC\b)))?(\s?)+(?P<lim>LIMIT\s+(?P<limit>\S+)?)?"
reg = re.compile(regex)
try:
    matches = re.match(regex, query_cmd)
except:
    sys.stderr.write("BAD QUERY")
    sys.exit(80)
where_flag = True
query = {}
if matches is None:
    sys.stderr.write("BAD QUERY")
    sys.exit(80)

# save everything on right place in dictionary
query['select'] = matches.group('select')
query['from'] = matches.group('from')
if query['from'] is None:
    query['from'] = ""
query['where'] = matches.group('where')
if query['where'] is None:
    query['where'] = ""
    where_flag = False
    if matches.group('wh') is not None:
        sys.stderr.write("BAD QUERY")
        sys.exit(80)
query['order'] = matches.group('order')
# ASCENDING OR DESCENDING ORDER -> ORDER_FLOW
query['order_flow'] = matches.group('order_flow')
query['limit'] = matches.group('limit')

if query['limit'] is None:
    if matches.group('lim') is not None:
        sys.stderr.write("BAD QUERY")
        sys.exit(80)
if query['limit'] is not None:
    try:
        query['limit'] = int(query['limit'])
    except:
        sys.stderr.write("BAD QUERY")
        sys.exit(80)
    if query['limit'] < 0:
        sys.stderr.write("BAD QUERY")
        sys.exit(80)
if matches.group(6) is not None:
    where_flag = True

if query['order_flow'] == 'ASC':
    query['order_flow'] = False
elif query['order_flow'] == 'DESC':
    query['order_flow'] = True

# ------------------------------FROM--------------------------
query_temp = {}
    # split if attribute entered
if "." in query['from']:
    tmp = query['from'].split(".")
    if tmp[0] == '':
        tmp[0] = None
    query_temp['element'] = tmp[0]
    query_temp['attribute'] = tmp[1]
else:
    query_temp['element'] = query['from']
    query_temp['attribute'] = None
query['from'] = query_temp
# ------------------------------WHERE--------------------------
if where_flag:
    query_temp = {}
    NOT_flag = False
    # dictionary for determine operand type
    operand = {'equal': False, 'CONTAINS': False,
               'lower': False, 'greater': False}
    # spliting WHERE part of query and check for operator type

# OPERATORS SHARE THE SAME APPROACH WHEN DETERMINING TYPE AND VALUE WHICH WAS ENTERED
# ---------------------------- OPERATOR = --------------------------
    if "=" in query['where']:
        # split if needed (attribute entered)
        tmp = query['where'].split("=")
        tmp[0] = tmp[0].strip()
        tmp[1] = tmp[1].strip()
        if tmp[0] == '' or tmp[1] == '':
            sys.stderr.write("MISSING WHERE VALUE")
            sys.exit(80)
        query_temp['value'] = tmp[1]
        query_temp['subject'] = tmp[0]
        # save operand type
        operand['equal'] = True
# OPERATORS SHARE THE SAME APPROACH WHEN DETERMINING TYPE AND VALUE WHICH WAS ENTERED
# ---------------------------- OPERATOR CONSTAINS --------------------------
    elif "CONTAINS" in query['where']:
        tmp = query['where'].split("CONTAINS")
        tmp[0] = tmp[0].strip()
        tmp[1] = tmp[1].strip()
        if tmp[0] == '' or tmp[1] == '':
            sys.stderr.write("MISSING WHERE VALUE")
            sys.exit(80)
        try:
            tmp[1] = float(tmp[1])
        except:
            pass
        if not isinstance(tmp[1], str):
            sys.stderr.write("BAD QUERY. STRING literal is expected.\n")
            sys.exit(80)
        query_temp['value'] = tmp[1]
        query_temp['subject'] = tmp[0]
        operand['CONTAINS'] = True
# OPERATORS SHARE THE SAME APPROACH WHEN DETERMINING TYPE AND VALUE WHICH WAS ENTERED
# ---------------------------- OPERATOR < --------------------------
    elif "<" in query['where']:
        tmp = query['where'].split("<")
        tmp[0] = tmp[0].strip()
        tmp[1] = tmp[1].strip()
        if tmp[0] == '' or tmp[1] == '':
            sys.stderr.write("MISSING WHERE VALUE")
            sys.exit(80)
        query_temp['value'] = tmp[1]
        query_temp['subject'] = tmp[0]
        operand['lower'] = True
# OPERATORS SHARE THE SAME APPROACH WHEN DETERMINING TYPE AND VALUE WHICH WAS ENTERED
# ---------------------------- OPERATOR > --------------------------
    elif ">" in query['where']:
        tmp = query['where'].split(">")
        tmp[0] = tmp[0].strip()
        tmp[1] = tmp[1].strip()
        if tmp[0] == '' or tmp[1] == '':
            sys.stderr.write("MISSING WHERE VALUE")
            sys.exit(80)
        query_temp['value'] = tmp[1]
        query_temp['subject'] = tmp[0]
        operand['greater'] = True
    else:
        sys.stderr.write("BAD QUERY")
        sys.exit(80)
# ---------------------------- OPERATOR NOT --------------------------
# function for determine multipling NOT operator
    while "NOT " in query_temp['subject']:
        query_temp['subject'] = query_temp['subject'].replace("NOT ", "", 1)
        NOT_flag = not NOT_flag

    query_temp_subj = {}
    # split if attribute entered
    if "." in query_temp['subject']:
        tmp = query_temp['subject'].split(".")
        query_temp_subj['element'] = tmp[0]
        query_temp_subj['attribute'] = tmp[1]
    else:
        query_temp_subj['element'] = query_temp['subject']
        query_temp_subj['attribute'] = None
    
    query_temp['subject'] = query_temp_subj
    query['where'] = query_temp

# ------------------------FROM------------------------------
root_element = {}  # array for elements which will be filtered from FROM part
xml_parse = mdom.parse(f_input)
if query['from']['element'] == "ROOT":
    root_element = [xml_parse.documentElement]
elif (query['from']['element'] == "WHERE" or query['from']['element'] == "") and query['from']['attribute'] is None:
    root_element = ''
# ----------------------------FROM .attribute --------------------------
elif query['from']['element'] is None and query['from']['attribute'] is not None:
    try:
        tmp_root_element = xml_parse.getElementsByTagName("*")
    except:
        sys.stderr.write("NON-EXISTING element")
        sys.exit(80)
    for root in tmp_root_element:
        if root.hasAttribute(query['from']['attribute']):
            root_element = [root]
            break
# ---------------------------- FROM element--------------------------
elif query['from']['element'] is not None and query['from']['attribute'] is None:
    try:
        root_element=[xml_parse.getElementsByTagName(query['from']['element'])[0]]
    except:
        sys.stderr.write("NON-EXISTING element")
        sys.exit(80)
# ---------------------------- FROM element.attribute --------------------------
elif query['from']['element'] is not None and query['from']['attribute'] is not None:
    try:
        tmp_root_element = xml_parse.getElementsByTagName(query['from']['element'])
    except:
        sys.stderr.write("NON-EXISTING element")
        sys.exit(80)
    for root in tmp_root_element:
        if root.hasAttribute(query['from']['attribute']):
            root_element = [root]
            break
else:
    sys.stderr.write("CHYBA pri spracovavani vyrazu.")
    sys.exit(80)
root_flag = False # flag for selection FROM ROOT
# ------------------------SELECT----------------------------
if "." in query['select']:
    sys.stderr.write("BAD QUERY.")
    sys.exit(80)
select_elem = []
if query['select'] == "ROOT":
    select_elem = [xml_parse.documentElement]
else:
    for element in root_element:
        if element.tagName == query['select']:
            if query['from']['element'] == "ROOT":
                select_elem += [element]
                root_flag = True
        else:
            select_elem += [element.getElementsByTagName(query['select'])]

# ------------------------WHERE----------------------------

# ----------------------------function for evaluating WHERE expression--------------------------
def returnValue(operand, query_val, value):
    try:
        # get rid of spaces
        value = value.strip()
    except:
        pass
    tmp_flag = False
    try:
        # trying to cast to float
        query_val = float(query_val)
        tmp_flag = True
    except:
        # check if value is quoted
        if query_val.startswith("\"") and query_val.endswith("\""):
            tmp_strip = query_val
            tmp_strip = tmp_strip.strip('\"')
            query_val = tmp_strip
    if tmp_flag:
        try:
            value = float(value)
        except:
            return False
    opt = None
    # determining which operand is used
    for name, statement in operand.items():
        if statement is True:
            opt = name

    # evaluation of statement in WHERE part
    if opt == "CONTAINS":
        if not isinstance(query_val, str):
            sys.stderr.write("BAD QUERY")
            sys.exit(80)
        if query_val in value:
            return True
        else:
            return False
    if opt == "equal":
        return query_val == value
    if opt == "lower":
        return query_val > value
    if opt == "greater":
        return query_val < value

whered_elem = []
# ----------------------------IF QUERY contains WHERE part--------------------------
if where_flag:
# ---------------------------- missing element and attribute--------------------------
    if query['where']['subject']['element'] == "" and query['where']['subject']['attribute'] is None:
        sys.stderr.write("BAD QUERY")
        sys.exit(80)
# ----------------------------WHERE .attribute--------------------------
    elif query['where']['subject']['element'] == "" and query['where']['subject']['attribute'] is not None:
        tmp_elem = []
        if not NOT_flag:
            for selected in select_elem:
                for sel in selected:
                    # if selected element has attribute
                    if sel.hasAttribute(query['where']['subject']['attribute']):
                        tmp_value = sel.getAttribute(query['where']['subject']['attribute'])
                        op = returnValue(operand, query['where']['value'], tmp_value)
                        if op:
                            whered_elem += [sel]
                    else:
                        # else find element with attribute
                        try:
                            tmp_elem = sel.getElementsByTagName("*")
                        except:
                            sys.stderr.write("NON-EXISTING element")
                            sys.exit(80)
                        for elem in tmp_elem:
                            if elem.hasAttribute(query['where']['subject']['attribute']):
                                try:
                                    tmp_value = elem.getAttribute(query['where']['subject']['attribute'])
                                except:
                                    tmp_value = None
                                    pass
                                op = returnValue(operand, query['where']['value'], tmp_value)
                                if op:
                                    whered_elem += [elem.parentNode]
# ----------------------------WHERE NOT .attribute --------------------------
        else:
            for selected in select_elem:
                for sel in selected:
                    # if selected element has attribute
                    if sel.hasAttribute(query['where']['subject']['attribute']):
                        tmp_value = sel.getAttribute(query['where']['subject']['attribute'])  # Ignore PEP8Bear
                        op = returnValue(operand, query['where']['value'], tmp_value)
                        if not op:
                            whered_elem += [sel]
                    else:
                        # try to find element with attribute
                        try:
                            tmp_elem = [sel.getElementsByTagName("*")]
                        except:
                            sys.stderr.write("NON-EXISTING element")
                            sys.exit(80)
                        for elem in tmp_elem:
                            if elem.hasAttribute(query['where']['subject']['attribute']):
                                tmp_value = elem.firstChild.nodeValue
                                op = returnValue(operand, query['where']['value'], tmp_value)
                                if not op:
                                    whered_elem += [elem.parentNode]

# ---------------------------- WHERE element--------------------------
    elif query['where']['subject']['element'] is not None and query['where']['subject']['attribute'] is None:
        tmp_elem = []
        if not NOT_flag:
            for selected in select_elem:
                for sel in selected:
                    # if selected element is element which we are looking up
                    if sel.tagName == query['where']['subject']['element']:
                        tmp_value = sel.firstChild.nodeValue
                        op = returnValue(operand, query['where']['value'], tmp_value)
                        if op:
                            whered_elem += [sel]
                    else:
                        # find element with given name
                        try:
                            tmp_elem = sel.getElementsByTagName(query['where']['subject']['element'])
                        except:
                            sys.stderr.write("NON-EXISTING element")
                            sys.exit(80)
                        for elem in tmp_elem:
                            tmp_value = elem.firstChild.nodeValue
                            op = returnValue(operand, query['where']['value'], tmp_value)
                            if op:
                                # save element
                                whered_elem += [elem.parentNode]
# ----------------------------WHERE NOT element --------------------------
        else:
            for selected in select_elem:
                for sel in selected:
                    # if selected element is element which we are looking up
                    if sel.tagName == query['where']['subject']['element']:
                        tmp_value = sel.firstChild.nodeValue
                        op = returnValue(operand, query['where']['value'], tmp_value)
                        if not op:
                            whered_elem += [sel]
                    else:
                        # find element with given name
                        try:
                            tmp_elem = sel.getElementsByTagName(query['where']['subject']['element'])
                        except:
                            sys.stderr.write("NON-EXISTING element")
                            sys.exit(80)
                        for elem in tmp_elem:
                            tmp_value = elem.firstChild.nodeValue
                            op = returnValue(operand, query['where']['value'], tmp_value)
                            if not op:
                                whered_elem += [elem.parentNode]
# ---------------------------- WHERE element.attribute--------------------------
    elif query['where']['subject']['element'] is not None and query['where']['subject']['attribute']is not None:
        tmp_elem = []
        if not NOT_flag:
            for selected in select_elem:
                for sel in selected:
                    # if selected element is element with attribute which we
                    # are looking up
                    if sel.tagName == query['where']['subject']['element']:
                        if sel.hasAttribute(query['where']['subject']['attribute']):
                            tmp_value = sel.getAttribute(query['where']['subject']['attribute'])
                            op = returnValue(operand, query['where']['value'], tmp_value)
                            if op:
                                whered_elem += [sel]
                    else:
                        # find element with given name and attribute
                        try:
                            tmp_elem = [sel.getElementsByTagName(query['where']['subject']['element'])]
                        except:
                            sys.stderr.write("NON-EXISTING element")
                            sys.exit(80)
                        for elem in tmp_elem:
                            if elem.hasAttribute(query['where']['subject']['attribute']):
                                tmp_value = elem.firstChild.nodeValue
                                op = returnValue(operand, query['where']['value'], tmp_value)
                                if op:
                                    whered_elem += [elem.parentNode]
# ---------------------------- WHERE NOT element.attribute--------------------------
        else:
            for selected in select_elem:
                for sel in selected:
                    # if selected element is element with attribute which we are looking up
                    if sel.tagName == query['where']['subject']['element']:
                        if sel.hasAttribute(query['where']['subject']['attribute']):
                            tmp_value = sel.getAttribute(query['where']['subject']['attribute'])
                            op = returnValue(operand, query['where']['value'], tmp_value)
                            if not op:
                                whered_elem += [sel]
                    else:
                        # find element with given name and attribute
                        try:
                            tmp_elem = [sel.getElementsByTagName(query['where']['subject']['element'])]
                        except:
                            sys.stderr.write("NON-EXISTING element")
                            sys.exit(80)
                        for elem in tmp_elem:
                            if elem.hasAttribute(query['where']['subject']['attribute']):
                                tmp_value = elem.firstChild.nodeValue
                                op = returnValue(operand, query['where']['value'], tmp_value)
                                if not op:
                                    whered_elem += [elem.parentNode]
# ---------------------------- OUTPUT PART--------------------------
sys.stdout = f_out
query_temp['order'] = {}
query_temp['order']['element'] = {}
# ----------------------------MISSING WHERE PART - ordering, limiting and writing from SELECT part-------------------------
if not where_flag:
    if query['order'] is not None:
        counter = 0
        order = []
        sort_ord = []
        # split to element and sttribute if needed
        if "." in query['order']:
            query['order'] = query['order'].split(".")
            query_temp['order']['element'] = query['order'][0]
            query_temp['order']['attribute'] = query['order'][1]
            query['order'] = query_temp['order']
        else:
            query_temp['order']['element'] = query['order']
            query_temp['order']['attribute'] = None
            query['order'] = query_temp['order']

        for tmp_sel in select_elem:
            whered_elem = tmp_sel
            tmp_x = ""
            for elem in whered_elem:
# ----------------------------ORDER element--------------------------
                if query['order']['element'] is not None and query['order']['element'] != '':
                    if query['order']['attribute'] is None:
                        try:
                            if elem.tagName == query['order']['element']:
                                x = elem.firstChild.nodeValue
                            else:
                                tmp_x = elem.getElementsByTagName(query['order']['element'])[0]
                                x = tmp_x.firstChild.nodeValue  # ######################
                        except:
                            sys.stderr.write("ORDER ELEMENT MISSING\n")
                            sys.exit(4)
# ----------------------------ORDER .attribute--------------------------
                elif (query['order']['element'] == '' or query['order']['element'] is None) and query['order']['attribute'] is not None:
                    order_attr = False
                    try:
                        temp_x = xml_parse.getElementsByTagName("*")
                    except:
                        sys.stderr.write("NON-EXISTING element")
                        sys.exit(80)
                    for temp in temp_x:
                        if temp.hasAttribute(query['order']['attribute']):
                            x = temp.getAttribute(query['order']['attribute'])
                            order_attr = True
                            break
                    if not order_attr:
                        sys.stderr.write("ORDER ATTRIBUTE MISSING\n")
                        sys.exit(4)
# ---------------------------- ORDER element.attribute--------------------------
                elif (query['order']['element'] != '' or query['order']['element'] is not None) and query['order']['attribute'] is not None:
                    order_attr = False
                    try:
                        if elem.tagName == query['order']['element']:
                            if elem.hasAttribute(query['order']['attribute']):
                                x = elem.getAttribute(query['order']['attribute'])
                                order_attr = True
                        else:
                            temp_x = elem.getElementsByTagName(query['order']['element'])[0]
                            if temp_x.hasAttribute(query['order']['attribute']):
                                x = elem.getAttribute(query['order']['attribute'])
                                order_attr = True
                    except:
                            sys.stderr.write("ORDER ATTRIBUTE MISSING\n")
                            sys.exit(4)
                    if not order_attr:
                        sys.stderr.write("ORDER ATTRIBUTE MISSING\n")
                        sys.exit(4)
                else:
                    sys.stderr.write("BAD QUERY.\n")
                    sys.exit(80)

                y = elem
                order += [(x, y)]
            # sort by value in couple (1.value, 2.element from xml file)
            sort_ord = sorted(order, key=operator.itemgetter(0), reverse=query['order_flow'])
            # print elements sorted
            listed = [x[1] for x in sort_ord]
            # set attribute of ordered elements
            order_counter = 1
            for elem in listed:
                elem.setAttribute("order", str(order_counter))
                order_counter = order_counter + 1
            # print xml header if -n is not entered
            if not args.n:
                sys.stdout.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            # print xml root element if --root arg entered
            if args.root is not None:
                sys.stdout.write("<" + args.root + ">")
            for elem in listed:
                if query['limit'] is not None:
                    if counter != query['limit']:
                        counter = counter + 1
                    else:
                        break
                sys.stdout.write(elem.toxml())
                sys.stdout.write("")
# ---------------------------- without ORDER--------------------------
    else:
        # print xml header if not -n entered
        if not args.n:
            sys.stdout.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        # print root element if --root arg entered
        if args.root is not None:
            sys.stdout.write("<" + args.root + ">")
        for tmp_sel in select_elem:
            if root_flag:
                whered_elem = [tmp_sel]
            else:
                whered_elem = tmp_sel
            counter = 0
            # limit number of elements on output
            for elem in whered_elem:
                if query['limit'] is not None:
                    if counter != query['limit']:
                        counter = counter + 1
                    else:
                        break
                sys.stdout.write(elem.toxml())
                sys.stdout.write("")
# ----------------------------ordering, limiting and writing WHERE part--------------------------
# -----------------------------SAME APPROACH AS ORDERING AND LIMITING SELECT PART----------------
else:
    if query['order'] is not None:
        counter = 0
        order = []
        sort_ord = []
        if "." in query['order']:
            query['order'] = query['order'].split(".")
            query_temp['order']['element'] = query['order'][0]
            query_temp['order']['attribute'] = query['order'][1]
            query['order'] = query_temp['order']
        else:
            query_temp['order']['element'] = query['order']
            query_temp['order']['attribute'] = None
            query['order'] = query_temp['order']

        for elem in whered_elem:
# ---------------------------- ORDER element --------------------------
            if query['order']['element'] is not None and query['order']['element'] != '' and query['order']['attribute'] is None:
                try:
                    if elem.tagName == query['order']['element']:
                        x = elem.firstChild.nodeValue
                    else:
                        tmp_x = elem.getElementsByTagName(query['order']['element'])[0]
                        x = tmp_x.firstChild.nodeValue  # ######################
                except:
                    sys.stderr.write("ORDER ELEMENT MISSING\n")
                    sys.exit(4)
# ---------------------------- ORDER .attribute--------------------------
            elif (query['order']['element'] == '' or query['order']['element'] is None) and query['order']['attribute'] is not None:
                try:
                    temp_x = xml_parse.getElementsByTagName("*")
                    for temp in temp_x:
                        if temp.hasAttribute(query['order']['attribute']):
                            x = temp.getAttribute(query['order']['attribute'])
                            break
                except:
                    sys.stderr.write("ORDER ATTRIBUTE MISSING")
                    sys.exit(4)
# ---------------------------- ORDER element.attribute--------------------------
            elif (query['order']['element'] != '' or query['order']['element'] is not None) and query['order']['attribute'] is not None:
                try:
                    if elem.tagName == query['order']['element']:
                        if elem.hasAttribute(query['order']['attribute']):
                            x = elem.getAttribute(query['order']['attribute'])
                    else:
                        temp_x = elem.getElementsByTagName(query['order']['element'])[0]
                        if temp_x.hasAttribute(query['order']['attribute']):
                            x = elem.getAttribute(query['order']['attribute'])
                except:
                    sys.stderr.write("ORDER ELEMENT or ATTRIBUTE MISSING\n")
                    sys.exit(4)
# ----------------------------missing ORDER element value --------------------------
            else:
                sys.stderr.write("BAD QUERY.")
                sys.exit(80)

            y = elem
            order += [(x, y)]
        # sort by value in couple (1.value, 2.element from xml file)
        sort_ord = sorted(order, key=operator.itemgetter(0), reverse=query['order_flow'])
        # print elements sorted
        listed = [x[1] for x in sort_ord]
        # set attribute of ordered elements
        order_counter = 1
        for elem in listed:
            elem.setAttribute("order", str(order_counter))
            order_counter = order_counter + 1
        whered_elem = listed
    # print xml header if not -n entered
    if not args.n:
        sys.stdout.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
    # print xml root element if --root arg netered
    if args.root is not None:
        sys.stdout.write("<" + args.root + ">")
        # limit number of elements
    for elem in whered_elem:
        if query['limit'] is not None:
            counter = 0
            if counter != query['limit']:
                counter = counter + 1
            else:
                break
        sys.stdout.write(elem.toxml())
        sys.stdout.write("")
# print xml root element if --root arg netered
if args.root is not None:
    sys.stdout.write("\n</"+args.root+">")

sys.exit(0)
