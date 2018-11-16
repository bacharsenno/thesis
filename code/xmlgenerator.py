import simplejson
from pprint import pprint
from collections import defaultdict, OrderedDict
from operator import itemgetter
import sys
import getopt

Elementary = {"integer", "float", "string", ""}
Basic = {"integer", "float", "string"}
value_object = defaultdict(list)
cleaned_value_object = OrderedDict()
parent_list = dict()
depth_array = dict()
parent = "root"
maxDepth = 0

def process_options(argv):
	filename = None
	try:
		opts, args = getopt.getopt(argv[1:], "f:s", ['filename='])
	except getopt.GetoptError, err:
	# print help information and exit:
		print str(err)
		#usage()
		sys.exit(2)
	for o, a in opts:
		if o in ("-f", "--filename"):
			filename = a
	return filename
	
def generate_value(key, value):
	if key == "formattedAddress":
		print ''
	if value["type"] == "array":
		if value["properties"] and value["properties"][0]["type"] in Basic:
			return '<js:value name="' + key + '" type="' + value["properties"][0]["type"] + '" qualifier="list" />'
		return '<js:value name="' + key + '" type="' + key + '" qualifier="list" />'
	elif value["type"] == "object":
		return '<js:value name="' + key + '" type="' + key + '" />'
	else:
		return '<js:value name="' + key + '" type="' + value["type"] + '" />'
		
def isElementary(o):
	if o["type"] in Elementary:
		return True
	elif o["type"] == "object":
		return False
	elif o["type"] == "array":
		i = o["properties"]
		if not i:
			return True
		return isElementary(i[0])
		
def isBaseObject(o):
	for key, value in o.iteritems():
		if value == None:
			value = dict()
			value["type"] = "string"
		if isElementary(value) or key in Elementary:
			continue
		else:
			return False, key
	return True, True

def getObject(o):
	if o["type"] == "array":
		return o["properties"][0]["properties"]
	else:
		return o["properties"]

def parseObject(o, parent, depth):
	depth = depth + 1
	global maxDepth
	if depth > maxDepth:
		maxDepth = depth
	if parent in parent_list:
		parent_list[parent] = parent_list[parent] + 1
	else:
		parent_list[parent] = 1
	parent = parent + ":::" + str(parent_list[parent])
	for key, value in o.iteritems():
		if key == "groups":
			print ''
		if key == "id":
			continue
		if value == None:
			value = dict()
			value["type"] = "string"
			o[key] = value
		if isElementary(value) or key in Elementary:
			value_object[parent].append(generate_value(key, value))
			continue
		val, k = isBaseObject(getObject(value))
		if val == True:
			parseObject(getObject(value), key, depth)
			Elementary.add(key)
			value_object[parent].append(generate_value(key, value))
		else:
			temp = getObject(getObject(value)[k])
			parseObject(temp, k, depth + 1)
			Elementary.add(k)
			parseObject(getObject(value), key, depth)
			value_object[parent].append(generate_value(key, value))
	depth_array[parent] = depth


def cleanupValues():
	for key, value in value_object.iteritems():
		if ":::" in key:
			k = key.split(":::")[0]
			if k in cleaned_value_object.keys():
				for val in value:
					if val not in cleaned_value_object[k]:
						cleaned_value_object[k].append(val)
			else:
				cleaned_value_object[k] = value

def reorderValues():
	global cleaned_value_object
	for key, value in cleaned_value_object.iteritems():
		for key2, value2 in depth_array.iteritems():
			k = key2.split(":::")[0]
			if key == k:
				if type(cleaned_value_object[key][-1]) == str:
					cleaned_value_object[key].append(value2)
				elif cleaned_value_object[key][1] < value2:
					cleaned_value_object[key][1] = value2
	cleaned_value_object = sorted(cleaned_value_object.items(), key=lambda x: x[1][-1], reverse=True)

def printValues(valueArray):
	for value in valueArray:
		print "\t" + value

def generateXML():
	for key, value in cleaned_value_object:
		if key == None:
			print ''
		if key == "root":
			continue
		else:
			print '<js:object id="' + key + '">'
			printValues(value[:-1])
			print '</js:object>'
	print '<js:object id="root">'
	printValues(value_object.get("root:::1")[:-1])
	print '</js:object>'

def main():
	filename = process_options(sys.argv)
	with open(filename, 'r') as f:
		data = simplejson.load(f)
	data = data["properties"]
	parseObject(data, "root", 0)
	cleanupValues()
	reorderValues()
	generateXML()
			
if __name__ == '__main__':
	main()